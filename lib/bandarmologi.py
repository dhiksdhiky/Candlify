"""
v2/lib/bandarmologi.py — Fast & Lean Bandarmologi Calculation Engine
===================================================================
Features:
- Single-pass query from Neon PostgreSQL (broker_summary)
- Thread-safe lazy database engine with exponential backoff
- In-memory caching with market-hours aware dynamic TTL
- Calculates:
  1. HMB (Harga Modal Bandar) — Weighted average price of Top 5 accumulators (rolling 20 days)
  2. Net Flow Bandar — Top 3 Net Buyers vs Top 3 Net Sellers (per day)
  3. Accumulation / Distribution Status & Broker Breakdown
"""

import os
import re
import time
import logging
import threading
from datetime import datetime, date, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CandlifyBandarV2")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Import centralized DB engine & utility helpers
from lib.db import get_db_engine
from lib.utils import (
    WIB_TZ, now_wib, is_idx_market_open, get_bandar_ttl,
    SYMBOL_REGEX, clean_symbol
)

# In-Memory Cache: { cache_key: (timestamp, data_dict) }
_BANDAR_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_BANDAR_CACHE_LOCK = threading.Lock()
_CACHE_MAX_ENTRIES = 128

# Raw DataFrame cache per symbol: {symbol: (timestamp, df)}
_RAW_DF_CACHE: Dict[str, Tuple[float, pd.DataFrame]] = {}
_RAW_DF_LOCK = threading.Lock()

# Market Intelligence Cache per symbol: {symbol: (timestamp, data_dict)}
_INTELLIGENCE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_INTELLIGENCE_LOCK = threading.Lock()


def _evict_oldest_entries(cache_dict: Dict[str, Tuple[float, Any]], max_entries: int = _CACHE_MAX_ENTRIES) -> None:
    """Evict 20% entri tertua jika cache penuh untuk mencegah cache stampede."""
    if len(cache_dict) >= max_entries:
        oldest_keys = sorted(cache_dict.keys(), key=lambda k: cache_dict[k][0])[: max(1, max_entries // 5)]
        for k in oldest_keys:
            cache_dict.pop(k, None)


def get_stock_market_intelligence(symbol: str) -> Dict[str, Any]:
    """
    Menghitung Market Intelligence resmi dari BEI (Official IDX Data):
    1. Foreign Flow (Asing): 1D, 5D, 20D (Lot & Estimasi Rupiah berbasis VWAP harian, Buy vs Sell)
    2. Trade Size (Whale vs Ritel): Lot/Trade hari ini vs Rerata 20 hari
    3. Pasar Nego (Crossing Saham): Volume, Value & Deteksi Crossing (> Rp 10 Miliar / > 1% Shares)
    4. Emiten Info: Notasi Khusus BEI & Tradeable Shares
    """
    clean_sym = clean_symbol(symbol)
    now = time.time()
    ttl = get_bandar_ttl()

    with _INTELLIGENCE_LOCK:
        if clean_sym in _INTELLIGENCE_CACHE:
            ts, cached_intel = _INTELLIGENCE_CACHE[clean_sym]
            if now - ts < ttl:
                return cached_intel

    engine = get_db_engine()
    empty_intel = {
        "success": False,
        "symbol": clean_sym,
        "foreign_flow": {
            "today_net_shares": 0, "today_net_lots": 0, "today_net_val": 0.0,
            "today_buy_shares": 0, "today_buy_lots": 0,
            "today_sell_shares": 0, "today_sell_lots": 0,
            "flow_5d_shares": 0, "flow_5d_lots": 0, "flow_5d_val": 0.0,
            "flow_20d_shares": 0, "flow_20d_lots": 0, "flow_20d_val": 0.0,
            "status_1d": "NEUTRAL", "status_5d": "NEUTRAL", "status_20d": "NEUTRAL"
        },
        "trade_size": {
            "today_lot_per_trade": 0.0, "avg_lot_per_trade_20d": 0.0,
            "whale_ratio": 1.0, "whale_label": "Normal", "frequency": 0
        },
        "pasar_nego": {
            "volume_shares": 0, "volume_lots": 0, "value": 0.0,
            "has_crossing": False, "crossing_reason": ""
        },
        "emiten_info": {
            "notasi_khusus": "", "tradeable_shares": 0, "papan_pencatatan": "Utama"
        }
    }

    if not engine:
        return empty_intel

    try:
        with engine.connect() as conn:
            # 1. Ambil 20 hari data harga_saham terbaru
            q_h = text("""
                SELECT tanggal, close, volume, value, frequency,
                       foreign_buy, foreign_sell, foreign_net,
                       non_regular_volume, non_regular_value
                FROM harga_saham
                WHERE ticker = :ticker
                ORDER BY tanggal DESC
                LIMIT 20
            """)
            df_h = pd.read_sql(q_h, conn, params={"ticker": clean_sym})

            # 2. Ambil info daftar_saham
            q_d = text("""
                SELECT notasi_khusus, tradeable_shares, papan_pencatatan
                FROM daftar_saham
                WHERE kode = :ticker
            """)
            meta_row = conn.execute(q_d, {"ticker": clean_sym}).mappings().first()

        notasi = str(meta_row["notasi_khusus"] or "") if meta_row else ""
        tradeable = int(meta_row["tradeable_shares"] or 0) if meta_row else 0
        papan = str(meta_row["papan_pencatatan"] or "Utama") if meta_row else "Utama"

        if df_h.empty:
            empty_intel["emiten_info"] = {
                "notasi_khusus": notasi, "tradeable_shares": tradeable, "papan_pencatatan": papan
            }
            return empty_intel

        # Perhitungan Foreign Flow berbasis VWAP harian (Value / Volume) dengan fallback Close
        def _calc_vwap(row: Any) -> float:
            vol_r = float(row.get("volume") or 0)
            val_r = float(row.get("value") or 0)
            if vol_r > 0 and val_r > 0:
                return val_r / vol_r
            return float(row.get("close") or 0)

        df_h["vwap"] = df_h.apply(_calc_vwap, axis=1)
        today = df_h.iloc[0]
        today_vwap = float(today["vwap"] or today["close"] or 0)
        today_buy_s = int(today.get("foreign_buy") or 0)
        today_sell_s = int(today.get("foreign_sell") or 0)
        today_net_s = int(today.get("foreign_net") or 0)
        today_net_val = float(today_net_s * today_vwap)

        df_5d = df_h.head(5)
        net_5d_s = int(df_5d["foreign_net"].sum())
        val_5d = float((df_5d["foreign_net"] * df_5d["vwap"].astype(float)).sum())

        net_20d_s = int(df_h["foreign_net"].sum())
        val_20d = float((df_h["foreign_net"] * df_h["vwap"].astype(float)).sum())

        foreign_intel = {
            "today_net_shares": today_net_s,
            "today_net_lots": int(round(today_net_s / 100.0)),
            "today_net_val": round(today_net_val, 2),
            "today_buy_shares": today_buy_s,
            "today_buy_lots": int(round(today_buy_s / 100.0)),
            "today_sell_shares": today_sell_s,
            "today_sell_lots": int(round(today_sell_s / 100.0)),
            "flow_5d_shares": net_5d_s,
            "flow_5d_lots": int(round(net_5d_s / 100.0)),
            "flow_5d_val": round(val_5d, 2),
            "flow_20d_shares": net_20d_s,
            "flow_20d_lots": int(round(net_20d_s / 100.0)),
            "flow_20d_val": round(val_20d, 2),
            "status_1d": "ACCUM" if today_net_s > 0 else ("DISTRIB" if today_net_s < 0 else "NEUTRAL"),
            "status_5d": "ACCUM" if net_5d_s > 0 else ("DISTRIB" if net_5d_s < 0 else "NEUTRAL"),
            "status_20d": "ACCUM" if net_20d_s > 0 else ("DISTRIB" if net_20d_s < 0 else "NEUTRAL")
        }

        # Perhitungan Trade Size (Whale vs Ritel)
        freq_today = int(today.get("frequency") or 0)
        vol_today = int(today.get("volume") or 0)
        lot_today = vol_today / 100.0
        today_lpt = round(lot_today / freq_today, 1) if freq_today > 0 else 0.0

        valid_history = df_h[df_h["frequency"] > 0].copy()
        if not valid_history.empty:
            lpt_series = (valid_history["volume"] / 100.0) / valid_history["frequency"]
            avg_20d_lpt = round(float(lpt_series.mean()), 1)
        else:
            avg_20d_lpt = today_lpt

        whale_ratio = round(today_lpt / avg_20d_lpt, 2) if avg_20d_lpt > 0 else 1.0
        if whale_ratio >= 1.5:
            whale_label = "Dominasi Whale (Smart Money)"
        elif whale_ratio <= 0.75 and freq_today >= 50:
            whale_label = "Aktivitas Ritel (Retail Active)"
        else:
            whale_label = "Normal"

        trade_size_intel = {
            "today_lot_per_trade": today_lpt,
            "avg_lot_per_trade_20d": avg_20d_lpt,
            "whale_ratio": whale_ratio,
            "whale_label": whale_label,
            "frequency": freq_today
        }

        # Perhitungan Pasar Nego (Crossing Saham)
        nego_vol_s = int(today.get("non_regular_volume") or 0)
        nego_val = float(today.get("non_regular_value") or 0.0)
        nego_lots = int(round(nego_vol_s / 100.0))

        has_crossing = False
        crossing_reason = ""
        if nego_val >= 10_000_000_000:
            has_crossing = True
            crossing_reason = f"Transaksi Nego Besar Rp {nego_val / 1e9:.1f} Miliar"
        elif tradeable > 0 and nego_vol_s >= (0.01 * tradeable):
            has_crossing = True
            crossing_reason = f"Volume Nego {nego_lots:,} Lot (>= 1% Saham Beredar)"

        nego_intel = {
            "volume_shares": nego_vol_s,
            "volume_lots": nego_lots,
            "value": round(nego_val, 2),
            "has_crossing": has_crossing,
            "crossing_reason": crossing_reason
        }

        result = {
            "success": True,
            "symbol": clean_sym,
            "date": str(today["tanggal"]),
            "foreign_flow": foreign_intel,
            "trade_size": trade_size_intel,
            "pasar_nego": nego_intel,
            "emiten_info": {
                "notasi_khusus": notasi,
                "tradeable_shares": tradeable,
                "papan_pencatatan": papan
            }
        }

        with _INTELLIGENCE_LOCK:
            _evict_oldest_entries(_INTELLIGENCE_CACHE)
            _INTELLIGENCE_CACHE[clean_sym] = (now, result)

        return result
    except Exception as e:
        logger.error(f"Error calculating market intelligence for {clean_sym}: {e}", exc_info=True)
        return empty_intel


def get_raw_broker_df(clean_sym: str) -> Optional[pd.DataFrame]:
    """
    Ambil atau cache DataFrame raw broker_summary untuk suatu ticker.
    Menghindari re-query berulang ke Neon DB saat user menggonta-ganti rentang tanggal.
    """
    now = time.time()
    ttl = get_bandar_ttl()
    with _RAW_DF_LOCK:
        if clean_sym in _RAW_DF_CACHE:
            ts, df = _RAW_DF_CACHE[clean_sym]
            if now - ts < ttl:
                return df

    engine = get_db_engine()
    if not engine:
        return None

    try:
        cutoff_date = (now_wib().date() - timedelta(days=240)).strftime("%Y-%m-%d")
        sql = text("""
            SELECT date, broker_code, net_vol, net_val, buy_vol, buy_val, sell_vol, sell_val
            FROM broker_summary
            WHERE ticker = :ticker AND date >= :cutoff_date
            ORDER BY date ASC
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"ticker": clean_sym, "cutoff_date": cutoff_date})
            if df.empty:
                sql_fallback = text("""
                    SELECT date, broker_code, net_vol, net_val, buy_vol, buy_val, sell_vol, sell_val
                    FROM broker_summary
                    WHERE ticker = :ticker
                    ORDER BY date ASC
                """)
                df = pd.read_sql(sql_fallback, conn, params={"ticker": clean_sym})

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            for col in ['buy_vol', 'buy_val', 'sell_vol', 'sell_val']:
                if col not in df.columns:
                    df[col] = 0

        with _RAW_DF_LOCK:
            _evict_oldest_entries(_RAW_DF_CACHE)
            _RAW_DF_CACHE[clean_sym] = (now, df)
        return df
    except Exception as e:
        logger.error(f"Error querying broker_summary for {clean_sym}: {e}")
        return None

def get_bandarmologi(symbol: str, days_lookback: int = 180) -> Dict[str, Any]:
    """
    Hitung seri data Bandarmologi (HMB & Net Flow) untuk suatu saham.
    Menggunakan single-pass in-memory processing agar super cepat.
    Default 180 hari (6 bulan) sesuai retention plan di Neon DB.
    """
    clean_sym = clean_symbol(symbol)
    cache_key = f"bandar_{clean_sym}_{days_lookback}"
    now = time.time()
    ttl = get_bandar_ttl()

    # 1. Cek Cache
    with _BANDAR_CACHE_LOCK:
        if cache_key in _BANDAR_CACHE:
            cached_time, cached_data = _BANDAR_CACHE[cache_key]
            if now - cached_time < ttl:
                return cached_data

    df = get_raw_broker_df(clean_sym)
    if df is None or df.empty:
        empty_res = {
            "success": True,
            "symbol": clean_sym,
            "count": 0,
            "available_range": None,
            "summary": None,
            "data": []
        }
        with _BANDAR_CACHE_LOCK:
            _BANDAR_CACHE[cache_key] = (now, empty_res)
        return empty_res

    try:
        all_dates = sorted(df['date'].unique())
        if not all_dates:
            return empty_res

        # Filter days_lookback jika ditentukan (default 180 hari)
        if days_lookback and days_lookback > 0:
            cutoff_dt = pd.to_datetime(now_wib().date()) - pd.Timedelta(days=days_lookback)
            target_dates = [d for d in all_dates if pd.to_datetime(d) >= cutoff_dt]
            if not target_dates:
                target_dates = all_dates[-days_lookback:] if len(all_dates) >= days_lookback else all_dates
        else:
            target_dates = all_dates

        series: List[Dict[str, Any]] = []

        for d in target_dates:
            d_dt = pd.to_datetime(d)
            # Timestamp UTC+7 00:00:00 WIB dalam epoch milliseconds
            epoch_ms = int(datetime.combine(d_dt.date(), datetime.min.time(), tzinfo=WIB_TZ).timestamp() * 1000)

            # Transaksi hari d
            df_d = df[df['date'] == d]
            
            # Top 3 Net Buy vs Top 3 Net Sell hari d
            buyers = df_d[df_d['net_val'] > 0].nlargest(3, 'net_val')
            sellers = df_d[df_d['net_val'] < 0].nsmallest(3, 'net_val') # negatif terkecil
            
            top3_buy = float(buyers['net_val'].sum())
            top3_sell = float(sellers['net_val'].sum())
            net_flow = round(top3_buy + top3_sell) # Jika buy > sell bernilai positif (akumulasi)
            
            # Rolling 20 hari bursa s.d hari d untuk HMB (Harga Modal Akumulator)
            d_idx = all_dates.index(d)
            window_dates = all_dates[max(0, d_idx - 19):d_idx + 1]
            df_window = df[df['date'].isin(window_dates)]
            
            acc_window = df_window.groupby('broker_code').agg({
                'net_vol': 'sum',
                'buy_vol': 'sum',
                'buy_val': 'sum'
            })
            top_acc = acc_window[acc_window['net_vol'] > 0].nlargest(5, 'net_vol')
            
            # Net-Inventory Weighted HMB: Bobot berdasarkan sisa barang riil (net_vol)
            valid_acc = top_acc[top_acc['buy_vol'] > 0]
            if not valid_acc.empty:
                avg_buy_prices = valid_acc['buy_val'] / (valid_acc['buy_vol'] * 100.0)
                weighted_cost = (valid_acc['net_vol'] * avg_buy_prices).sum()
                total_net_vol = valid_acc['net_vol'].sum()
                hmb = round(float(weighted_cost / total_net_vol)) if total_net_vol > 0 else 0
            else:
                hmb = 0

            series.append({
                "date": d_dt.strftime("%Y-%m-%d"),
                "timestamp": epoch_ms,
                "hmb": hmb,
                "net_flow": net_flow,
                "top3_buy": top3_buy,
                "top3_sell": top3_sell,
                "status": "ACCUM" if net_flow > 0 else "DISTRIB"
            })

        # Ambil breakdown broker hari terakhir untuk summary default (Top 8 Pembeli vs Top 8 Penjual)
        latest_d = all_dates[-1]
        df_latest = df[df['date'] == latest_d]
        latest_buyers = df_latest[df_latest['net_val'] > 0].nlargest(8, 'net_val')
        latest_sellers = df_latest[df_latest['net_val'] < 0].nsmallest(8, 'net_val')

        total_buy_val = float(df_latest[df_latest['net_val'] > 0]['net_val'].sum())
        total_sell_val = abs(float(df_latest[df_latest['net_val'] < 0]['net_val'].sum()))

        top_buyers_list = []
        for _, r in latest_buyers.iterrows():
            vol = int(r.net_vol)
            val = float(r.net_val)
            buy_vol = int(r['buy_vol']) if 'buy_vol' in r and pd.notna(r['buy_vol']) else 0
            buy_val = float(r['buy_val']) if 'buy_val' in r and pd.notna(r['buy_val']) else 0.0
            avg_p = round(buy_val / (buy_vol * 100)) if buy_vol > 0 else (round(val / (vol * 100)) if vol > 0 else 0)
            top_buyers_list.append({
                "broker": str(r.broker_code),
                "net_vol": vol,
                "net_val": val,
                "avg_price": avg_p
            })

        top_sellers_list = []
        for _, r in latest_sellers.iterrows():
            vol = abs(int(r.net_vol))
            val = abs(float(r.net_val))
            sell_vol = int(r['sell_vol']) if 'sell_vol' in r and pd.notna(r['sell_vol']) else 0
            sell_val = float(r['sell_val']) if 'sell_val' in r and pd.notna(r['sell_val']) else 0.0
            avg_p = round(sell_val / (sell_vol * 100)) if sell_vol > 0 else (round(val / (vol * 100)) if vol > 0 else 0)
            top_sellers_list.append({
                "broker": str(r.broker_code),
                "net_vol": vol,
                "net_val": val,
                "avg_price": avg_p
            })

        latest_item = series[-1] if series else None
        intel = get_stock_market_intelligence(clean_sym)

        summary = {
            "latest_date": latest_item["date"] if latest_item else None,
            "latest_hmb": latest_item["hmb"] if latest_item else 0,
            "latest_net_flow": latest_item["net_flow"] if latest_item else 0,
            "latest_status": latest_item["status"] if latest_item else "NEUTRAL",
            "total_buy_val": total_buy_val,
            "total_sell_val": total_sell_val,
            "top_buyers": top_buyers_list,
            "top_sellers": top_sellers_list,
            "market_intelligence": intel,
            "foreign_flow": intel.get("foreign_flow", {}),
            "trade_size": intel.get("trade_size", {}),
            "pasar_nego": intel.get("pasar_nego", {}),
            "notasi_khusus": intel.get("emiten_info", {}).get("notasi_khusus", "")
        }

        available_range = {
            "min_date": pd.to_datetime(all_dates[0]).strftime("%Y-%m-%d"),
            "max_date": pd.to_datetime(all_dates[-1]).strftime("%Y-%m-%d"),
            "total_dates": len(all_dates)
        }

        result = {
            "success": True,
            "symbol": clean_sym,
            "source": "neon_db",
            "count": len(series),
            "available_range": available_range,
            "summary": summary,
            "market_intelligence": intel,
            "data": series
        }

        # Simpan Cache
        with _BANDAR_CACHE_LOCK:
            _evict_oldest_entries(_BANDAR_CACHE)
            _BANDAR_CACHE[cache_key] = (now, result)

        return result

    except Exception as e:
        logger.error(f"Error calculating bandarmologi for {clean_sym}: {e}")
        return {
            "success": False,
            "error": str(e),
            "symbol": clean_sym,
            "data": []
        }

def get_broksum_range(symbol: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Hitung agregasi Broker Summary untuk rentang tanggal tertentu (custom range).
    Mendukung filter dinamis (1D, 1W, 2W, 1M, 3M, 6M, atau tanggal custom).
    Super cepat karena menghitung langsung dari DataFrame in-memory (0 DB overhead).
    """
    clean_sym = clean_symbol(symbol)
    df = get_raw_broker_df(clean_sym)
    
    if df is None or df.empty:
        return {
            "success": False,
            "symbol": clean_sym,
            "error": "Data broker summary tidak ditemukan",
            "summary": None
        }

    all_dates = sorted(df['date'].unique())
    min_date_str = pd.to_datetime(all_dates[0]).strftime("%Y-%m-%d")
    max_date_str = pd.to_datetime(all_dates[-1]).strftime("%Y-%m-%d")

    # Parsing to_date
    if to_date:
        try:
            end_dt = pd.to_datetime(to_date)
        except Exception:
            end_dt = all_dates[-1]
    else:
        end_dt = all_dates[-1]

    # Parsing from_date
    if from_date:
        try:
            start_dt = pd.to_datetime(from_date)
        except Exception:
            start_dt = end_dt
    else:
        start_dt = end_dt

    # Pastikan start_dt <= end_dt
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    # Filter rentang tanggal (inklusif)
    df_filtered = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]

    if df_filtered.empty:
        df_filtered = df[df['date'] == all_dates[-1]]
        start_dt = all_dates[-1]
        end_dt = all_dates[-1]

    trading_days = int(df_filtered['date'].nunique())

    # Agregasi per broker dalam rentang tanggal
    acc = df_filtered.groupby('broker_code').agg({
        'net_vol': 'sum',
        'net_val': 'sum',
        'buy_vol': 'sum',
        'buy_val': 'sum',
        'sell_vol': 'sum',
        'sell_val': 'sum'
    }).reset_index()

    buyers = acc[acc['net_val'] > 0].nlargest(8, 'net_val')
    sellers = acc[acc['net_val'] < 0].nsmallest(8, 'net_val')

    total_buy_val = float(acc[acc['net_val'] > 0]['net_val'].sum())
    total_sell_val = abs(float(acc[acc['net_val'] < 0]['net_val'].sum()))

    top_buyers = []
    for _, r in buyers.iterrows():
        vol = int(r.net_vol)
        val = float(r.net_val)
        buy_vol = int(r['buy_vol']) if 'buy_vol' in r and pd.notna(r['buy_vol']) else 0
        buy_val = float(r['buy_val']) if 'buy_val' in r and pd.notna(r['buy_val']) else 0.0
        avg_p = round(buy_val / (buy_vol * 100)) if buy_vol > 0 else (round(val / (vol * 100)) if vol > 0 else 0)
        top_buyers.append({
            "broker": str(r.broker_code),
            "net_vol": vol,
            "net_val": val,
            "avg_price": avg_p
        })

    top_sellers = []
    for _, r in sellers.iterrows():
        vol = abs(int(r.net_vol))
        val = abs(float(r.net_val))
        sell_vol = int(r['sell_vol']) if 'sell_vol' in r and pd.notna(r['sell_vol']) else 0
        sell_val = float(r['sell_val']) if 'sell_val' in r and pd.notna(r['sell_val']) else 0.0
        avg_p = round(sell_val / (sell_vol * 100)) if sell_vol > 0 else (round(val / (vol * 100)) if vol > 0 else 0)
        top_sellers.append({
            "broker": str(r.broker_code),
            "net_vol": vol,
            "net_val": val,
            "avg_price": avg_p
        })

    # Net Flow Top 3 pada rentang waktu terpilih
    top3_buy = float(buyers.nlargest(3, 'net_val')['net_val'].sum()) if not buyers.empty else 0.0
    top3_sell = float(sellers.nsmallest(3, 'net_val')['net_val'].sum()) if not sellers.empty else 0.0
    net_flow = round(top3_buy + top3_sell)

    # Modal bandar akumulator pada rentang waktu terpilih (Net-Inventory Weighted)
    top_acc = acc[acc['net_vol'] > 0].nlargest(5, 'net_vol')
    valid_acc = top_acc[top_acc['buy_vol'] > 0]
    if not valid_acc.empty:
        avg_buy_prices = valid_acc['buy_val'] / (valid_acc['buy_vol'] * 100.0)
        weighted_cost = (valid_acc['net_vol'] * avg_buy_prices).sum()
        total_net_vol = valid_acc['net_vol'].sum()
        hmb = round(float(weighted_cost / total_net_vol)) if total_net_vol > 0 else 0
    else:
        hmb = 0

    # Herfindahl-Hirschman Index (HHI) & Accumulation Asymmetry Ratio (AAR)
    pos_buyers = acc[acc['net_val'] > 0]
    neg_sellers = acc[acc['net_val'] < 0]
    tot_pos_buy = float(pos_buyers['net_val'].sum())
    tot_neg_sell = abs(float(neg_sellers['net_val'].sum()))

    hhi_buy = float(((pos_buyers['net_val'] / tot_pos_buy) ** 2).sum()) if tot_pos_buy > 0 else 0.0
    hhi_sell = float(((neg_sellers['net_val'].abs() / tot_neg_sell) ** 2).sum()) if tot_neg_sell > 0 else 0.0
    aar = round(float(hhi_buy / hhi_sell), 2) if hhi_sell > 0 else (2.0 if hhi_buy > 0 else 1.0)

    intel = get_stock_market_intelligence(clean_sym)
    range_foreign = dict(intel.get("foreign_flow", {}))

    # Jika rentang waktu lebih dari 1 hari atau tanggal custom, hitung agregasi foreign flow rentang waktu tersebut
    if start_dt != end_dt:
        try:
            engine = get_db_engine()
            if engine:
                with engine.connect() as conn:
                    q_rf = text("""
                        SELECT SUM(foreign_net) as net_shares,
                               SUM(foreign_net * CASE WHEN volume > 0 AND COALESCE(value, 0) > 0 THEN (value / volume) ELSE close END) as net_val,
                               SUM(foreign_buy) as buy_shares,
                               SUM(foreign_sell) as sell_shares,
                               SUM(non_regular_volume) as nego_vol,
                               SUM(non_regular_value) as nego_val
                        FROM harga_saham
                        WHERE ticker = :ticker AND tanggal >= :start_d AND tanggal <= :end_d
                    """)
                    r_row = conn.execute(q_rf, {
                        "ticker": clean_sym,
                        "start_d": pd.to_datetime(start_dt).date(),
                        "end_d": pd.to_datetime(end_dt).date()
                    }).mappings().first()
                    if r_row and r_row["net_shares"] is not None:
                        net_s = int(r_row["net_shares"] or 0)
                        range_foreign["range_net_shares"] = net_s
                        range_foreign["range_net_lots"] = int(round(net_s / 100.0))
                        range_foreign["range_net_val"] = float(r_row["net_val"] or 0.0)
                        range_foreign["range_buy_shares"] = int(r_row["buy_shares"] or 0)
                        range_foreign["range_sell_shares"] = int(r_row["sell_shares"] or 0)
                        range_foreign["range_status"] = "ACCUM" if net_s > 0 else ("DISTRIB" if net_s < 0 else "NEUTRAL")
        except Exception as e:
            logger.warning(f"Error calculating range foreign flow for {clean_sym}: {e}")

    summary_dict = {
        "latest_date": pd.to_datetime(end_dt).strftime("%Y-%m-%d"),
        "latest_hmb": hmb,
        "latest_net_flow": net_flow,
        "latest_status": "ACCUM" if net_flow > 0 else "DISTRIB",
        "aar": aar,
        "hhi_buy": round(hhi_buy, 4),
        "hhi_sell": round(hhi_sell, 4),
        "total_buy_val": total_buy_val,
        "total_sell_val": total_sell_val,
        "top_buyers": top_buyers,
        "top_sellers": top_sellers,
        "market_intelligence": intel,
        "foreign_flow": range_foreign,
        "trade_size": intel.get("trade_size", {}),
        "pasar_nego": intel.get("pasar_nego", {}),
        "notasi_khusus": intel.get("emiten_info", {}).get("notasi_khusus", "")
    }

    return {
        "success": True,
        "symbol": clean_sym,
        "from_date": pd.to_datetime(start_dt).strftime("%Y-%m-%d"),
        "to_date": pd.to_datetime(end_dt).strftime("%Y-%m-%d"),
        "trading_days": trading_days,
        "available_range": {
            "min_date": min_date_str,
            "max_date": max_date_str,
            "total_dates": len(all_dates)
        },
        "summary": summary_dict,
        "market_intelligence": intel
    }


def get_historical_price_table(symbol: str, timeframe: str = "daily", limit: int = 60) -> Dict[str, Any]:
    """
    Mengambil tabel data historis harga saham & turnover (Gambar 3 Stockbit):
    Date | Close | Change | Value (Turnover)
    Mendukung timeframe: 'daily', 'weekly', 'monthly'.
    """
    clean_sym = clean_symbol(symbol)
    engine = get_db_engine()
    if not engine:
        return {"success": False, "symbol": clean_sym, "data": []}

    try:
        with engine.connect() as conn:
            # 1. Ambil riwayat harga harian beserta nilai transaksi resmi BEI (value)
            q_price = text("""
                SELECT tanggal as date, open, high, low, close, volume, COALESCE(value, 0) as official_value
                FROM harga_saham
                WHERE ticker = :ticker
                ORDER BY tanggal DESC
                LIMIT 300
            """)
            df_price = pd.read_sql(q_price, conn, params={"ticker": clean_sym})

            # 2. Ambil turnover harian dari broker_summary sebagai fallback jika official_value = 0
            q_turnover = text("""
                SELECT date, SUM(buy_val) as brok_turnover
                FROM broker_summary
                WHERE ticker = :ticker
                GROUP BY date
            """)
            df_turnover = pd.read_sql(q_turnover, conn, params={"ticker": clean_sym})

        if df_price.empty:
            return {"success": True, "symbol": clean_sym, "timeframe": timeframe, "data": []}

        df_price['date'] = pd.to_datetime(df_price['date'])
        if not df_turnover.empty:
            df_turnover['date'] = pd.to_datetime(df_turnover['date'])
            merged = pd.merge(df_price, df_turnover, on='date', how='left')
        else:
            merged = df_price.copy()
            merged['brok_turnover'] = 0.0

        # Prioritas Turnover: 1. Official IDX Value (>0) -> 2. Broksum buy_val (>0) -> 3. close * volume (shares)
        def _resolve_turnover(row: Any) -> float:
            off_v = float(row.get('official_value') or 0.0)
            if off_v > 0:
                return off_v
            brok_v = float(row.get('brok_turnover') or 0.0)
            if brok_v > 0:
                return brok_v
            return float(row.get('close') or 0.0) * float(row.get('volume') or 0.0)

        merged['turnover'] = merged.apply(_resolve_turnover, axis=1)
        merged = merged.sort_values('date', ascending=True)

        tf = (timeframe or "daily").lower().strip()
        if tf == "weekly":
            merged['period'] = merged['date'].dt.to_period('W-FRI')
            resampled = merged.groupby('period').agg({
                'date': 'last',
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'turnover': 'sum'
            }).reset_index(drop=True)
            df_final = resampled
        elif tf == "monthly":
            merged['period'] = merged['date'].dt.to_period('M')
            resampled = merged.groupby('period').agg({
                'date': 'last',
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'turnover': 'sum'
            }).reset_index(drop=True)
            df_final = resampled
        else:
            df_final = merged

        df_final['prev_close'] = df_final['close'].shift(1)
        df_final['change'] = df_final['close'] - df_final['prev_close']
        df_final['change_pct'] = ((df_final['change'] / df_final['prev_close']) * 100.0).fillna(0.0)

        # Urutkan dari yang paling baru ke lama
        df_final = df_final.sort_values('date', ascending=False).head(limit)

        records = []
        for _, r in df_final.iterrows():
            d_obj = pd.to_datetime(r['date'])
            d_display = d_obj.strftime("%d %b %y")
            val = float(r['turnover'] or 0.0)

            if val >= 1e12:
                val_str = f"{val / 1e12:.2f} B"
            elif val >= 1e9:
                val_str = f"{val / 1e9:.2f} B"
            elif val >= 1e6:
                val_str = f"{val / 1e6:.2f} M"
            else:
                val_str = f"{val:,.0f}"

            chg = float(r['change'] if pd.notna(r['change']) else 0.0)
            chg_pct = float(r['change_pct'] if pd.notna(r['change_pct']) else 0.0)
            sign = '+' if chg > 0 else ''

            records.append({
                "date": d_obj.strftime("%Y-%m-%d"),
                "date_display": d_display,
                "close": int(round(r['close'])) if r['close'] >= 1 else round(r['close'], 2),
                "change": chg,
                "change_pct": round(chg_pct, 2),
                "change_display": f"{sign}{int(chg) if abs(chg) >= 1 else chg} ({sign}{chg_pct:.2f}%)",
                "value": val,
                "value_display": val_str,
                "volume": int(r['volume'] or 0)
            })

        return {
            "success": True,
            "symbol": clean_sym,
            "timeframe": tf,
            "count": len(records),
            "data": records
        }
    except Exception as e:
        logger.error(f"Error fetching historical price table for {clean_sym}: {e}")
        return {"success": False, "symbol": clean_sym, "error": str(e), "data": []}


def get_broker_daily_activity(symbol: str, broker_code: str, month_str: Optional[str] = None) -> Dict[str, Any]:
    """
    Mengambil kalender aktivitas harian untuk satu broker tertentu (Gambar 2 Stockbit):
    Menampilkan transaksi harian (Net Val, Net Vol, Avg Price, status BUY/SELL).
    """
    clean_sym = clean_symbol(symbol)
    clean_brk = (broker_code or "XL").strip().upper()
    df = get_raw_broker_df(clean_sym)

    if df is None or df.empty:
        return {
            "success": True,
            "symbol": clean_sym,
            "broker": clean_brk,
            "broker_code": clean_brk,
            "month": month_str or now_wib().strftime("%Y-%m"),
            "available_months": [],
            "available_brokers": [],
            "trading_days": 0,
            "accum_days": 0,
            "monthly_net_val": 0.0,
            "monthly_net_vol": 0,
            "daily_activity": [],
            "days": {},
            "summary": {"total_net_val": 0, "total_net_vol": 0, "buy_days": 0, "sell_days": 0}
        }

    # Available months & brokers
    df['month'] = df['date'].dt.strftime("%Y-%m")
    available_months = sorted(df['month'].unique().tolist(), reverse=True)
    target_month = month_str if (month_str and month_str in available_months) else (available_months[0] if available_months else now_wib().strftime("%Y-%m"))
    
    # Ambil HANYA broker yang memiliki transaksi nyata di bulan target_month ini
    df_m = df[df['month'] == target_month]
    broker_stats = {}
    if not df_m.empty:
        active_mask = (df_m['buy_vol'] > 0) | (df_m['sell_vol'] > 0) | (df_m['net_vol'] != 0) | (df_m['net_val'] != 0)
        df_active_month = df_m[active_mask]
        if not df_active_month.empty:
            accum_days_series = (df_active_month['net_val'] > 0).groupby(df_active_month['broker_code']).sum()
            net_val_series = df_active_month['net_val'].groupby(df_active_month['broker_code']).sum()
            turnover_series = (df_active_month['buy_val'].fillna(0) + df_active_month['sell_val'].fillna(0)).groupby(df_active_month['broker_code']).sum()

            stats_df = pd.DataFrame({
                'accum_days': accum_days_series,
                'total_net_val': net_val_series,
                'total_turnover': turnover_series
            })
            # Urutkan: broker paling sering akumulasi (accum_days terbanyak, lalu total_net_val terbesar di paling kiri)
            sorted_stats = stats_df.sort_values(by=['accum_days', 'total_net_val'], ascending=[False, False])
            top_brks = sorted_stats.index.tolist()

            for brk_code, row in sorted_stats.iterrows():
                broker_stats[brk_code] = {
                    "accum_days": int(row['accum_days']),
                    "net_val": float(row['total_net_val']),
                    "is_buyer": bool(row['total_net_val'] >= 0)
                }
        else:
            top_brks = df.groupby('broker_code')['buy_vol'].sum().sort_values(ascending=False).head(25).index.tolist()
    else:
        top_brks = df.groupby('broker_code')['buy_vol'].sum().sort_values(ascending=False).head(25).index.tolist()

    if clean_brk not in top_brks:
        if not df_m.empty and 'df_active_month' in locals() and clean_brk in df_active_month['broker_code'].values:
            top_brks.insert(0, clean_brk)
        elif top_brks:
            clean_brk = top_brks[0]
    
    df_filtered = df[(df['broker_code'] == clean_brk) & (df['month'] == target_month)].sort_values('date', ascending=True)

    days_data = {}
    tot_val = 0.0
    tot_vol = 0
    buy_days = 0
    sell_days = 0

    for _, r in df_filtered.iterrows():
        d_str = r['date'].strftime("%Y-%m-%d")
        net_v = int(r['net_vol'])
        net_val = float(r['net_val'])
        buy_vol = int(r['buy_vol']) if 'buy_vol' in r else 0
        buy_val = float(r['buy_val']) if 'buy_val' in r else 0.0
        sell_vol = int(r['sell_vol']) if 'sell_vol' in r else 0
        sell_val = float(r['sell_val']) if 'sell_val' in r else 0.0

        if net_val >= 0:
            avg_p = round(buy_val / (buy_vol * 100)) if buy_vol > 0 else (round(net_val / (net_v * 100)) if net_v > 0 else 0)
            status_act = "BUY"
            if net_val > 0:
                buy_days += 1
        else:
            avg_p = round(sell_val / (sell_vol * 100)) if sell_vol > 0 else (round(abs(net_val) / (abs(net_v) * 100)) if net_v < 0 else 0)
            status_act = "SELL"
            sell_days += 1

        val_abs = abs(net_val)
        if val_abs >= 1e9:
            val_disp = f"{val_abs / 1e9:.1f}B"
        elif val_abs >= 1e6:
            val_disp = f"{val_abs / 1e6:.1f}M"
        elif val_abs >= 1e3:
            val_disp = f"{val_abs / 1e3:.0f}K"
        else:
            val_disp = f"{val_abs:.0f}"

        vol_abs = abs(net_v)
        if vol_abs >= 1000:
            vol_disp = f"{vol_abs / 1000:.1f}K Lot"
        else:
            vol_disp = f"{vol_abs} Lot"

        days_data[d_str] = {
            "date": d_str,
            "day": r['date'].day,
            "net_vol": net_v,
            "net_vol_display": vol_disp,
            "net_val": net_val,
            "net_val_display": val_disp,
            "avg_price": avg_p,
            "status": status_act,
            "buy_vol": buy_vol,
            "sell_vol": sell_vol
        }
        tot_val += net_val
        tot_vol += net_v

    return {
        "success": True,
        "symbol": clean_sym,
        "broker": clean_brk,
        "broker_code": clean_brk,
        "month": target_month,
        "available_months": available_months,
        "available_brokers": top_brks,
        "broker_stats": broker_stats,
        "trading_days": len(days_data),
        "accum_days": buy_days,
        "monthly_net_val": tot_val,
        "monthly_net_vol": tot_vol,
        "daily_activity": list(days_data.values()),
        "summary": {
            "total_net_val": tot_val,
            "total_net_vol": tot_vol,
            "buy_days": buy_days,
            "sell_days": sell_days
        },
        "days": days_data
    }


def get_broker_flow(symbol: str, days: int = 30, metric: str = "val", broker_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Mengambil data garis visualisasi akumulasi/distribusi kumulatif per broker (Gambar 1 Stockbit):
    Nilai kumulatif per tanggal untuk Top Accumulators & Top Distributors (atau broker terpilih).
    """
    clean_sym = clean_symbol(symbol)
    df = get_raw_broker_df(clean_sym)

    if df is None or df.empty:
        return {
            "success": True,
            "symbol": clean_sym,
            "dates": [],
            "series": {},
            "series_list": [],
            "top_brokers": [],
            "top_buyers": [],
            "top_sellers": [],
            "summary": {"net_flow": 0, "total_buy": 0, "total_sell": 0, "status": "NEUTRAL"},
            "meter": {"acc_pct": 50, "dist_pct": 50, "net_status": "NEUTRAL", "net_flow": 0}
        }

    all_dates = sorted(df['date'].unique())
    target_dates = all_dates[-days:] if len(all_dates) >= days else all_dates
    df_window = df[df['date'].isin(target_dates)].copy()

    val_col = 'net_val' if metric == 'val' else 'net_vol'
    piv = df_window.pivot_table(index='date', columns='broker_code', values=val_col, fill_value=0)
    cum_flow = piv.cumsum()

    # Hitung total akhir tiap broker untuk menentukan Top 5 Buyers & Top 5 Sellers
    latest_totals = cum_flow.iloc[-1]
    top_buyers = latest_totals[latest_totals > 0].nlargest(5).index.tolist()
    top_sellers = latest_totals[latest_totals < 0].nsmallest(5).index.tolist()

    if broker_list and len(broker_list) > 0:
        selected_brokers = [b.upper() for b in broker_list if b.upper() in cum_flow.columns]
    else:
        # Default: Top 3 Buyers & Top 3 Sellers
        selected_brokers = (top_buyers[:3] + top_sellers[:3])

    # Warna khas untuk garis broker (Stockbit style)
    PALETTE = [
        "#a855f7", # CC - Purple
        "#ec4899", # YU - Pink
        "#eab308", # SQ - Yellow
        "#f97316", # MG - Orange
        "#22c55e", # XL - Green
        "#06b6d4", # NI - Cyan
        "#3b82f6", # PD - Blue
        "#ef4444", # YP - Red
        "#14b8a6", # CS - Teal
        "#f43f5e"  # BK - Rose
    ]

    dates_str = [pd.to_datetime(d).strftime("%Y-%m-%d") for d in cum_flow.index]
    series = []
    for i, brk in enumerate(selected_brokers):
        if brk not in cum_flow.columns:
            continue
        vals = [round(float(v), 2) for v in cum_flow[brk].values]
        final_val = vals[-1] if vals else 0
        series.append({
            "broker": brk,
            "color": PALETTE[i % len(PALETTE)],
            "data": vals,
            "final_val": final_val,
            "is_buyer": final_val >= 0
        })

    # Meter Net Distribution vs Net Accumulation
    tot_pos = float(latest_totals[latest_totals > 0].sum())
    tot_neg = abs(float(latest_totals[latest_totals < 0].sum()))
    total_flow = tot_pos + tot_neg
    acc_pct = round((tot_pos / total_flow) * 100, 1) if total_flow > 0 else 50.0
    dist_pct = round((tot_neg / total_flow) * 100, 1) if total_flow > 0 else 50.0

    top_brokers = list(dict.fromkeys(top_buyers + top_sellers))
    series_dict = {s["broker"]: s["data"] for s in series}

    summary_flow = {
        "net_flow": round(tot_pos - tot_neg),
        "total_buy": tot_pos,
        "total_sell": tot_neg,
        "status": "ACCUM" if tot_pos > tot_neg else "DISTRIB"
    }

    return {
        "success": True,
        "symbol": clean_sym,
        "metric": metric,
        "days": len(target_dates),
        "dates": dates_str,
        "series": series_dict,
        "series_list": series,
        "top_brokers": top_brokers,
        "available_brokers": sorted(df['broker_code'].unique().tolist()),
        "top_buyers": top_buyers,
        "top_sellers": top_sellers,
        "summary": summary_flow,
        "meter": {
            "acc_pct": acc_pct,
            "dist_pct": dist_pct,
            "net_flow": round(tot_pos - tot_neg),
            "status": "ACCUM" if tot_pos > tot_neg else "DISTRIB"
        }
    }

