"""
worker/scanner_bali.py — Pre-Breakout Base (Bali Setup) Scanner Engine
=====================================================================
Mendeteksi pola konsolidasi ketat (Pre-Breakout Base) dengan volume kering
dan konfirmasi akumulasi broker summary (Smart Money / HMB).

Formula:
1. Prior Ignition Spike: Ada lonjakan volume >= 2.0x VMA20 & kenaikan >= 5% dalam 4-28 hari bursa sebelumnya.
2. Tight Base: Rentang konsolidasi 5-7 hari bursa (range_7) <= 8.0% (atau HL <= 13%).
3. Volume Dry-Up: Volume hari ini <= 0.40x VMA20 atau rata-rata 3 hari <= 0.45x VMA20.
4. Volatility Squeeze: Bollinger Bandwidth (BBW) <= 14.0%.
5. Trend & Price Guard: Harga saham >= 50 dan bertahan di atas / dekat MA20 (>= -4.0%).
6. Broksum Smart Money: Verifikasi akumulator terbesar & HMB (Harga Modal Bandar).
7. Scoring: 0 - 100 poin berdasarkan keketatan base, keringnya volume, dan konfirmasi akumulasi.
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np
from sqlalchemy import text

# Import database configuration
from db_config import engine, get_dialect, TEST_MODE

logger = logging.getLogger("BaliScanner")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def calculate_score(range_7: float, vol_dry: float, bbw: float, price: float, hmb: Optional[float], has_acc: bool) -> int:
    """Menghitung skor kualitas sinyal pre-breakout (0-100 poin)."""
    score = 0

    # 1. Base Tightness (Max 25 pts)
    if range_7 <= 3.0:
        score += 25
    elif range_7 <= 5.0:
        score += 20
    elif range_7 <= 7.0:
        score += 15
    else:
        score += 10

    # 2. Volume Dry-Up (Max 30 pts)
    if vol_dry <= 0.15:
        score += 30
    elif vol_dry <= 0.25:
        score += 25
    elif vol_dry <= 0.35:
        score += 20
    else:
        score += 15

    # 3. Volatility Squeeze / BBW (Max 20 pts)
    if bbw <= 6.0:
        score += 20
    elif bbw <= 9.0:
        score += 15
    elif bbw <= 12.0:
        score += 10
    else:
        score += 5

    # 4. Broker Summary Confirmation (Max 25 pts)
    if has_acc and hmb and hmb > 0 and price > 0:
        diff_pct = abs(price - hmb) / price * 100.0
        if diff_pct <= 4.0:
            score += 25
        elif diff_pct <= 8.0:
            score += 20
        else:
            score += 15
    elif has_acc:
        score += 15
    else:
        score += 5

    return min(100, max(0, score))


def scan_pre_breakout(target_date: date) -> List[Dict[str, Any]]:
    """
    Menjalankan pemindaian pre-breakout untuk tanggal trading tertentu.
    Mengembalikan list sinyal saham yang memenuhi kriteria.
    """
    logger.info(f"🔍 Memulai pemindaian Pre-Breakout Base untuk tanggal: {target_date}...")

    # Load 90 hari kalender ke belakang untuk rolling window yang akurat
    lookback_start = target_date - timedelta(days=90)
    query_prices = text("""
        SELECT ticker, tanggal, open, high, low, close, volume
        FROM harga_saham
        WHERE tanggal >= :start_date AND tanggal <= :end_date
        ORDER BY ticker, tanggal ASC
    """)

    with engine.connect() as conn:
        df_prices = pd.read_sql(query_prices, conn, params={
            "start_date": lookback_start.strftime("%Y-%m-%d"),
            "end_date": target_date.strftime("%Y-%m-%d")
        })

    if df_prices.empty:
        logger.warning(f"⚠️ Tidak ada data harga saham untuk tanggal {target_date}.")
        return []

    df_prices['tanggal'] = pd.to_datetime(df_prices['tanggal'])
    target_dt = pd.to_datetime(target_date)

    candidates = []

    # Filter teknikal per ticker
    for ticker, sub in df_prices.groupby('ticker'):
        sub = sub.sort_values('tanggal').reset_index(drop=True)
        idx_match = sub[sub['tanggal'] == target_dt].index
        if len(idx_match) == 0:
            continue
        curr_i = idx_match[0]
        if curr_i < 15:
            continue

        # Hitung moving averages dan bollinger bands
        vma20 = sub['volume'].rolling(20, min_periods=5).mean()
        ma20 = sub['close'].rolling(20, min_periods=5).mean()
        std20 = sub['close'].rolling(20, min_periods=5).std()
        bbw = (4 * std20) / ma20 * 100.0
        pct = sub['close'].pct_change()
        is_spike = (sub['volume'] / vma20.shift(1).replace(0, np.nan) >= 2.0) & (pct >= 0.05)

        # 1. Prior spike check in last 5 to 30 days
        spike_window = is_spike.iloc[max(0, curr_i - 28) : max(0, curr_i - 3)]
        if not spike_window.any():
            continue

        # 2. Consolidation window (last 7 trading days)
        w7 = sub.iloc[max(0, curr_i - 6) : curr_i + 1]
        if len(w7) < 5:
            continue

        min_c7 = w7['close'].min()
        max_c7 = w7['close'].max()
        if min_c7 <= 0:
            continue
        close_range_7 = (max_c7 - min_c7) / min_c7 * 100.0

        min_l7 = w7['low'].min()
        max_h7 = w7['high'].max()
        hl_range_7 = (max_h7 - min_l7) / min_l7 * 100.0 if min_l7 > 0 else 999.0

        curr_vol = sub.loc[curr_i, 'volume']
        curr_vma = vma20.iloc[curr_i]
        curr_close = sub.loc[curr_i, 'close']
        curr_ma20 = ma20.iloc[curr_i]
        curr_bbw = bbw.iloc[curr_i]

        if curr_vma <= 0 or curr_close < 50:
            continue

        vol_dry = curr_vol / curr_vma
        vol_dry_3d = sub['volume'].iloc[max(0, curr_i - 2) : curr_i + 1].mean() / curr_vma
        price_to_ma20 = (curr_close - curr_ma20) / curr_ma20 * 100.0

        # Kriteria Pre-Breakout Base:
        # - Close Range <= 8.0% ATAU High-Low Range <= 13.0%
        # - Volume Dry-Up <= 0.40x ATAU 3D avg <= 0.45x
        # - BBW <= 14.0%
        # - Price near/above MA20 >= -4.0%
        if (close_range_7 <= 8.0 or hl_range_7 <= 13.0) and (vol_dry <= 0.40 or vol_dry_3d <= 0.45) and curr_bbw <= 14.0 and price_to_ma20 >= -4.0:
            candidates.append({
                'date': target_date,
                'ticker': ticker,
                'price': float(curr_close),
                'range_7': round(float(close_range_7), 2),
                'volume_dry_ratio': round(float(min(vol_dry, vol_dry_3d)), 2),
                'bbw': round(float(curr_bbw), 2),
                'price_to_ma20': round(float(price_to_ma20), 2),
                'hmb': None,
                'top_accumulator': None,
                'score': 0
            })

    logger.info(f"🎯 Ditemukan {len(candidates)} kandidat teknikal pre-breakout pada {target_date}.")

    if not candidates:
        return []

    # Validasi broker summary untuk para kandidat
    candidate_tickers = [c['ticker'] for c in candidates]
    brok_start = target_date - timedelta(days=12)

    try:
        # Query broker summary portabel untuk SQLite maupun PostgreSQL
        placeholders = ", ".join([f":t_{i}" for i in range(len(candidate_tickers))])
        params = {f"t_{i}": candidate_tickers[i] for i in range(len(candidate_tickers))}
        params["start_date"] = brok_start.strftime("%Y-%m-%d")
        params["end_date"] = target_date.strftime("%Y-%m-%d")

        query_brok = text(f"""
            SELECT ticker, broker_code, buy_vol, buy_val, sell_vol, sell_val, net_vol, net_val
            FROM broker_summary
            WHERE ticker IN ({placeholders})
              AND date >= :start_date AND date <= :end_date
        """)

        with engine.connect() as conn:
            df_brok = pd.read_sql(query_brok, conn, params=params)

        brok_stats: Dict[str, Dict[str, Any]] = {}
        if not df_brok.empty:
            for t, g in df_brok.groupby('ticker'):
                agg = g.groupby('broker_code').agg({
                    'buy_vol': 'sum',
                    'buy_val': 'sum',
                    'net_vol': 'sum',
                    'net_val': 'sum'
                }).reset_index()

                # Cari broker pembeli bersih terbesar
                net_buyers = agg[agg['net_val'] > 0].sort_values('net_val', ascending=False)
                if not net_buyers.empty:
                    top_row = net_buyers.iloc[0]
                    top_code = top_row['broker_code']
                    b_vol = top_row['buy_vol']
                    b_val = top_row['buy_val']
                    hmb_val = round(b_val / (b_vol * 100.0), 1) if b_vol > 0 else None
                    brok_stats[t] = {
                        'top_acc': top_code,
                        'hmb': hmb_val,
                        'has_acc': True
                    }
                else:
                    brok_stats[t] = {
                        'top_acc': None,
                        'hmb': None,
                        'has_acc': False
                    }
    except Exception as e:
        logger.warning(f"⚠️ Gagal mengecek broker summary: {e}")
        brok_stats = {}

    # Hitung final score
    enriched_signals = []
    for c in candidates:
        t = c['ticker']
        b_info = brok_stats.get(t, {'top_acc': None, 'hmb': None, 'has_acc': False})
        c['top_accumulator'] = b_info['top_acc']
        c['hmb'] = b_info['hmb']
        c['score'] = calculate_score(
            range_7=c['range_7'],
            vol_dry=c['volume_dry_ratio'],
            bbw=c['bbw'],
            price=c['price'],
            hmb=c['hmb'],
            has_acc=b_info['has_acc']
        )
        enriched_signals.append(c)

    # Urutkan berdasarkan score tertinggi
    enriched_signals.sort(key=lambda x: x['score'], reverse=True)
    return enriched_signals


def save_signals_to_db(signals: List[Dict[str, Any]], target_date: date) -> int:
    """
    Menyimpan atau memperbarui sinyal pre-breakout ke tabel candlify_signals.
    Menghapus sinyal lama untuk tanggal target terlebih dahulu agar hasil re-scan selalu fresh dan sinkron.
    """
    inserted = 0
    with engine.begin() as conn:
        # 1. Bersihkan sinyal basi untuk tanggal target
        conn.execute(
            text("DELETE FROM candlify_signals WHERE date = :target_date"),
            {"target_date": target_date}
        )

        if not signals:
            logger.info(f"🧹 Sinyal lama untuk {target_date} dibersihkan (0 kandidat lolos).")
            return 0

        # 2. Insert batch sinyal baru
        dialect = get_dialect()
        if dialect == "sqlite":
            stmt = text("""
                INSERT OR REPLACE INTO candlify_signals (
                    date, ticker, price, range_7, volume_dry_ratio, bbw, price_to_ma20, hmb, top_accumulator, score
                ) VALUES (
                    :date, :ticker, :price, :range_7, :volume_dry_ratio, :bbw, :price_to_ma20, :hmb, :top_accumulator, :score
                )
            """)
        else:
            stmt = text("""
                INSERT INTO candlify_signals (
                    date, ticker, price, range_7, volume_dry_ratio, bbw, price_to_ma20, hmb, top_accumulator, score
                ) VALUES (
                    :date, :ticker, :price, :range_7, :volume_dry_ratio, :bbw, :price_to_ma20, :hmb, :top_accumulator, :score
                )
                ON CONFLICT (date, ticker) DO UPDATE SET
                    price = EXCLUDED.price,
                    range_7 = EXCLUDED.range_7,
                    volume_dry_ratio = EXCLUDED.volume_dry_ratio,
                    bbw = EXCLUDED.bbw,
                    price_to_ma20 = EXCLUDED.price_to_ma20,
                    hmb = EXCLUDED.hmb,
                    top_accumulator = EXCLUDED.top_accumulator,
                    score = EXCLUDED.score
            """)

        for s in signals:
            clean_s = {
                'date': s['date'],
                'ticker': str(s['ticker']),
                'price': float(s['price']),
                'range_7': float(s['range_7']),
                'volume_dry_ratio': float(s['volume_dry_ratio']),
                'bbw': float(s['bbw']),
                'price_to_ma20': float(s['price_to_ma20']),
                'hmb': float(s['hmb']) if s['hmb'] is not None else None,
                'top_accumulator': str(s['top_accumulator']) if s['top_accumulator'] is not None else None,
                'score': int(s['score'])
            }
            conn.execute(stmt, clean_s)
            inserted += 1

    logger.info(f"💾 Berhasil menyimpan {inserted} sinyal ke candlify_signals untuk {target_date}.")
    return inserted


def run_scanner(target_date: Optional[date] = None, backfill_days: int = 1) -> int:
    """
    Fungsi entry point untuk dieksekusi oleh pipeline atau CLI.
    """
    total_saved = 0

    with engine.connect() as conn:
        if target_date is None:
            max_d = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            if not max_d:
                logger.error("❌ Database harga_saham kosong, scanner dibatalkan.")
                return 0
            if isinstance(max_d, str):
                target_date = datetime.strptime(max_d, "%Y-%m-%d").date()
            elif isinstance(max_d, datetime):
                target_date = max_d.date()
            else:
                target_date = max_d

        if backfill_days > 1:
            # Ambil n tanggal trading terakhir
            trading_dates_res = conn.execute(text("""
                SELECT DISTINCT tanggal FROM harga_saham 
                WHERE tanggal <= :d
                ORDER BY tanggal DESC LIMIT :lim
            """), {"d": target_date.strftime("%Y-%m-%d"), "lim": backfill_days}).fetchall()
            dates_to_scan = [row[0] for row in reversed(trading_dates_res)]
        else:
            dates_to_scan = [target_date]

    for d in dates_to_scan:
        if isinstance(d, str):
            d_obj = datetime.strptime(d, "%Y-%m-%d").date()
        elif isinstance(d, datetime):
            d_obj = d.date()
        else:
            d_obj = d

        signals = scan_pre_breakout(d_obj)
        saved = save_signals_to_db(signals, d_obj)
        total_saved += saved

    logger.info(f"✅ Pre-Breakout Scanner selesai. Total sinyal: {total_saved}.")
    return total_saved


if __name__ == "__main__":
    args = sys.argv[1:]
    target_d = None
    backfill = 1

    if "--date" in args:
        idx = args.index("--date")
        if idx + 1 < len(args):
            target_d = datetime.strptime(args[idx + 1], "%Y-%m-%d").date()

    if "--backfill" in args:
        idx = args.index("--backfill")
        if idx + 1 < len(args):
            backfill = int(args[idx + 1])

    run_scanner(target_date=target_d, backfill_days=backfill)
