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


# Cache in-memory untuk pemetaan papan pencatatan BEI
_BOARD_MAP: Dict[str, str] = {}
_BOARD_MAP_TIMESTAMP: float = 0.0
_BOARD_MAP_LOCK = threading.Lock()
_BOARD_MAP_TTL = 3600.0  # 1 jam


def get_stock_board_map() -> Dict[str, str]:
    """
    Ambil mapping kode saham -> papan pencatatan (Utama, Pengembangan, Pemantauan Khusus, Akselerasi).
    Prioritas: Database daftar_saham -> Fallback: worker/daftar_saham.csv.
    """
    global _BOARD_MAP, _BOARD_MAP_TIMESTAMP
    now = time.time()
    if _BOARD_MAP and (now - _BOARD_MAP_TIMESTAMP < _BOARD_MAP_TTL):
        return _BOARD_MAP

    with _BOARD_MAP_LOCK:
        if _BOARD_MAP and (time.time() - _BOARD_MAP_TIMESTAMP < _BOARD_MAP_TTL):
            return _BOARD_MAP

        b_map: Dict[str, str] = {}
        # 1. Coba dari database Neon DB
        try:
            from lib.db import get_db_engine
            from sqlalchemy import text
            eng = get_db_engine()
            if eng:
                with eng.connect() as conn:
                    rows = conn.execute(text("SELECT kode, papan_pencatatan FROM daftar_saham")).fetchall()
                    for r in rows:
                        if r[0]:
                            b_map[str(r[0]).strip().upper()] = str(r[1] or "Pengembangan").strip()
        except Exception as e:
            logger.warning(f"Gagal mengambil board map dari DB, mencoba CSV: {e}")

        # 2. Fallback dari CSV jika DB kosong/error
        if not b_map:
            import os
            import csv
            csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "worker", "daftar_saham.csv")
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                        reader = csv.reader(f, delimiter=";")
                        for row in reader:
                            if len(row) >= 6 and row[1] and row[1] != "Kode":
                                b_map[row[1].strip().upper()] = row[5].strip()
                except Exception as e:
                    logger.warning(f"Gagal membaca fallback CSV daftar_saham: {e}")

        if b_map:
            _BOARD_MAP = b_map
            _BOARD_MAP_TIMESTAMP = time.time()
            logger.info(f"Loaded board map for {len(_BOARD_MAP)} stocks")

        return _BOARD_MAP


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
        board_map = get_stock_board_map()

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

            board_val = board_map.get(clean_symbol, "Pengembangan")
            is_fca = ("Pemantauan" in board_val)

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
                "board": board_val,
                "is_fca": is_fca,
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


# Cache in-memory untuk sinyal pre-breakout: { "timestamp": float, "data": dict }
_SIGNALS_CACHE: Dict[str, Any] = {"timestamp": 0.0, "data": {}}
_SIGNALS_LOCK = threading.Lock()
_SIGNALS_TTL = 60.0


def get_pre_breakout_signals(target_date: Optional[str] = None, min_score: int = 60, limit: int = 100) -> Dict[str, Any]:
    """Ambil sinyal pre-breakout dari tabel candlify_signals dengan in-memory cache."""
    global _SIGNALS_CACHE
    now = time.time()
    cache_key = f"{target_date or 'latest'}_{min_score}_{limit}"

    with _SIGNALS_LOCK:
        if (now - _SIGNALS_CACHE.get("timestamp", 0.0) < _SIGNALS_TTL) and cache_key in _SIGNALS_CACHE.get("data", {}):
            return _SIGNALS_CACHE["data"][cache_key]

    from lib.db import get_db_engine
    engine = get_db_engine()
    if not engine:
        return {"success": False, "error": "Database tidak terhubung", "count": 0, "signals": []}

    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            if not target_date:
                max_d = conn.execute(text("SELECT MAX(date) FROM candlify_signals")).scalar()
                if not max_d:
                    return {"success": True, "date": None, "count": 0, "signals": []}
                target_date_str = str(max_d)
            else:
                target_date_str = target_date

            stmt = text("""
                SELECT s.date, s.ticker, s.price, s.range_7, s.volume_dry_ratio, s.bbw, s.price_to_ma20, s.hmb, s.top_accumulator, s.score, s.created_at,
                       COALESCE(d.papan_pencatatan, 'Utama') AS papan_pencatatan
                FROM candlify_signals s
                LEFT JOIN daftar_saham d ON s.ticker = d.kode
                WHERE s.date = :t_date AND s.score >= :min_score
                ORDER BY s.score DESC, s.range_7 ASC
                LIMIT :limit
            """)
            rows = conn.execute(stmt, {"t_date": target_date_str, "min_score": min_score, "limit": limit}).mappings().all()

            signals = []
            for r in rows:
                board_val = r.get("papan_pencatatan") or "Utama"
                signals.append({
                    "date": str(r["date"]),
                    "ticker": r["ticker"],
                    "price": float(r["price"]),
                    "range_7": float(r["range_7"]),
                    "volume_dry_ratio": float(r["volume_dry_ratio"]),
                    "bbw": float(r["bbw"]),
                    "price_to_ma20": float(r["price_to_ma20"]),
                    "hmb": float(r["hmb"]) if r["hmb"] is not None else None,
                    "top_accumulator": r["top_accumulator"],
                    "score": int(r["score"]),
                    "board": board_val,
                    "is_fca": ("Pemantauan" in board_val),
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None
                })

            result = {
                "success": True,
                "date": target_date_str,
                "count": len(signals),
                "signals": signals
            }

            with _SIGNALS_LOCK:
                if now - _SIGNALS_CACHE.get("timestamp", 0.0) >= _SIGNALS_TTL:
                    _SIGNALS_CACHE = {"timestamp": now, "data": {}}
                _SIGNALS_CACHE["data"][cache_key] = result

            return result
    except Exception as e:
        logger.error(f"Error fetching pre-breakout signals: {e}")
        return {"success": False, "error": str(e), "count": 0, "signals": []}


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

    elif preset in ("pre_breakout", "bali"):
        # Pre-Breakout Base: Range ketat, Volume Kering, Akumulasi Bandar
        sig_data = get_pre_breakout_signals(min_score=60, limit=200)
        if not sig_data.get("success", False):
            logger.warning(f"⚠️ Gagal memuat sinyal pre-breakout untuk screener: {sig_data.get('error')}")
            return []

        signals = sig_data.get("signals", [])
        if not signals:
            return []

        sig_map = {s["ticker"]: s for s in signals}
        matched = []
        seen = set()

        for s in stocks:
            sym = s.get("symbol")
            if sym in sig_map:
                sig = sig_map[sym]
                s_copy = dict(s)
                s_copy["score"] = sig["score"]
                s_copy["range_7"] = sig["range_7"]
                s_copy["volume_dry_ratio"] = sig["volume_dry_ratio"]
                s_copy["top_accumulator"] = sig["top_accumulator"]
                s_copy["hmb"] = sig["hmb"]
                s_copy["price_to_ma20"] = sig["price_to_ma20"]
                s_copy["board"] = sig.get("board", "Utama")
                s_copy["is_fca"] = sig.get("is_fca", False)
                s_copy["is_pre_breakout"] = True
                matched.append(s_copy)
                seen.add(sym)

        for sym, sig in sig_map.items():
            if sym not in seen:
                matched.append({
                    "symbol": sym,
                    "name": sym,
                    "price": int(round(sig["price"])) if sig["price"] >= 1 else float(round(sig["price"], 2)),
                    "change_pct": 0.0,
                    "volume": 0,
                    "market_cap": 0,
                    "volume_surge": 0.0,
                    "rsi": None,
                    "score": sig["score"],
                    "range_7": sig["range_7"],
                    "volume_dry_ratio": sig["volume_dry_ratio"],
                    "top_accumulator": sig["top_accumulator"],
                    "hmb": sig["hmb"],
                    "price_to_ma20": sig["price_to_ma20"],
                    "board": sig.get("board", "Utama"),
                    "is_fca": sig.get("is_fca", False),
                    "is_pre_breakout": True
                })

        return matched

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
    elif sort_key == "score_desc":
        return sorted(stocks, key=lambda x: x.get("score", 0) or 0, reverse=True)
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

    eff_sort = sort or "change_desc"
    if preset in ("pre_breakout", "bali") and eff_sort == "change_desc":
        eff_sort = "score_desc"

    sorted_stocks = sort_stocks(filtered, eff_sort)

    return {
        "success": True,
        "preset": preset or "all",
        "search": search or "",
        "sort": eff_sort,
        "total_universe": len(all_stocks),
        "count": len(sorted_stocks),
        "stocks": sorted_stocks
    }
