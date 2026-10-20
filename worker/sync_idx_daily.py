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
import time
import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

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
    Dilengkapi rotasi profil TLS impersonation & session cookie warm-up untuk menembus Cloudflare WAF.
    """
    params: Dict[str, Any] = {
        "length": 9999,
        "start": 0,
    }
    if date_str:
        clean_d = date_str.replace("-", "").strip()
        params["date"] = clean_d

    referer_url = "https://www.idx.co.id/id/data-pasar/ringkasan-perdagangan/ringkasan-saham"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer_url,
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }

    proxy_url = os.getenv("IDX_PROXY_URL", "").strip() or None
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
    proxy_candidates = [proxies, None] if proxies else [None]

    profiles = [impersonate, "chrome124", "chrome120", "safari15_5", "edge101"]
    # Hilangkan duplikat dengan tetap menjaga urutan
    seen_p = set()
    ordered_profiles = [p for p in profiles if not (p in seen_p or seen_p.add(p))]

    last_error: Optional[Exception] = None

    for p_cfg in proxy_candidates:
        for prof in ordered_profiles:
            try:
                mode_lbl = f"{prof}+proxy" if p_cfg else prof
                logger.info("📡 Mengakses IDX GetStockSummary (impersonate=%s, date=%s)...", mode_lbl, date_str or "latest")
                response = cf_requests.get(
                    IDX_SUMMARY_URL,
                    params=params,
                    headers=headers,
                    impersonate=prof,
                    proxies=p_cfg,
                    timeout=timeout,
                )

                # Jika terhadang Cloudflare 403, lakukan Session Warm-up (ambil cookie __cf_bm dari halaman induk)
                if response.status_code == 403:
                    logger.info("🔄 HTTP 403 pada direct GET (%s), mencoba Session Cookie Warm-up...", mode_lbl)
                    with cf_requests.Session(impersonate=prof, proxies=p_cfg) as s:
                        s.get(
                            referer_url,
                            headers={
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            },
                            timeout=timeout,
                        )
                        response = s.get(
                            IDX_SUMMARY_URL,
                            params=params,
                            headers=headers,
                            timeout=timeout,
                        )

                if response.status_code == 200:
                    payload = response.json()
                    if isinstance(payload, dict) and "data" in payload:
                        return payload
                    raise ValueError("Payload IDX GetStockSummary tidak valid atau kosong.")

                last_error = RuntimeError(f"HTTP {response.status_code} saat mengakses IDX Trading Summary (impersonate={mode_lbl}).")
                logger.warning("⚠️ %s", last_error)
            except Exception as exc:
                last_error = exc
                logger.warning("⚠️ Impersonate %s gagal: %s", prof, exc)
                # Jika koneksi proxy lokal ditolak (misal WARP tidak aktif), langsung beralih ke kandidat tanpa proxy
                if p_cfg is not None and ("Connection refused" in str(exc) or "Failed to connect" in str(exc) or "(7)" in str(exc)):
                    break

    if last_error:
        raise last_error
    raise RuntimeError("Gagal mengakses IDX Trading Summary setelah mencoba semua profil TLS.")


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
    """Menulis ulang worker/daftar_saham.csv lokal dengan data terbaru sambil mempertahankan Tanggal Pencatatan historis."""
    existing_dates: Dict[str, str] = {}
    if os.path.exists(csv_path):
        try:
            with open(csv_path, "r", encoding="utf-8-sig") as rf:
                reader = csv.DictReader(rf, delimiter=";")
                for row in reader:
                    k = (row.get("Kode") or "").strip().upper()
                    tgl = (row.get("Tanggal Pencatatan") or "").strip()
                    if k and tgl:
                        existing_dates[k] = tgl
        except Exception as e:
            logger.warning("⚠️ Gagal membaca Tanggal Pencatatan lama dari CSV: %s", e)

    sorted_rows = sorted(daftar_rows, key=lambda x: x["kode"])
    lines = ["No;Kode;Nama Perusahaan;Tanggal Pencatatan;Saham;Papan Pencatatan\n"]
    for i, r in enumerate(sorted_rows, 1):
        saham_str = format_shares_dot(r["saham"])
        tgl_pencatatan = r.get("tanggal_pencatatan") or existing_dates.get(r["kode"], "")
        line = f"{i};{r['kode']};{r['nama_perusahaan']};{tgl_pencatatan};{saham_str};{r['papan_pencatatan']}\n"
        lines.append(line)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("📄 File %s berhasil disinkronkan (%d emiten).", csv_path, len(sorted_rows))


def sync_daftar_saham_bulk(daftar_rows: List[Dict[str, Any]]) -> int:
    """Melakukan bulk upsert ke tabel daftar_saham di DB."""
    if not daftar_rows:
        return 0

    dialect = get_dialect()
    if dialect == "postgresql":
        try:
            from psycopg2.extras import execute_values
            raw_conn = engine.raw_connection()
            cursor = raw_conn.cursor()
            sql = """
                INSERT INTO daftar_saham (
                    kode, no, nama_perusahaan, saham, tradeable_shares, papan_pencatatan, notasi_khusus, tanggal_update
                ) VALUES %s
                ON CONFLICT (kode) DO UPDATE SET
                    no = EXCLUDED.no,
                    nama_perusahaan = EXCLUDED.nama_perusahaan,
                    saham = EXCLUDED.saham,
                    tradeable_shares = EXCLUDED.tradeable_shares,
                    papan_pencatatan = EXCLUDED.papan_pencatatan,
                    notasi_khusus = EXCLUDED.notasi_khusus,
                    tanggal_update = CURRENT_DATE
            """
            data_tuples = [
                (
                    r["kode"], r["no"], r["nama_perusahaan"], r["saham"],
                    r["tradeable_shares"], r["papan_pencatatan"], r["notasi_khusus"],
                    date.today()
                )
                for r in daftar_rows
            ]
            execute_values(cursor, sql, data_tuples, page_size=1000)
            raw_conn.commit()
            raw_conn.close()
            logger.info("✅ Master emiten tersinkronisasi (fast execute_values): %d emiten.", len(daftar_rows))
            return len(daftar_rows)
        except Exception as pg_err:
            logger.warning("⚠️ execute_values gagal (%s), fallback ke standard execute...", pg_err)

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
    if dialect == "postgresql":
        try:
            from psycopg2.extras import execute_values
            raw_conn = engine.raw_connection()
            cursor = raw_conn.cursor()
            sql = """
                INSERT INTO harga_saham (
                    ticker, tanggal, open, high, low, close, volume,
                    value, frequency, foreign_buy, foreign_sell, foreign_net,
                    offer, offer_volume, bid, bid_volume,
                    non_regular_volume, non_regular_value
                ) VALUES %s
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
            """
            data_tuples = [
                (
                    r["ticker"], r["tanggal"], r["open"], r["high"], r["low"], r["close"], r["volume"],
                    r["value"], r["frequency"], r["foreign_buy"], r["foreign_sell"], r["foreign_net"],
                    r["offer"], r["offer_volume"], r["bid"], r["bid_volume"],
                    r["non_regular_volume"], r["non_regular_value"]
                )
                for r in harga_rows
            ]
            execute_values(cursor, sql, data_tuples, page_size=1000)
            raw_conn.commit()
            raw_conn.close()
            logger.info("✅ Harga & flow harian tersinkronisasi (fast execute_values): %d baris.", len(harga_rows))
            return len(harga_rows)
        except Exception as pg_err:
            logger.warning("⚠️ execute_values gagal (%s), fallback ke standard execute...", pg_err)

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
        pipe_success = bool(run_pipeline())
        fallback_res["prices_synced"] = 1 if pipe_success else 0
        fallback_res["success"] = pipe_success
        fallback_res["status"] = "success" if pipe_success else "failed"
    except Exception as err:
        logger.error("❌ Fallback pipeline Yahoo Finance gagal: %s", err)
        fallback_res["success"] = False
        fallback_res["status"] = "failed"

    return fallback_res


def detect_and_fill_idx_gaps(
    latest_trading_date: date,
    max_lookback_days: int = 14,
    delay_seconds: float = 1.0,
) -> List[str]:
    """
    Mendeteksi dan menambal otomatis (Auto-Backfill) tanggal bursa yang bolong
    atau yang sebelumnya hanya terisi oleh fallback Yahoo Finance (frequency = 0)
    dalam rentang `max_lookback_days` hari kalender ke belakang.
    """
    start_check = latest_trading_date - timedelta(days=max_lookback_days)
    official_dates: Set[date] = set()
    fallback_only_dates: Set[date] = set()

    try:
        with engine.connect() as conn:
            query = text("""
                SELECT
                    tanggal,
                    SUM(CASE WHEN frequency > 0 THEN 1 ELSE 0 END) AS idx_cnt,
                    COUNT(*) AS total_cnt
                FROM harga_saham
                WHERE tanggal >= :start_d AND tanggal < :end_d
                GROUP BY tanggal
            """)
            rows = conn.execute(
                query, {"start_d": start_check, "end_d": latest_trading_date}
            ).fetchall()

            for r in rows:
                dt_val = r[0]
                if isinstance(dt_val, str):
                    try:
                        dt_val = datetime.strptime(dt_val[:10], "%Y-%m-%d").date()
                    except Exception:
                        continue
                idx_cnt = int(r[1] or 0)
                total_cnt = int(r[2] or 0)
                if idx_cnt >= 500:
                    official_dates.add(dt_val)
                elif total_cnt > 0:
                    # Tanggal bursa aktif yang sebelumnya hanya terisi via Yahoo Finance fallback (frequency=0)
                    fallback_only_dates.add(dt_val)
    except Exception as db_err:
        logger.warning("⚠️ [Auto-Gap] Gagal memeriksa histori tanggal di DB: %s", db_err)
        return []

    if official_dates:
        last_official_date = max(official_dates)
    else:
        last_official_date = latest_trading_date - timedelta(days=min(7, max_lookback_days))

    candidate_dates: Set[date] = set(fallback_only_dates)
    cur_d = last_official_date + timedelta(days=1)
    while cur_d < latest_trading_date:
        if cur_d.weekday() < 5 and cur_d not in official_dates:
            candidate_dates.add(cur_d)
        cur_d += timedelta(days=1)

    if not candidate_dates:
        logger.info("✅ [Auto-Gap] Tidak ada hari bursa yang bolong (histori IDX lengkap hingga %s).", latest_trading_date)
        return []

    sorted_gaps = sorted(candidate_dates)
    logger.info(
        "🩹 [Auto-Gap] Terdeteksi %d kandidat tanggal yang belum memiliki data resmi IDX: %s",
        len(sorted_gaps),
        ", ".join(d.strftime("%Y-%m-%d") for d in sorted_gaps),
    )

    filled_dates: List[str] = []
    for d in sorted_gaps:
        d_iso = d.strftime("%Y-%m-%d")
        d_param = d.strftime("%Y%m%d")
        try:
            if filled_dates and delay_seconds > 0:
                time.sleep(delay_seconds)
            logger.info("📥 [Auto-Gap] Menambal data IDX untuk tanggal %s...", d_iso)
            res = run_sync_daily(
                date_str=d_param,
                use_fallback=False,
                fill_gaps=False,
                sync_master=False,
            )
            if res.get("status") == "success" and res.get("prices_synced", 0) > 0:
                filled_dates.append(d_iso)
                logger.info(
                    "✅ [Auto-Gap] Tanggal %s berhasil ditambal (%d saham).",
                    d_iso,
                    res.get("prices_synced", 0),
                )
            else:
                logger.info("ℹ️ [Auto-Gap] Tanggal %s dilewati (libur bursa / 0 saham).", d_iso)
        except Exception as gap_err:
            logger.warning("⚠️ [Auto-Gap] Gagal menambal tanggal %s: %s", d_iso, gap_err)

    return filled_dates


def run_sync_daily(
    date_str: str = "",
    use_fallback: bool = True,
    fill_gaps: bool = True,
    sync_master: bool = True,
) -> Dict[str, Any]:
    """
    Fungsi utama All-in-One EOD Synchronizer.
    Mengambil data perdagangan resmi BEI, menyimpan ke daftar_saham dan harga_saham,
    serta otomatis menambal hari bursa yang terlewat di belakangnya (Auto Gap-Detector).
    """
    start_time = datetime.now()
    if not date_str:
        logger.info("╔════════════════════════════════════════════════════════════╗")
        logger.info("║       ALL-IN-ONE IDX TRADING SUMMARY & PRICE ENGINE        ║")
        logger.info("╚════════════════════════════════════════════════════════════╝")

    try:
        # Layer 1: IDX GetStockSummary
        payload = fetch_idx_trading_summary(date_str=date_str)
        if date_str and not payload.get("data"):
            logger.info("ℹ️ Tanggal %s tidak memiliki data perdagangan (libur bursa / belum rilis).", date_str)
            return {
                "status": "empty",
                "layer": 1,
                "source": "idx_official",
                "trading_date": date_str,
                "stocks_synced": 0,
                "prices_synced": 0,
                "duration_seconds": round((datetime.now() - start_time).total_seconds(), 2),
            }

        rows_daftar, rows_harga, trading_date = parse_trading_summary_data(payload)

        stocks_count = 0
        if sync_master:
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

        # 4. Auto Gap-Detector (tambal otomatis hari bursa di belakangnya yang bolong / hanya Yahoo fallback)
        gaps_filled: List[str] = []
        if fill_gaps and not date_str and trading_date and not TEST_MODE:
            gaps_filled = detect_and_fill_idx_gaps(latest_trading_date=trading_date)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info("🎉 SINKRONISASI LAYER 1 SUKSES!")
        logger.info(f"  📅 Tanggal Bursa: {trading_date}")
        if sync_master:
            logger.info(f"  🏢 Master Emiten: {stocks_count} saham")
        logger.info(f"  📈 Harga & Flow : {prices_count} baris")
        if gaps_filled:
            logger.info(f"  🩹 Hari Ditambal: {len(gaps_filled)} hari ({', '.join(gaps_filled)})")
        logger.info(f"  ⏱️ Waktu Proses : {duration:.2f} detik")

        return {
            "status": "success",
            "layer": 1,
            "source": "idx_official",
            "trading_date": str(trading_date) if trading_date else None,
            "stocks_synced": stocks_count,
            "prices_synced": prices_count,
            "gaps_filled": gaps_filled,
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
