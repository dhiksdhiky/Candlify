"""
worker/sync_idx_daily.py — All-in-One IDX Stock Summary & Daily Price Engine
=============================================================================
Arsitektur Dua Lapis (Dual-Layer Sync):
- Layer 1 (Utama - BEI Official API):
  Mengambil JSON ringkasan perdagangan harian BEI via:
  https://www.idx.co.id/primary/TradingSummary/GetStockSummary?length=9999&start=0
  Bypass proteksi Cloudflare via TLS impersonation (curl_cffi safari17_0).
  Memperbarui DUA tabel database sekaligus dalam 1 kali proses kilat:
  1. `daftar_saham`: Kode, Nama, Papan, Free Float (Tradeable Shares), Notasi Khusus (FCA, XD, dll).
  2. `harga_saham`: OHLCV resmi, Value (Turnover IDR), Frequency, Foreign Buy/Sell/Net, Bid/Offer.
  3. Memperbarui `worker/daftar_saham.csv` lokal agar selalu sinkron.

- Layer 2 (Fallback Otomatis):
  Jika Layer 1 gagal (koneksi terputus / Cloudflare memblokir):
  Otomatis alihkan ke:
  1. `sync_daftar_saham.py` (DirectApi / Nuxt SSR) untuk master emiten.
  2. `pipeline.py` (yfinance) untuk harga OHLCV.
"""

from __future__ import annotations

import os
import sys
import re
import csv
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from curl_cffi import requests as cf_requests

# Pastikan path import module worker terbaca
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import engine, get_dialect, TEST_MODE, log_to_db

logger = logging.getLogger("SyncIDXDaily")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

IDX_SUMMARY_URL = "https://www.idx.co.id/primary/TradingSummary/GetStockSummary"

BOARD_MAP = {
    "1": "Utama",
    "2": "Pengembangan",
    "3": "Akselerasi",
    "4": "Pemantauan Khusus",
    "5": "Ekonomi Baru",
}

BULAN_INDO = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}


def decode_remarks(remarks: str) -> Tuple[str, str]:
    """
    Mendekode string Remarks resmi dari BEI (contoh: '--U-4105000000J211ME---------X').
    Returns:
        (papan_pencatatan, notasi_khusus)
    """
    if not remarks or len(remarks) < 5:
        return "Pengembangan", ""

    # Karakter ke-5 (index 4) adalah kode Papan Pencatatan resmi
    board_char = remarks[4]
    listing_board = BOARD_MAP.get(board_char, "Pengembangan")

    notations: List[str] = []

    # 1. Corporate Action prefix (2 karakter pertama jika bukan '--')
    corp = remarks[:2].replace("-", "").strip()
    if corp:
        notations.append(corp)

    # 2. Notasi khusus BEI di bagian akhir (index 18 sampai 30)
    # Contoh: 'ME---------X' -> 'M', 'E', 'X'
    if len(remarks) >= 30:
        tail = remarks[18:].replace("-", "").strip()
        for ch in tail:
            if ch and ch not in notations:
                notations.append(ch)

    notasi_str = ", ".join(notations) if notations else ""
    return listing_board, notasi_str


def format_shares_dot(shares: int) -> str:
    """Format angka saham dengan pemisah titik: 1924688333 -> '1.924.688.333'."""
    return f"{shares:,}".replace(",", ".")


def fetch_idx_trading_summary(
    date_str: str = "",
    impersonate: str = "safari17_0",
    timeout: int = 25
) -> Dict[str, Any]:
    """
    Mengambil data Trading Summary dari portal resmi BEI.
    Bisa menerima date_str format 'YYYYMMDD' atau 'YYYY-MM-DD'.
    """
    params: Dict[str, Any] = {
        "length": 9999,
        "start": 0,
    }
    if date_str:
        clean_d = date_str.replace("-", "").strip()
        params["date"] = clean_d

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    }

    logger.info("📡 Mengakses IDX GetStockSummary (impersonate=%s, date=%s)...", impersonate, date_str or "latest")
    
    # Coba impersonate utama, jika gagal coba fallback impersonate
    try:
        response = cf_requests.get(
            IDX_SUMMARY_URL,
            params=params,
            headers=headers,
            impersonate=impersonate,
            timeout=timeout
        )
    except Exception as exc:
        if impersonate != "safari15_5":
            logger.warning("⚠️ Impersonate %s gagal (%s), mencoba safari15_5...", impersonate, exc)
            response = cf_requests.get(
                IDX_SUMMARY_URL,
                params=params,
                headers=headers,
                impersonate="safari15_5",
                timeout=timeout
            )
        else:
            raise

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code} saat mengakses IDX Trading Summary.")

    payload = response.json()
    if not isinstance(payload, dict) or "data" not in payload:
        raise ValueError("Payload IDX GetStockSummary tidak valid atau kosong.")

    return payload


def parse_trading_summary_data(
    payload: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[date]]:
    """
    Mengurai payload JSON menjadi:
    1. rows_daftar_saham (untuk tabel daftar_saham & daftar_saham.csv)
    2. rows_harga_saham (untuk tabel harga_saham)
    3. trading_date (tanggal resmi perdagangan bursa)
    """
    raw_data = payload.get("data", [])
    if not raw_data:
        raise ValueError("Data Trading Summary dari BEI kosong.")

    rows_daftar: List[Dict[str, Any]] = []
    rows_harga: List[Dict[str, Any]] = []
    trading_date: Optional[date] = None

    for i, item in enumerate(raw_data, 1):
        raw_code = str(item.get("StockCode", "")).strip().upper()
        if not re.match(r"^[A-Z0-9]{4,6}$", raw_code):
            continue

        raw_name = str(item.get("StockName", "")).strip()
        remarks = str(item.get("Remarks", "")).strip()
        papan, notasi = decode_remarks(remarks)

        # Parse shares
        try:
            listed_shares = int(float(item.get("ListedShares", 0) or 0))
        except (ValueError, TypeError):
            listed_shares = 0

        try:
            tradeable_shares = int(float(item.get("TradebleShares", 0) or 0))
        except (ValueError, TypeError):
            tradeable_shares = listed_shares

        # Parse Date
        date_raw = str(item.get("Date", "")).strip().split("T")[0]
        row_date: Optional[date] = None
        if date_raw:
            try:
                row_date = datetime.strptime(date_raw, "%Y-%m-%d").date()
                if trading_date is None:
                    trading_date = row_date
            except Exception:
                row_date = None

        if row_date is None:
            continue

        # Parse OHLCV
        try:
            close_price = float(item.get("Close", 0) or 0)
            open_price = float(item.get("OpenPrice", 0) or 0)
            high_price = float(item.get("High", 0) or 0)
            low_price = float(item.get("Low", 0) or 0)
            prev_price = float(item.get("Previous", 0) or 0)
            
            # Jika saham tidak ditransaksikan hari ini (Open=0 / High=0), gunakan Close/Previous
            if open_price == 0 and close_price > 0:
                open_price = close_price
            if high_price == 0 and close_price > 0:
                high_price = close_price
            if low_price == 0 and close_price > 0:
                low_price = close_price

            vol = int(float(item.get("Volume", 0) or 0))
            val = float(item.get("Value", 0) or 0)
            freq = int(float(item.get("Frequency", 0) or 0))
            f_buy = int(float(item.get("ForeignBuy", 0) or 0))
            f_sell = int(float(item.get("ForeignSell", 0) or 0))
            f_net = f_buy - f_sell

            offer = float(item.get("Offer", 0) or 0)
            offer_vol = int(float(item.get("OfferVolume", 0) or 0))
            bid = float(item.get("Bid", 0) or 0)
            bid_vol = int(float(item.get("BidVolume", 0) or 0))

            non_reg_vol = int(float(item.get("NonRegularVolume", 0) or 0))
            non_reg_val = float(item.get("NonRegularValue", 0) or 0)
        except Exception as parse_err:
            logger.warning("Gagal parsing angka untuk %s: %s", raw_code, parse_err)
            continue

        rows_daftar.append({
            "kode": raw_code,
            "no": i,
            "nama_perusahaan": raw_name,
            "saham": listed_shares,
            "tradeable_shares": tradeable_shares,
            "papan_pencatatan": papan,
            "notasi_khusus": notasi,
        })

        rows_harga.append({
            "ticker": raw_code,
            "tanggal": row_date,
            "open": open_price,
            "high": high_price,
            "low": low_price,
            "close": close_price,
            "volume": vol,
            "value": val,
            "frequency": freq,
            "foreign_buy": f_buy,
            "foreign_sell": f_sell,
            "foreign_net": f_net,
            "offer": offer,
            "offer_volume": offer_vol,
            "bid": bid,
            "bid_volume": bid_vol,
            "non_regular_volume": non_reg_vol,
            "non_regular_value": non_reg_val,
        })

    return rows_daftar, rows_harga, trading_date


def update_local_csv(daftar_rows: List[Dict[str, Any]], csv_path: str) -> None:
    """Menulis ulang worker/daftar_saham.csv lokal dengan data terbaru."""
    sorted_rows = sorted(daftar_rows, key=lambda x: x["kode"])
    lines = ["No;Kode;Nama Perusahaan;Tanggal Pencatatan;Saham;Papan Pencatatan\n"]
    for i, r in enumerate(sorted_rows, 1):
        saham_str = format_shares_dot(r["saham"])
        line = f"{i};{r['kode']};{r['nama_perusahaan']};;{saham_str};{r['papan_pencatatan']}\n"
        lines.append(line)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("📄 File %s berhasil disinkronkan (%d emiten).", csv_path, len(sorted_rows))


def sync_daftar_saham_bulk(daftar_rows: List[Dict[str, Any]]) -> int:
    """Melakukan bulk upsert ke tabel daftar_saham di DB."""
    if not daftar_rows:
        return 0

    dialect = get_dialect()
    if dialect == "sqlite":
        upsert_stmt = text("""
            INSERT INTO daftar_saham (
                kode, no, nama_perusahaan, saham, tradeable_shares, papan_pencatatan, notasi_khusus, tanggal_update
            ) VALUES (
                :kode, :no, :nama_perusahaan, :saham, :tradeable_shares, :papan_pencatatan, :notasi_khusus, CURRENT_DATE
            )
            ON CONFLICT (kode) DO UPDATE SET
                no = EXCLUDED.no,
                nama_perusahaan = EXCLUDED.nama_perusahaan,
                saham = EXCLUDED.saham,
                tradeable_shares = EXCLUDED.tradeable_shares,
                papan_pencatatan = EXCLUDED.papan_pencatatan,
                notasi_khusus = EXCLUDED.notasi_khusus,
                tanggal_update = CURRENT_DATE
        """)
    else:
        upsert_stmt = text("""
            INSERT INTO daftar_saham (
                kode, no, nama_perusahaan, saham, tradeable_shares, papan_pencatatan, notasi_khusus, tanggal_update
            ) VALUES (
                :kode, :no, :nama_perusahaan, :saham, :tradeable_shares, :papan_pencatatan, :notasi_khusus, CURRENT_DATE
            )
            ON CONFLICT (kode) DO UPDATE SET
                no = EXCLUDED.no,
                nama_perusahaan = EXCLUDED.nama_perusahaan,
                saham = EXCLUDED.saham,
                tradeable_shares = EXCLUDED.tradeable_shares,
                papan_pencatatan = EXCLUDED.papan_pencatatan,
                notasi_khusus = EXCLUDED.notasi_khusus,
                tanggal_update = CURRENT_DATE
        """)

    with engine.begin() as conn:
        conn.execute(upsert_stmt, daftar_rows)

    logger.info("✅ Master emiten tersinkronisasi: %d emiten ke tabel daftar_saham.", len(daftar_rows))
    return len(daftar_rows)


def sync_harga_saham_bulk(harga_rows: List[Dict[str, Any]]) -> int:
    """Melakukan bulk upsert ke tabel harga_saham di DB."""
    if not harga_rows:
        return 0

    dialect = get_dialect()
    upsert_stmt = text("""
        INSERT INTO harga_saham (
            ticker, tanggal, open, high, low, close, volume,
            value, frequency, foreign_buy, foreign_sell, foreign_net,
            offer, offer_volume, bid, bid_volume,
            non_regular_volume, non_regular_value
        ) VALUES (
            :ticker, :tanggal, :open, :high, :low, :close, :volume,
            :value, :frequency, :foreign_buy, :foreign_sell, :foreign_net,
            :offer, :offer_volume, :bid, :bid_volume,
            :non_regular_volume, :non_regular_value
        )
        ON CONFLICT (ticker, tanggal) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            value = EXCLUDED.value,
            frequency = EXCLUDED.frequency,
            foreign_buy = EXCLUDED.foreign_buy,
            foreign_sell = EXCLUDED.foreign_sell,
            foreign_net = EXCLUDED.foreign_net,
            offer = EXCLUDED.offer,
            offer_volume = EXCLUDED.offer_volume,
            bid = EXCLUDED.bid,
            bid_volume = EXCLUDED.bid_volume,
            non_regular_volume = EXCLUDED.non_regular_volume,
            non_regular_value = EXCLUDED.non_regular_value
    """)

    with engine.begin() as conn:
        conn.execute(upsert_stmt, harga_rows)

    logger.info("✅ Harga & flow harian tersinkronisasi: %d baris ke tabel harga_saham.", len(harga_rows))
    return len(harga_rows)


def execute_layer_2_fallback() -> Dict[str, Any]:
    """
    Eksekusi cadangan jika Layer 1 (IDX GetStockSummary) gagal:
    1. Sinkronisasi master emiten via sync_daftar_saham.py
    2. Sinkronisasi OHLCV via pipeline.py (Yahoo Finance)
    """
    logger.warning("🛡️ Mengaktifkan LAYER 2 FALLBACK (Daftar Saham Direct/Nuxt + Yahoo Finance Pipeline)...")
    fallback_res: Dict[str, Any] = {
        "source": "layer_2_fallback",
        "stocks_synced": 0,
        "prices_synced": 0,
        "success": False
    }

    try:
        from sync_daftar_saham import run_sync
        ds_res = run_sync()
        fallback_res["stocks_synced"] = ds_res.get("total_emiten", 0)
    except Exception as err:
        logger.error("❌ Fallback sync_daftar_saham gagal: %s", err)

    try:
        from pipeline import run_pipeline
        pipe_success = run_pipeline()
        fallback_res["prices_synced"] = 1 if pipe_success else 0
        fallback_res["success"] = pipe_success
    except Exception as err:
        logger.error("❌ Fallback pipeline Yahoo Finance gagal: %s", err)
        fallback_res["success"] = False

    return fallback_res


def run_sync_daily(
    date_str: str = "",
    use_fallback: bool = True
) -> Dict[str, Any]:
    """
    Fungsi utama All-in-One EOD Synchronizer.
    Mengambil data perdagangan resmi BEI, menyimpan ke daftar_saham dan harga_saham.
    """
    start_time = datetime.now()
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║       ALL-IN-ONE IDX TRADING SUMMARY & PRICE ENGINE        ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")

    try:
        # Layer 1: IDX GetStockSummary
        payload = fetch_idx_trading_summary(date_str=date_str)
        rows_daftar, rows_harga, trading_date = parse_trading_summary_data(payload)

        # 1. Update master daftar_saham di DB
        stocks_count = sync_daftar_saham_bulk(rows_daftar)

        # 2. Update worker/daftar_saham.csv lokal
        csv_path = os.path.join(os.path.dirname(__file__), "daftar_saham.csv")
        try:
            update_local_csv(rows_daftar, csv_path)
        except Exception as csv_err:
            logger.warning("⚠️ Gagal update CSV lokal: %s", csv_err)

        # 3. Update tabel harga_saham di DB
        prices_count = sync_harga_saham_bulk(rows_harga)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info("🎉 SINKRONISASI LAYER 1 SUKSES!")
        logger.info(f"  📅 Tanggal Bursa: {trading_date}")
        logger.info(f"  🏢 Master Emiten: {stocks_count} saham")
        logger.info(f"  📈 Harga & Flow : {prices_count} baris")
        logger.info(f"  ⏱️ Waktu Proses : {duration:.2f} detik")

        return {
            "status": "success",
            "layer": 1,
            "source": "idx_official",
            "trading_date": str(trading_date) if trading_date else None,
            "stocks_synced": stocks_count,
            "prices_synced": prices_count,
            "duration_seconds": round(duration, 2),
        }

    except Exception as exc:
        logger.error("❌ LAYER 1 (IDX GetStockSummary) GAGAL: %s", exc)
        log_to_db("sync_idx_daily", "WARNING", f"Layer 1 gagal ({exc}), switching to Layer 2", exc_info=exc)

        if use_fallback:
            return execute_layer_2_fallback()
        else:
            raise


if __name__ == "__main__":
    target_date = ""
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        target_date = sys.argv[1]

    result = run_sync_daily(date_str=target_date)
    print("\nHasil Sinkronisasi:")
    print(result)
