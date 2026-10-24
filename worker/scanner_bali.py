"""
worker/scanner_bali.py — Pre-Breakout Base Scanner Engine
=========================================================
Mendeteksi pola konsolidasi ketat (Pre-Breakout Base) dengan volume kering
dan konfirmasi akumulasi broker summary (Smart Money / HMB).

Formula:
1. Prior Ignition Spike: Ada lonjakan volume >= 2.0x VMA20 & kenaikan >= 5% dalam 4-28 hari bursa sebelumnya.
2. Tight Base: Rentang konsolidasi 5-7 hari bursa (range_7) <= 8.0% (atau HL <= 13%).
3. Volume Dry-Up: Volume hari ini <= 0.40x VMA20 atau rata-rata 3 hari <= 0.45x VMA20.
4. Volatility Squeeze: Bollinger Bandwidth (BBW) <= 14.0%.
5. Trend & Price Guard: Harga saham >= 50 dan bertahan di atas / dekat MA20 (>= -4.0%).
6. Broksum Smart Money (Strict Base Window + Freshness Guard):
   - Hanya menghitung broker summary di dalam tanggal fase konsolidasi (w7 = 5-7 hari bursa terakhir).
   - Wajib memiliki minimal >= 3 hari bursa broksum aktif di dalam base dan maksimal tertinggal 2 hari bursa.
   - HMB dihitung dari Top 5 Accumulators (Net-Inventory Weighted) konsisten dengan modul Bandarmologi.
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
from typing import Optional, List, Dict, Any, Set

import pandas as pd
import numpy as np
from sqlalchemy import text

import os

# Ensure worker directory is in sys.path
_WORKER_DIR = os.path.dirname(os.path.abspath(__file__))
if _WORKER_DIR not in sys.path:
    sys.path.insert(0, _WORKER_DIR)

# Import database configuration
from db_config import engine, get_dialect, TEST_MODE

logger = logging.getLogger("BaliScanner")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def _to_date(val: Any) -> Optional[date]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, pd.Timestamp):
        return val.date()
    if isinstance(val, str):
        return datetime.strptime(val[:10], "%Y-%m-%d").date()
    return None


def calculate_score(
    range_7: float,
    vol_dry: float,
    bbw: float,
    price: float,
    hmb: Optional[float],
    has_acc: bool,
    dominance: float = 0.0,
    clv: float = 0.0,
    aar: float = 1.0,
    up_down_vol_ratio: float = 1.0,
    is_pocket_pivot: bool = False
) -> int:
    """
    Menghitung skor kualitas sinyal pre-breakout (0-100 poin).
    Termasuk bobot:
    1. Keketatan Base (Max 20 pts)
    2. Volume Dry-Up (Max 20 pts)
    3. Volatility Squeeze / BBW (Max 15 pts)
    4. Broker Akumulasi (Net-Inventory HMB, Dominance & AAR) (Max 25 pts)
    5. Price Absorption (CLV 3D & Up/Down Volume Ratio) (Max 15 pts)
    6. Bonus Pocket Pivot Trigger (+5 pts)
    """
    score = 0

    # 1. Base Tightness (Max 20 pts)
    if range_7 <= 3.0:
        score += 20
    elif range_7 <= 5.0:
        score += 16
    elif range_7 <= 7.0:
        score += 12
    elif range_7 <= 10.0:
        score += 8
    else:
        score += 4

    # 2. Volume Dry-Up (Max 20 pts)
    if vol_dry <= 0.15:
        score += 20
    elif vol_dry <= 0.25:
        score += 16
    elif vol_dry <= 0.35:
        score += 12
    elif vol_dry <= 0.45:
        score += 8
    else:
        score += 4

    # 3. Volatility Squeeze / BBW (Max 15 pts)
    if bbw <= 6.0:
        score += 15
    elif bbw <= 9.0:
        score += 12
    elif bbw <= 12.0:
        score += 8
    else:
        score += 5

    # 4. Broker Summary Confirmation, HMB & AAR (Max 25 pts)
    if has_acc and hmb and hmb > 0 and price > 0:
        diff_pct = abs(price - hmb) / price * 100.0
        hmb_pts = 12 if diff_pct <= 4.0 else (8 if diff_pct <= 8.0 else 4)
        dom_pts = 8 if dominance >= 30.0 else (5 if dominance >= 15.0 else 2)
        aar_pts = 5 if aar >= 1.5 else (3 if aar >= 1.0 else 1)
        score += (hmb_pts + dom_pts + aar_pts)
    elif has_acc:
        dom_pts = 8 if dominance >= 30.0 else 5
        aar_pts = 5 if aar >= 1.5 else 2
        score += (4 + dom_pts + aar_pts)
    else:
        score += 5

    # 5. Price Absorption (CLV) & Up/Down Vol Ratio (Max 15 pts)
    clv_pts = 8 if clv >= 0.50 else (6 if clv >= 0.0 else (3 if clv >= -0.50 else 1))
    vol_pts = 7 if up_down_vol_ratio >= 1.25 else (5 if up_down_vol_ratio >= 1.0 else 2)
    score += (clv_pts + vol_pts)

    # 6. Pocket Pivot Trigger Bonus (+5 pts)
    if is_pocket_pivot:
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

        curr_high = float(sub.loc[curr_i, 'high'])
        curr_low = float(sub.loc[curr_i, 'low'])
        hl_diff = curr_high - curr_low
        clv = round(((curr_close - curr_low) - (curr_high - curr_close)) / hl_diff, 2) if hl_diff > 0 else 0.0
        adt20 = round(float(curr_vma * curr_close), 0)

        # Base Up/Down Volume Ratio & 3-Day Mean CLV
        up_days = w7[w7['close'] >= w7['open']]
        down_days = w7[w7['close'] < w7['open']]
        up_vol_mean = up_days['volume'].mean() if len(up_days) > 0 else 0.0
        down_vol_mean = down_days['volume'].mean() if len(down_days) > 0 else 0.0
        up_down_vol_ratio = round(float(up_vol_mean / down_vol_mean), 2) if down_vol_mean > 0 else 2.0

        w3 = sub.iloc[max(0, curr_i - 2) : curr_i + 1]
        hl_diffs = (w3['high'] - w3['low']).replace(0, np.nan)
        clv_series = ((w3['close'] - w3['low']) - (w3['high'] - w3['close'])) / hl_diffs
        clv_3d = round(float(clv_series.fillna(0.0).mean()), 2)

        # Pocket Pivot Trigger Detection
        lookback_10 = sub.iloc[max(0, curr_i - 10) : curr_i]
        down_candles = lookback_10[lookback_10['close'] < lookback_10['open']]
        max_down_vol_10d = float(down_candles['volume'].max()) if len(down_candles) > 0 else 0.0
        ma5 = float(sub['close'].rolling(5, min_periods=1).mean().iloc[curr_i])
        support_base = float(min_l7)
        is_pocket_pivot = bool((curr_vol > max_down_vol_10d) and (curr_close > ma5) and (curr_close <= support_base * 1.05))

        # Kriteria Pre-Breakout Base:
        # - Close Range <= 8.0% ATAU High-Low Range <= 13.0%
        # - Volume Dry-Up <= 0.40x ATAU 3D avg <= 0.45x
        # - BBW <= 14.0%
        # - Price near/above MA20 >= -4.0%
        if (close_range_7 <= 8.0 or hl_range_7 <= 13.0) and (vol_dry <= 0.40 or vol_dry_3d <= 0.45) and curr_bbw <= 14.0 and price_to_ma20 >= -4.0:
            base_dates = sorted([_to_date(d) for d in w7['tanggal'] if _to_date(d) is not None])
            candidates.append({
                'date': target_date,
                'ticker': ticker,
                'price': float(curr_close),
                'range_7': round(float(close_range_7), 2),
                'volume_dry_ratio': round(float(min(vol_dry, vol_dry_3d)), 2),
                'bbw': round(float(curr_bbw), 2),
                'price_to_ma20': round(float(price_to_ma20), 2),
                'clv': clv,
                'clv_3d': clv_3d,
                'up_down_vol_ratio': up_down_vol_ratio,
                'is_pocket_pivot': is_pocket_pivot,
                'adt20': adt20,
                'base_dates': base_dates,
                'base_start_date': base_dates[0] if base_dates else (target_date - timedelta(days=10)),
                'hmb': None,
                'top_accumulator': None,
                'dominance': 0.0,
                'aar': 1.0,
                'board': 'Pengembangan',
                'score': 0
            })

    logger.info(f"🎯 Ditemukan {len(candidates)} kandidat teknikal pre-breakout pada {target_date}.")

    if not candidates:
        return []

    # Validasi broker summary khusus di dalam jendela konsolidasi (w7) masing-masing kandidat
    candidate_tickers = [c['ticker'] for c in candidates]
    cand_base_map = {c['ticker']: c['base_dates'] for c in candidates}
    min_base_start = min(c['base_start_date'] for c in candidates)

    try:
        placeholders = ", ".join([f":t_{i}" for i in range(len(candidate_tickers))])
        params = {f"t_{i}": candidate_tickers[i] for i in range(len(candidate_tickers))}
        params["start_date"] = min_base_start.strftime("%Y-%m-%d")
        params["end_date"] = target_date.strftime("%Y-%m-%d")

        query_brok = text(f"""
            SELECT ticker, date, broker_code, buy_vol, buy_val, sell_vol, sell_val, net_vol, net_val
            FROM broker_summary
            WHERE ticker IN ({placeholders})
              AND date >= :start_date AND date <= :end_date
        """)

        with engine.connect() as conn:
            df_brok = pd.read_sql(query_brok, conn, params=params)

        brok_stats: Dict[str, Dict[str, Any]] = {}
        if not df_brok.empty:
            df_brok['norm_date'] = df_brok['date'].apply(_to_date)

            for t, g_all in df_brok.groupby('ticker'):
                base_dates_t = cand_base_map.get(t, [])
                base_start_t = base_dates_t[0] if base_dates_t else min_base_start

                # Filter ketat HANYA transaksi broker di dalam jendela base konsolidasi (w7)
                g = g_all[(g_all['norm_date'] >= base_start_t) & (g_all['norm_date'] <= target_date)]
                brok_dates_in_base = sorted([d for d in g['norm_date'].unique() if d is not None])

                # Freshness & Coverage Guard:
                # 1. Wajib ada minimal >= 3 hari bursa broksum aktif di dalam base w7
                # 2. Tanggal broksum terakhir tidak boleh tertinggal > 2 hari bursa dari target_date
                min_req_days = min(3, len(base_dates_t)) if base_dates_t else 3
                max_lag_cutoff = base_dates_t[-min(3, len(base_dates_t))] if base_dates_t else (target_date - timedelta(days=4))
                is_brok_fresh_and_valid = (
                    len(brok_dates_in_base) >= min_req_days
                    and brok_dates_in_base[-1] >= max_lag_cutoff
                )

                if not is_brok_fresh_and_valid:
                    logger.info(
                        f"⚠️ [{t}] Broksum base belum lengkap/basi "
                        f"({len(brok_dates_in_base)}/{len(base_dates_t)} hari bursa, "
                        f"last={brok_dates_in_base[-1] if brok_dates_in_base else 'None'}). "
                        f"Skip klaim HMB & poin akumulasi."
                    )
                    brok_stats[t] = {
                        'top_acc': None,
                        'hmb': None,
                        'has_acc': False,
                        'dominance': 0.0,
                        'aar': 1.0
                    }
                    continue

                agg = g.groupby('broker_code').agg({
                    'buy_vol': 'sum',
                    'buy_val': 'sum',
                    'net_vol': 'sum',
                    'net_val': 'sum'
                }).reset_index()

                # Net-Inventory Weighted HMB (Top 5 Accumulators), Dominansi & HHI Asymmetry (AAR)
                net_buyers = agg[agg['net_val'] > 0].sort_values('net_val', ascending=False)
                if not net_buyers.empty:
                    top_row = net_buyers.iloc[0]
                    top_code = top_row['broker_code']
                    top_net_val = float(top_row['net_val'])
                    total_pos_net_val = float(net_buyers['net_val'].sum())
                    dominance_pct = round(top_net_val / total_pos_net_val * 100.0, 1) if total_pos_net_val > 0 else 0.0

                    # Net-Inventory Weighted HMB menggunakan Top 5 Accumulators (konsisten dengan lib/bandarmologi.py)
                    top5_acc = agg[agg['net_vol'] > 0].nlargest(5, 'net_vol')
                    valid_acc = top5_acc[top5_acc['buy_vol'] > 0]
                    if valid_acc.empty:
                        valid_acc = net_buyers[(net_buyers['buy_vol'] > 0) & (net_buyers['net_vol'] > 0)].head(5)

                    if not valid_acc.empty:
                        avg_buy_prices = valid_acc['buy_val'] / (valid_acc['buy_vol'] * 100.0)
                        weighted_cost = (valid_acc['net_vol'] * avg_buy_prices).sum()
                        total_net_vol = valid_acc['net_vol'].sum()
                        hmb_val = round(float(weighted_cost / total_net_vol), 1) if total_net_vol > 0 else None
                    else:
                        hmb_val = None

                    # Herfindahl-Hirschman Index (HHI) & Accumulation Asymmetry Ratio (AAR)
                    pos_b = agg[agg['net_val'] > 0]
                    neg_s = agg[agg['net_val'] < 0]
                    tot_p = float(pos_b['net_val'].sum())
                    tot_n = abs(float(neg_s['net_val'].sum()))
                    hhi_b = float(((pos_b['net_val'] / tot_p) ** 2).sum()) if tot_p > 0 else 0.0
                    hhi_s = float(((neg_s['net_val'].abs() / tot_n) ** 2).sum()) if tot_n > 0 else 0.0
                    aar_val = round(float(hhi_b / hhi_s), 2) if hhi_s > 0 else (2.0 if hhi_b > 0 else 1.0)

                    brok_stats[t] = {
                        'top_acc': top_code,
                        'hmb': hmb_val,
                        'has_acc': True,
                        'dominance': dominance_pct,
                        'aar': aar_val
                    }
                else:
                    brok_stats[t] = {
                        'top_acc': None,
                        'hmb': None,
                        'has_acc': False,
                        'dominance': 0.0,
                        'aar': 1.0
                    }
    except Exception as e:
        logger.warning(f"⚠️ Gagal mengecek broker summary: {e}")
        brok_stats = {}

    # Ambil papan pencatatan dari tabel daftar_saham
    board_map: Dict[str, str] = {}
    try:
        with engine.connect() as conn:
            b_placeholders = ", ".join([f":bt_{i}" for i in range(len(candidate_tickers))])
            b_params = {f"bt_{i}": candidate_tickers[i] for i in range(len(candidate_tickers))}
            query_board = text(f"SELECT kode, papan_pencatatan FROM daftar_saham WHERE kode IN ({b_placeholders})")
            b_rows = conn.execute(query_board, b_params).fetchall()
            for b_r in b_rows:
                board_map[b_r[0]] = b_r[1] or 'Pengembangan'
    except Exception as e:
        logger.warning(f"⚠️ Gagal mengambil papan pencatatan dari DB: {e}")

    # Hitung final score
    enriched_signals = []
    for c in candidates:
        t = c['ticker']
        b_info = brok_stats.get(t, {'top_acc': None, 'hmb': None, 'has_acc': False, 'dominance': 0.0, 'aar': 1.0})
        c['top_accumulator'] = b_info['top_acc']
        c['hmb'] = b_info['hmb']
        c['dominance'] = b_info.get('dominance', 0.0)
        c['aar'] = b_info.get('aar', 1.0)
        c['board'] = board_map.get(t, 'Pengembangan')
        c['score'] = calculate_score(
            range_7=c['range_7'],
            vol_dry=c['volume_dry_ratio'],
            bbw=c['bbw'],
            price=c['price'],
            hmb=c['hmb'],
            has_acc=b_info['has_acc'],
            dominance=b_info.get('dominance', 0.0),
            clv=c.get('clv_3d', c.get('clv', 0.0)),
            aar=b_info.get('aar', 1.0),
            up_down_vol_ratio=c.get('up_down_vol_ratio', 1.0),
            is_pocket_pivot=c.get('is_pocket_pivot', False)
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

        # 2. Insert batch sinyal baru beserta metrik institusional v2
        dialect = get_dialect()
        if dialect == "sqlite":
            stmt = text("""
                INSERT OR REPLACE INTO candlify_signals (
                    date, ticker, price, range_7, volume_dry_ratio, bbw, price_to_ma20,
                    hmb, top_accumulator, dominance, aar, clv_3d, up_down_vol_ratio, is_pocket_pivot, score
                ) VALUES (
                    :date, :ticker, :price, :range_7, :volume_dry_ratio, :bbw, :price_to_ma20,
                    :hmb, :top_accumulator, :dominance, :aar, :clv_3d, :up_down_vol_ratio, :is_pocket_pivot, :score
                )
            """)
        else:
            stmt = text("""
                INSERT INTO candlify_signals (
                    date, ticker, price, range_7, volume_dry_ratio, bbw, price_to_ma20,
                    hmb, top_accumulator, dominance, aar, clv_3d, up_down_vol_ratio, is_pocket_pivot, score
                ) VALUES (
                    :date, :ticker, :price, :range_7, :volume_dry_ratio, :bbw, :price_to_ma20,
                    :hmb, :top_accumulator, :dominance, :aar, :clv_3d, :up_down_vol_ratio, :is_pocket_pivot, :score
                )
                ON CONFLICT (date, ticker) DO UPDATE SET
                    price = EXCLUDED.price,
                    range_7 = EXCLUDED.range_7,
                    volume_dry_ratio = EXCLUDED.volume_dry_ratio,
                    bbw = EXCLUDED.bbw,
                    price_to_ma20 = EXCLUDED.price_to_ma20,
                    hmb = EXCLUDED.hmb,
                    top_accumulator = EXCLUDED.top_accumulator,
                    dominance = EXCLUDED.dominance,
                    aar = EXCLUDED.aar,
                    clv_3d = EXCLUDED.clv_3d,
                    up_down_vol_ratio = EXCLUDED.up_down_vol_ratio,
                    is_pocket_pivot = EXCLUDED.is_pocket_pivot,
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
                'dominance': float(s.get('dominance') or 0.0),
                'aar': float(s.get('aar') or 1.0),
                'clv_3d': float(s.get('clv_3d') or s.get('clv') or 0.0),
                'up_down_vol_ratio': float(s.get('up_down_vol_ratio') or 1.0),
                'is_pocket_pivot': (1 if s.get('is_pocket_pivot') else 0) if dialect == "sqlite" else bool(s.get('is_pocket_pivot', False)),
                'score': int(s['score'])
            }
            conn.execute(stmt, clean_s)
            inserted += 1

    logger.info(f"💾 Berhasil menyimpan {inserted} sinyal ke candlify_signals untuk {target_date}.")
    return inserted


def _detect_dirty_signal_dates(
    conn,
    latest_date: date,
    touched_dates: Optional[List[Any]] = None,
    lookback_trading_days: int = 10
) -> List[date]:
    """
    Mendeteksi tanggal perdagangan dalam 10 hari bursa terakhir yang perlu di-scan ulang:
    1. Tanggal yang belum ada di candlify_signals, ATAU
    2. Tanggal yang sinyalnya kemarin disimpan tanpa HMB (hmb IS NULL) saat broksum sedang down,
       padahal sekarang broker_summary pada jendela tanggal tersebut sudah terisi, ATAU
    3. Tanggal yang jendela base 7 harinya baru saja mendapat tambalan broksum dari Harvester (touched_dates).
    """
    rows = conn.execute(text("""
        SELECT DISTINCT tanggal FROM harga_saham
        WHERE tanggal <= :d
        ORDER BY tanggal DESC LIMIT :lim
    """), {"d": latest_date.strftime("%Y-%m-%d"), "lim": lookback_trading_days}).fetchall()

    recent_dates: List[date] = sorted([_to_date(r[0]) for r in rows if _to_date(r[0]) is not None])
    if not recent_dates:
        return [latest_date]

    min_recent = recent_dates[0]
    touched_set: Set[date] = {_to_date(d) for d in (touched_dates or []) if _to_date(d) is not None}

    # Cek status sinyal di candlify_signals untuk recent_dates
    sig_rows = conn.execute(text("""
        SELECT date,
               COUNT(*) AS total_sig,
               SUM(CASE WHEN hmb IS NOT NULL THEN 1 ELSE 0 END) AS with_hmb
        FROM candlify_signals
        WHERE date >= :min_d AND date <= :max_d
        GROUP BY date
    """), {"min_d": min_recent.strftime("%Y-%m-%d"), "max_d": latest_date.strftime("%Y-%m-%d")}).fetchall()

    sig_status: Dict[date, Dict[str, int]] = {}
    for sr in sig_rows:
        d_k = _to_date(sr[0])
        if d_k:
            sig_status[d_k] = {"total": int(sr[1] or 0), "with_hmb": int(sr[2] or 0)}

    # Cek ketersediaan broker_summary per tanggal
    brok_rows = conn.execute(text("""
        SELECT date, COUNT(DISTINCT ticker) AS ticker_cnt
        FROM broker_summary
        WHERE date >= :min_d AND date <= :max_d
        GROUP BY date
    """), {"min_d": min_recent.strftime("%Y-%m-%d"), "max_d": latest_date.strftime("%Y-%m-%d")}).fetchall()

    brok_counts: Dict[date, int] = {}
    for br in brok_rows:
        d_k = _to_date(br[0])
        if d_k:
            brok_counts[d_k] = int(br[1] or 0)

    dirty_dates: Set[date] = {latest_date}

    for idx, d in enumerate(recent_dates):
        # Jendela base 7 hari bursa untuk tanggal d
        base_window_d = set(recent_dates[max(0, idx - 6) : idx + 1])

        # 1. Jika Harvester baru saja menambal tanggal historis di dalam base window ini
        historical_touched = {td for td in touched_set if td < latest_date}
        if historical_touched and (base_window_d & historical_touched):
            dirty_dates.add(d)
            continue

        # 2. Jika sinyal tanggal d kemarin disimpan tanpa HMB (with_hmb == 0) saat broksum sedang down,
        #    dan sekarang sudah ada broksum aktif di tanggal d atau H-1 bursa
        st = sig_status.get(d)
        recent_2_base = recent_dates[max(0, idx - 1) : idx + 1]
        has_brok_now = any(brok_counts.get(bd, 0) >= 50 for bd in recent_2_base)
        if has_brok_now and st is not None and st["total"] > 0 and st["with_hmb"] == 0:
            dirty_dates.add(d)

    sorted_dirty = sorted(dirty_dates)
    if len(sorted_dirty) > 1:
        logger.info(
            "🔄 [Auto Re-Scan] Terdeteksi %d tanggal dalam 10 hari bursa terakhir yang perlu pembaruan sinyal: %s",
            len(sorted_dirty),
            ", ".join(d.strftime("%Y-%m-%d") for d in sorted_dirty)
        )
    return sorted_dirty


def run_scanner(
    target_date: Optional[date] = None,
    backfill_days: int = 1,
    touched_dates: Optional[List[Any]] = None
) -> int:
    """
    Fungsi entry point untuk dieksekusi oleh pipeline atau CLI.
    Mendukung Auto Re-Scan otomatis jika ada gap broker_summary yang baru saja terisi.
    """
    try:
        from db_config import migrate_schema
        migrate_schema()
    except Exception:
        pass

    total_saved = 0

    with engine.connect() as conn:
        if target_date is None:
            max_d = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            if not max_d:
                logger.error("❌ Database harga_saham kosong, scanner dibatalkan.")
                return 0
            target_date = _to_date(max_d)

        if backfill_days > 1:
            # Ambil n tanggal trading terakhir secara eksplisit
            trading_dates_res = conn.execute(text("""
                SELECT DISTINCT tanggal FROM harga_saham 
                WHERE tanggal <= :d
                ORDER BY tanggal DESC LIMIT :lim
            """), {"d": target_date.strftime("%Y-%m-%d"), "lim": backfill_days}).fetchall()
            dates_to_scan = [_to_date(row[0]) for row in reversed(trading_dates_res) if _to_date(row[0]) is not None]
        else:
            # Smart Auto Re-Scan: deteksi tanggal dalam 10 hari bursa terakhir yang baru ditambal broksum-nya
            dates_to_scan = _detect_dirty_signal_dates(conn, target_date, touched_dates=touched_dates)

    for d_obj in dates_to_scan:
        if d_obj is None:
            continue
        signals = scan_pre_breakout(d_obj)
        saved = save_signals_to_db(signals, d_obj)
        total_saved += saved

    logger.info(f"✅ Pre-Breakout Scanner selesai. Total sinyal disimpan/diperbarui: {total_saved}.")
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
