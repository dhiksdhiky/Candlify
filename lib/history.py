"""
v2/lib/history.py — Production-Grade Candlestick Data Engine
============================================================
P0 & P1 Hardened:
- Robust Input Validation & Sanitization (regex ^[A-Z0-9]{1,10}$)
- Thread-Safe DB Lazy Initializer
- Smart Dynamic TTL (Market-Hours Aware: Mon-Fri 08:45-16:30 WIB)
- HTTP Session with Exponential Backoff & 429 Retry Strategy
- Automatic Yahoo Mirror Fallback (query1 -> query2)
- Stale-Cache-on-Error Resilience (sajikan cache kadaluwarsa daripada crash)
- Strict Timezone Anchor (Asia/Jakarta WIB)
"""

import os
import re
import time
import logging
import threading
from datetime import datetime, date, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CandlifyHistoryV2")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Timezone & Market Hours Helper ────────────────────────────
WIB_TZ = timezone(timedelta(hours=7))  # Asia/Jakarta (UTC+7)

def now_wib() -> datetime:
    return datetime.now(WIB_TZ)

def is_idx_market_open() -> bool:
    """Cek apakah saat ini jam operasional Bursa Efek Indonesia (Mon-Fri 08:45 - 16:30 WIB)."""
    now = now_wib()
    # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
    if now.weekday() > 4:
        return False
    current_minute = now.hour * 60 + now.minute
    market_open = 8 * 60 + 45   # 08:45 WIB
    market_close = 16 * 60 + 30 # 16:30 WIB
    return market_open <= current_minute <= market_close

def get_smart_ttl(interval: str) -> int:
    """Hitung TTL dinamis: pendek saat jam bursa, panjang saat bursa tutup."""
    market_open = is_idx_market_open()
    
    if not market_open:
        # Saat bursa tutup / akhir pekan, candle tidak bergerak -> cache panjang (1-2 jam)
        return 3600
        
    # Saat jam bursa aktif:
    ttl_map = {
        "1m": 30,    # 30 detik untuk 1m (khusus BYOT Stockbit)
        "2m": 60,
        "5m": 120,   # 2 menit
        "15m": 300,  # 5 menit
        "30m": 300,
        "1h": 600,   # 10 menit
        "4h": 900,   # 15 menit
        "1d": 900,   # 15 menit
        "1wk": 1800, # 30 menit
        "1mo": 3600  # 1 jam
    }
    return ttl_map.get(interval.lower(), 300)

# ── HTTP Session with Retry & Backoff ────────────────────────
def create_resilient_session() -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1.0,  # 1s, 2s, 4s
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

_HTTP_SESSION = create_resilient_session()

# In-Memory Cache: { cache_key: (timestamp, data_dict) }
_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
_CACHE_MAX_ENTRIES = 256

# Database Thread-Safe Lazy Initialization
_db_engine = None
_db_lock = threading.Lock()

def get_db_engine():
    global _db_engine
    if _db_engine is not None:
        return _db_engine
        
    with _db_lock:
        if _db_engine is not None:
            return _db_engine
            
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return None
        
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        try:
            from sqlalchemy import create_engine
            _db_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"connect_timeout": 5}
            )
            return _db_engine
        except Exception as e:
            logger.warning(f"⚠️ Gagal menghubungkan ke Neon DB: {e}")
            return None

# ── Input Validation ──────────────────────────────────────────
SYMBOL_REGEX = re.compile(r'^[A-Z0-9]{1,10}$')

INTERVAL_MAP = {
    "1m": ("1m", "5d"),    # Opsional/khusus Stockbit BYOT
    "2m": ("2m", "1mo"),
    "5m": ("5m", "1mo"),
    "15m": ("15m", "1mo"),
    "30m": ("30m", "1mo"),
    "60m": ("1h", "3mo"),
    "1h": ("1h", "3mo"),
    "4h": ("4h", "6mo"),   # Intraday 4 Jam (Resampled dari 1h)
    "1d": ("1d", "1y"),
    "d": ("1d", "1y"),
    "1w": ("1wk", "5y"),
    "1wk": ("1wk", "5y"),
    "w": ("1wk", "5y"),
    "1mo": ("1mo", "max"),
    "m": ("1mo", "max")
}

VALID_RANGES = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

def clean_symbol(symbol: str) -> str:
    """Membersihkan dan memvalidasi ticker saham IDX."""
    if not symbol:
        raise ValueError("Kode simbol tidak boleh kosong.")
    cleaned = symbol.replace("IDX:", "").replace(".JK", "").upper().strip()
    if not SYMBOL_REGEX.match(cleaned):
        raise ValueError(f"Kode simbol '{cleaned}' tidak valid. Harus alfanumerik 1-10 karakter.")
    return cleaned

def resample_1h_to_4h(candles_1h: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Resample/aggregate 1H candles menjadi 4H candles untuk saham IDX.
    Karena jam bursa IDX (~5.5 jam/hari: 09:00 - 16:00 WIB),
    timeframe 4H standar menghasilkan 2 bar per hari bursa (TradingView aligned):
    - Sesi 1 (Pagi): 09:00 - 12:00/13:00 (jam < 13 WIB)
    - Sesi 2 (Siang/Sore): 13:00 - 16:15 (jam >= 13 WIB)
    """
    if not candles_1h:
        return []

    from collections import defaultdict
    grouped = defaultdict(list)
    for c in sorted(candles_1h, key=lambda x: x["timestamp"]):
        dt = datetime.fromtimestamp(c["timestamp"] / 1000, tz=WIB_TZ)
        bucket = 0 if dt.hour < 13 else 1
        key = (dt.date(), bucket)
        grouped[key].append(c)

    resampled = []
    for (d, b), bar_list in grouped.items():
        if not bar_list:
            continue
        resampled.append({
            "timestamp": bar_list[0]["timestamp"],
            "open": bar_list[0]["open"],
            "high": max(bar["high"] for bar in bar_list),
            "low": min(bar["low"] for bar in bar_list),
            "close": bar_list[-1]["close"],
            "volume": sum(bar.get("volume", 0) for bar in bar_list)
        })

    return resampled

# ── Fetch Implementations ────────────────────────────────────

def fetch_from_stockbit(symbol: str, token: str) -> Optional[Dict[str, Any]]:
    """Tarik 1m candlestick real-time dari endpoint Exodus Stockbit (BYOT)."""
    clean_sym = clean_symbol(symbol)
    url = f"https://exodus.stockbit.com/order-trade/running-trade/chart/{clean_sym}"
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    try:
        resp = _HTTP_SESSION.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            res_json = resp.json()
            data = res_json.get("data", {})
            price_charts = data.get("price_chart_data", [])
            
            candles = []
            for pt in price_charts:
                dt_str = f"{pt.get('date')} {pt.get('time', '09:00')}"
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M").replace(tzinfo=WIB_TZ)
                    ts = int(dt.timestamp() * 1000)
                except Exception:
                    ts = int(now_wib().timestamp() * 1000)
                    
                val_raw = pt.get("value", {})
                close_val = val_raw.get("raw") if isinstance(val_raw, dict) else pt.get("value")
                if close_val is None:
                    continue
                    
                open_val = pt.get("open") if pt.get("open") is not None else close_val
                high_val = pt.get("high") if pt.get("high") is not None else max(open_val, close_val)
                low_val = pt.get("low") if pt.get("low") is not None else min(open_val, close_val)
                
                candles.append({
                    "timestamp": ts,
                    "open": float(open_val),
                    "high": float(high_val),
                    "low": float(low_val),
                    "close": float(close_val),
                    "volume": float(pt.get("volume", 0) or 0)
                })
                
            if candles:
                return {
                    "success": True,
                    "symbol": clean_sym,
                    "interval": "1m",
                    "source": "stockbit_byot",
                    "count": len(candles),
                    "data": candles,
                    "meta": {
                        "regularMarketPrice": candles[-1]["close"],
                        "currency": "IDR",
                        "exchange": "IDX",
                        "timezone": "Asia/Jakarta"
                    },
                    "broker_chart_data": data.get("broker_chart_data", [])
                }
        else:
            logger.warning(f"Stockbit API returned HTTP {resp.status_code}")
    except Exception as e:
        logger.warning(f"Stockbit API error: {e}")
        
    return None

def fetch_from_neon_db(symbol: str) -> Optional[Dict[str, Any]]:
    """Tarik data daily historical (1D) dari database Neon PostgreSQL lokal."""
    engine = get_db_engine()
    if not engine:
        return None
        
    clean_sym = clean_symbol(symbol)
    query = """
        SELECT tanggal, open, high, low, close, volume 
        FROM harga_saham 
        WHERE ticker = :ticker 
        ORDER BY tanggal ASC
        LIMIT 1000
    """
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text(query), {"ticker": clean_sym}).fetchall()
            if not result:
                return None
                
            candles = []
            for row in result:
                tgl = row[0]
                # Pastikan timestamp ter-anchor ke midnight WIB (Asia/Jakarta)
                dt = datetime.combine(tgl, datetime.min.time()).replace(tzinfo=WIB_TZ)
                ts = int(dt.timestamp() * 1000)
                
                close_p = row[4]
                if close_p is None:
                    continue
                open_p = row[1] if row[1] is not None else close_p
                high_p = row[2] if row[2] is not None else max(open_p, close_p)
                low_p = row[3] if row[3] is not None else min(open_p, close_p)
                vol = row[5] or 0
                
                candles.append({
                    "timestamp": ts,
                    "open": float(open_p),
                    "high": float(high_p),
                    "low": float(low_p),
                    "close": float(close_p),
                    "volume": float(vol)
                })
                    
            if candles:
                prev_c = candles[-2]["close"] if len(candles) > 1 else candles[-1]["close"]
                last_c = candles[-1]["close"]
                change_pct = round(((last_c - prev_c) / prev_c) * 100, 2) if prev_c > 0 else 0.0

                return {
                    "success": True,
                    "symbol": clean_sym,
                    "interval": "1d",
                    "source": "neon_db",
                    "count": len(candles),
                    "data": candles,
                    "meta": {
                        "regularMarketPrice": last_c,
                        "regularMarketChangePercent": change_pct,
                        "currency": "IDR",
                        "exchange": "IDX",
                        "timezone": "Asia/Jakarta"
                    }
                }
    except Exception as e:
        logger.warning(f"⚠️ Neon DB fetch error: {e}")
        
    return None

def fetch_from_yahoo_finance(symbol: str, mapped_interval: str, selected_range: str) -> Dict[str, Any]:
    """Tarik data dari Yahoo Finance API dengan retry dan fallback mirror query2."""
    clean_sym = clean_symbol(symbol)
    yf_symbol = f"{clean_sym}.JK"
    
    hosts = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    last_error = None
    for host in hosts:
        url = f"https://{host}/v8/finance/chart/{yf_symbol}?range={selected_range}&interval={mapped_interval}"
        try:
            resp = _HTTP_SESSION.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                res_json = resp.json()
                chart_res = res_json.get("chart", {}).get("result")
                if chart_res:
                    result_data = chart_res[0]
                    meta = result_data.get("meta", {})
                    timestamps = result_data.get("timestamp", [])
                    indicators = result_data.get("indicators", {}).get("quote", [{}])[0]
                    
                    opens = indicators.get("open", [])
                    highs = indicators.get("high", [])
                    lows = indicators.get("low", [])
                    closes = indicators.get("close", [])
                    volumes = indicators.get("volume", [])
                    
                    candles = []
                    for i, ts in enumerate(timestamps):
                        c = closes[i] if i < len(closes) else None
                        if c is None:
                            continue
                            
                        o = opens[i] if i < len(opens) and opens[i] is not None else c
                        h = highs[i] if i < len(highs) and highs[i] is not None else max(o, c)
                        l = lows[i] if i < len(lows) and lows[i] is not None else min(o, c)
                        v = volumes[i] if i < len(volumes) and volumes[i] is not None else 0
                        
                        candles.append({
                            "timestamp": ts * 1000,
                            "open": round(float(o), 2),
                            "high": round(float(h), 2),
                            "low": round(float(l), 2),
                            "close": round(float(c), 2),
                            "volume": int(v)
                        })
                        
                    return {
                        "success": True,
                        "symbol": clean_sym,
                        "interval": mapped_interval,
                        "range": selected_range,
                        "source": "yahoo_finance",
                        "count": len(candles),
                        "data": candles,
                        "meta": {
                            "regularMarketPrice": meta.get("regularMarketPrice"),
                            "regularMarketChangePercent": meta.get("regularMarketChangePercent"),
                            "currency": meta.get("currency", "IDR"),
                            "exchange": meta.get("exchangeName", "JKT"),
                            "timezone": meta.get("exchangeTimezoneName", "Asia/Jakarta")
                        }
                    }
                else:
                    err_desc = res_json.get("chart", {}).get("error", {}).get("description", "No data")
                    last_error = f"Yahoo: {err_desc}"
            elif resp.status_code == 429:
                logger.warning(f"⚠️ Yahoo Finance 429 Rate Limit di {host}")
                last_error = "Rate limit (HTTP 429)"
            else:
                last_error = f"HTTP {resp.status_code} dari {host}"
        except Exception as e:
            last_error = str(e)
            
    return {
        "success": False,
        "error": last_error or "Gagal menarik data Yahoo Finance",
        "symbol": clean_sym,
        "data": []
    }

# ── Main Dispatcher with Stale-Cache Resilience ──────────────

def get_candlesticks(
    symbol: str, 
    interval: str = "1d", 
    range_val: Optional[str] = None, 
    stockbit_token: Optional[str] = None,
    source: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fungsi Utama Hybrid Candlestick Dispatcher.
    1. Validasi input ketat.
    2. Cek Stockbit BYOT jika token disertakan.
    3. Cek in-memory cache dengan TTL pintar.
    4. Jalur Neon DB jika 1D (kecuali dipaksa 'yahoo').
    5. Jalur Yahoo Finance (dengan retry & mirror fallback).
    6. Stale Cache Fallback jika upstream error/429.
    """
    clean_sym = clean_symbol(symbol)
    interval_norm = interval.lower().strip()
    
    if interval_norm not in INTERVAL_MAP:
        raise ValueError(f"Interval '{interval_norm}' tidak didukung. Pilihan: {list(INTERVAL_MAP.keys())}")
        
    mapped_interval, default_range = INTERVAL_MAP[interval_norm]
    selected_range = range_val if range_val and range_val in VALID_RANGES else default_range
    source_pref = (source or "default").lower().strip()
    
    # 1. Jalur Power-User: Stockbit BYOT
    if stockbit_token and interval_norm in ("1m", "intraday"):
        sb_res = fetch_from_stockbit(clean_sym, stockbit_token)
        if sb_res and sb_res.get("count", 0) > 0:
            return sb_res

    # 2. Cek In-Memory Cache
    cache_key = f"{clean_sym}_{mapped_interval}_{selected_range}_{source_pref}"
    now = time.time()
    ttl = get_smart_ttl(mapped_interval)
    
    with _CACHE_LOCK:
        if cache_key in _CACHE:
            cached_time, cached_data = _CACHE[cache_key]
            if now - cached_time < ttl:
                return cached_data

    # 3. Jalur Database Neon (Khusus 1D, lewati jika source='yahoo')
    if mapped_interval == "1d" and source_pref != "yahoo":
        db_res = fetch_from_neon_db(clean_sym)
        if db_res and db_res.get("count", 0) > 0:
            with _CACHE_LOCK:
                _prune_cache_if_needed()
                _CACHE[cache_key] = (now, db_res)
            return db_res

    # 4. Jalur Yahoo Finance (Intraday & Fallback)
    if mapped_interval == "4h":
        yf_res = fetch_from_yahoo_finance(clean_sym, "1h", selected_range)
        yf_res["interval"] = "4h"
        if yf_res.get("success") and yf_res.get("count", 0) > 0:
            resampled = resample_1h_to_4h(yf_res["data"])
            yf_res["count"] = len(resampled)
            yf_res["data"] = resampled
            with _CACHE_LOCK:
                _prune_cache_if_needed()
                _CACHE[cache_key] = (now, yf_res)
            return yf_res
    else:
        yf_res = fetch_from_yahoo_finance(clean_sym, mapped_interval, selected_range)
        if yf_res.get("success") and yf_res.get("count", 0) > 0:
            with _CACHE_LOCK:
                _prune_cache_if_needed()
                _CACHE[cache_key] = (now, yf_res)
            return yf_res

    # 5. Stale-Cache Resilience: Jika Yahoo gagal/429, sajikan cache kadaluwarsa daripada error
    with _CACHE_LOCK:
        if cache_key in _CACHE:
            _, stale_data = _CACHE[cache_key]
            logger.warning(f"⚠️ Menyajikan STALE data untuk {cache_key} karena upstream gagal ({yf_res.get('error')})")
            stale_data["stale"] = True
            return stale_data

    return yf_res

def _prune_cache_if_needed():
    """Batasi cache maksimum agar RAM serverless tidak bocor."""
    if len(_CACHE) >= _CACHE_MAX_ENTRIES:
        # Hapus 20% entri paling lama
        sorted_keys = sorted(_CACHE.keys(), key=lambda k: _CACHE[k][0])
        for k in sorted_keys[:(_CACHE_MAX_ENTRIES // 5)]:
            _CACHE.pop(k, None)
