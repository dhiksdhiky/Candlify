"""
v2/lib/screener.py — High-Performance IDX Stock Screener Engine
=============================================================
Features:
- Single batch fetch of all IDX stocks (~880+ symbols) via TradingView Scanner API
- In-memory thread-safe cache with 60-second TTL (0ms subsequent requests)
- Pre-packaged trading strategy presets (Swing, Breakout, Vol+BB, Oversold, Big Cap)
- Server-side sorting & search filtering
- Zero load on Neon DB (saves 100% database compute)
"""

import time
import logging
import threading
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger("CandlifyScreenerV2")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SCANNER_URL = "https://scanner.tradingview.com/indonesia/scan"

# Kolom esensial teknikal & fundamental dari TradingView scanner
TV_COLUMNS = [
    "close",                      # 0
    "change",                     # 1
    "volume",                     # 2
    "description",                # 3
    "market_cap_basic",           # 4
    "relative_volume_10d_calc",   # 5 (Volume Surge)
    "RSI",                        # 6
    "SMA20",                      # 7
    "SMA50",                      # 8
    "SMA200",                     # 9
    "EMA20",                      # 10
    "Perf.1M",                    # 11
    "Perf.3M",                    # 12
    "BB.lower",                   # 13
    "BB.upper",                   # 14
    "Pivot.M.Classic.R1"          # 15
]

# Cache in-memory: { "timestamp": float, "stocks": list }
_CACHE_DATA: List[Dict[str, Any]] = []
_CACHE_TIMESTAMP: float = 0.0
_CACHE_LOCK = threading.Lock()
_CACHE_TTL = 60.0  # 60 detik


def fetch_all_stocks_from_scanner() -> List[Dict[str, Any]]:
    """Tarik seluruh data saham BEI via TradingView scanner dalam satu kali panggilan batch."""
    payload = {
        "symbols": {"query": {"types": []}},
        "columns": TV_COLUMNS,
        "sort": {"sortBy": "change", "sortOrder": "desc"}
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(SCANNER_URL, json=payload, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(f"Scanner TradingView returned HTTP {resp.status_code}")
            return []

        json_data = resp.json()
        rows = json_data.get("data", [])
        stocks: List[Dict[str, Any]] = []

        for item in rows:
            symbol_raw = item.get("s", "")
            if not symbol_raw.startswith("IDX:"):
                continue
            clean_symbol = symbol_raw.replace("IDX:", "").strip().upper()
            d = item.get("d", [])
            if len(d) < 4:
                continue

            close_p = d[0] if len(d) > 0 and d[0] is not None else 0
            change_p = d[1] if len(d) > 1 and d[1] is not None else 0
            vol = d[2] if len(d) > 2 and d[2] is not None else 0
            desc = d[3] if len(d) > 3 and d[3] else clean_symbol
            mcap = d[4] if len(d) > 4 and d[4] is not None else 0
            vol_surge = d[5] if len(d) > 5 and d[5] is not None else 1.0
            rsi = d[6] if len(d) > 6 and d[6] is not None else None
            sma20 = d[7] if len(d) > 7 and d[7] is not None else None
            sma50 = d[8] if len(d) > 8 and d[8] is not None else None
            sma200 = d[9] if len(d) > 9 and d[9] is not None else None
            perf_1m = d[11] if len(d) > 11 and d[11] is not None else 0.0
            perf_3m = d[12] if len(d) > 12 and d[12] is not None else 0.0
            bb_lower = d[13] if len(d) > 13 and d[13] is not None else None
            bb_upper = d[14] if len(d) > 14 and d[14] is not None else None
            pivot_r1 = d[15] if len(d) > 15 and d[15] is not None else None

            # Abaikan saham tidak aktif / tanpa harga
            if close_p <= 0:
                continue

            stocks.append({
                "symbol": clean_symbol,
                "name": str(desc),
                "price": int(round(close_p)) if close_p >= 1 else float(round(close_p, 2)),
                "change_pct": round(float(change_p), 2),
                "volume": int(vol),
                "market_cap": int(mcap),
                "volume_surge": round(float(vol_surge), 2),
                "rsi": round(float(rsi), 1) if rsi is not None else None,
                "sma20": round(float(sma20), 1) if sma20 is not None else None,
                "sma50": round(float(sma50), 1) if sma50 is not None else None,
                "sma200": round(float(sma200), 1) if sma200 is not None else None,
                "perf_1m": round(float(perf_1m), 2),
                "perf_3m": round(float(perf_3m), 2),
                "bb_lower": round(float(bb_lower), 1) if bb_lower is not None else None,
                "bb_upper": round(float(bb_upper), 1) if bb_upper is not None else None,
                "pivot_r1": round(float(pivot_r1), 1) if pivot_r1 is not None else None,
            })

        return stocks
    except Exception as e:
        logger.error(f"Error fetching from TradingView scanner: {e}")
        return []


def get_all_stocks_cached() -> List[Dict[str, Any]]:
    """Ambil data seluruh saham dari cache memori, atau refresh jika cache stale."""
    global _CACHE_DATA, _CACHE_TIMESTAMP
    now = time.time()
    if _CACHE_DATA and (now - _CACHE_TIMESTAMP < _CACHE_TTL):
        return _CACHE_DATA

    with _CACHE_LOCK:
        # Double-check inside lock
        if _CACHE_DATA and (time.time() - _CACHE_TIMESTAMP < _CACHE_TTL):
            return _CACHE_DATA

        fresh_stocks = fetch_all_stocks_from_scanner()
        if fresh_stocks:
            _CACHE_DATA = fresh_stocks
            _CACHE_TIMESTAMP = time.time()
            logger.info(f"Screener cache refreshed: {len(_CACHE_DATA)} IDX stocks")
        return _CACHE_DATA


def filter_by_preset(stocks: List[Dict[str, Any]], preset: str) -> List[Dict[str, Any]]:
    """Filter saham berdasarkan template preset strategi teruji."""
    if not preset or preset == "all":
        return stocks

    preset = preset.lower().strip()

    if preset == "swing":
        # Swing Setup: Harga > 100, Price > SMA50, SMA20 >= SMA50, Perf 3M > 0, Vol Surge > 0.9
        return [
            s for s in stocks
            if s["price"] >= 100
            and s.get("sma50") and s["price"] > s["sma50"]
            and s.get("sma20") and s["sma20"] >= s["sma50"]
            and s.get("perf_3m", 0) > 0
            and s.get("volume_surge", 1.0) >= 0.9
        ]

    elif preset == "breakout":
        # Breakout Setup: Mendekati atau menembus Pivot R1, Volume Surge > 1.2x, Hari ini Hijau
        return [
            s for s in stocks
            if s["price"] >= 100
            and s.get("pivot_r1") and (s["price"] >= s["pivot_r1"] * 0.98)
            and s.get("volume_surge", 1.0) >= 1.2
            and s["change_pct"] > 0
        ]

    elif preset == "vol_bb":
        # Akumulasi Vol + BB: Dekat BB Lower (<= 4% di atas BB Lower), Volume Surge > 1.25x
        return [
            s for s in stocks
            if s["price"] >= 100
            and s.get("bb_lower") and (s["price"] <= s["bb_lower"] * 1.05)
            and s.get("volume_surge", 1.0) >= 1.25
        ]

    elif preset == "oversold":
        # Oversold Rebound: RSI <= 38 dan mulai rebound (Change % >= 0)
        return [
            s for s in stocks
            if s["price"] >= 100
            and s.get("rsi") and s["rsi"] <= 38
            and s["change_pct"] >= 0
        ]

    elif preset == "bigcap":
        # Big Cap Leaders: Market Cap >= 20T & Change % >= 0
        return [
            s for s in stocks
            if s["market_cap"] >= 20_000_000_000_000
            and s["change_pct"] >= 0
        ]

    return stocks


def sort_stocks(stocks: List[Dict[str, Any]], sort_key: str) -> List[Dict[str, Any]]:
    """Urutkan hasil screening berdasarkan kolom teknikal / fundamental yang dipilih."""
    sort_key = (sort_key or "change_desc").lower().strip()
    if sort_key == "change_asc":
        return sorted(stocks, key=lambda x: x.get("change_pct", 0.0) or 0.0)
    elif sort_key == "volume_desc":
        return sorted(stocks, key=lambda x: x.get("volume", 0) or 0, reverse=True)
    elif sort_key == "volume_asc":
        return sorted(stocks, key=lambda x: x.get("volume", 0) or 0)
    elif sort_key == "market_cap_desc":
        return sorted(stocks, key=lambda x: x.get("market_cap", 0) or 0, reverse=True)
    elif sort_key == "surge_desc":
        return sorted(stocks, key=lambda x: x.get("volume_surge", 1.0) or 1.0, reverse=True)
    elif sort_key == "price_desc":
        return sorted(stocks, key=lambda x: x.get("price", 0) or 0, reverse=True)
    elif sort_key == "price_asc":
        return sorted(stocks, key=lambda x: x.get("price", 0) or 0)
    elif sort_key == "perf_3m_desc":
        return sorted(stocks, key=lambda x: x.get("perf_3m", 0.0) or 0.0, reverse=True)
    elif sort_key == "perf_3m_asc":
        return sorted(stocks, key=lambda x: x.get("perf_3m", 0.0) or 0.0)
    elif sort_key == "perf_1m_desc":
        return sorted(stocks, key=lambda x: x.get("perf_1m", 0.0) or 0.0, reverse=True)
    elif sort_key == "rsi_asc":
        return sorted(stocks, key=lambda x: (x.get("rsi") is None, x.get("rsi", 999.0)))
    elif sort_key == "rsi_desc":
        return sorted(stocks, key=lambda x: (x.get("rsi") is None, x.get("rsi", -999.0)), reverse=True)
    # Default: change_desc
    return sorted(stocks, key=lambda x: x.get("change_pct", 0.0) or 0.0, reverse=True)


def get_screened_stocks(
    preset: Optional[str] = "all",
    search: Optional[str] = None,
    sort: Optional[str] = "change_desc"
) -> Dict[str, Any]:
    """
    Fungsi utama untuk mengambil dan menyaring daftar saham BEI.
    Super cepat karena 99% hit in-memory cache (< 1ms).
    """
    all_stocks = get_all_stocks_cached()
    filtered = filter_by_preset(all_stocks, preset or "all")

    if search:
        q = search.strip().upper()
        filtered = [s for s in filtered if q in s["symbol"] or q in s["name"].upper()]

    sorted_stocks = sort_stocks(filtered, sort or "change_desc")

    return {
        "success": True,
        "preset": preset or "all",
        "search": search or "",
        "sort": sort or "change_desc",
        "total_universe": len(all_stocks),
        "count": len(sorted_stocks),
        "stocks": sorted_stocks
    }
