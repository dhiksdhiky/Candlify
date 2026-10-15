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
        sql = text("""
            SELECT date, broker_code, net_vol, net_val, buy_vol, buy_val, sell_vol, sell_val
            FROM broker_summary
            WHERE ticker = :ticker
            ORDER BY date ASC
        """)
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn, params={"ticker": clean_sym})

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            for col in ['buy_vol', 'buy_val', 'sell_vol', 'sell_val']:
                if col not in df.columns:
                    df[col] = 0

        with _RAW_DF_LOCK:
            if len(_RAW_DF_CACHE) >= _CACHE_MAX_ENTRIES:
                _RAW_DF_CACHE.clear()
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
        summary = {
            "latest_date": latest_item["date"] if latest_item else None,
            "latest_hmb": latest_item["hmb"] if latest_item else 0,
            "latest_net_flow": latest_item["net_flow"] if latest_item else 0,
            "latest_status": latest_item["status"] if latest_item else "NEUTRAL",
            "total_buy_val": total_buy_val,
            "total_sell_val": total_sell_val,
            "top_buyers": top_buyers_list,
            "top_sellers": top_sellers_list
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
            "data": series
        }

        # Simpan Cache
        with _BANDAR_CACHE_LOCK:
            if len(_BANDAR_CACHE) >= _CACHE_MAX_ENTRIES:
                _BANDAR_CACHE.clear()
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
        "summary": {
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
            "top_sellers": top_sellers
        }
    }
