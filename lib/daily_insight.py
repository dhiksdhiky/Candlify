"""
lib/daily_insight.py — Daily Market Pulse & Multi-Broker Radar Service
======================================================================
Menyediakan agregasi cepat (di-cache in-memory) dari Neon DB / SQLite untuk:
1. Market-Wide Foreign Flow harian + Mini Bar Chart tren 20 hari + Market Breadth (% > MA20)
2. Multi-Broker Radar (gabungan 1 atau lebih broker pilihan, rentang 1D / 5D / 20D)
"""

import logging
import threading
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from lib.db import get_engine

logger = logging.getLogger("candlify.daily_insight")

_FOREIGN_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_BROKER_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_CACHE_LOCK = threading.Lock()
_MAX_CACHE_ENTRIES = 120
_LATEST_TTL = 300.0      # 5 menit untuk tanggal terbaru
_HISTORICAL_TTL = 3600.0 # 1 jam untuk tanggal historis (EOD immutable)

DEFAULT_POPULAR_BROKERS = ["AK", "BK", "ZP", "KZ", "RX", "CC", "YP", "XL", "MG"]


def _evict_if_needed(cache_dict: Dict[str, Tuple[float, Dict[str, Any]]]) -> None:
    if len(cache_dict) >= _MAX_CACHE_ENTRIES:
        oldest_key = min(cache_dict.keys(), key=lambda k: cache_dict[k][0])
        cache_dict.pop(oldest_key, None)


def clear_daily_insight_cache() -> None:
    with _CACHE_LOCK:
        _FOREIGN_CACHE.clear()
        _BROKER_CACHE.clear()


def _parse_date_str(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip()[:10]
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return s
    except ValueError:
        return None


def get_daily_foreign_insight(target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Ambil insight Foreign Flow & Market Breadth seluruh BEI pada tanggal tertentu,
    termasuk grafik batang tren Net Foreign 20 hari terakhir.
    """
    req_date = _parse_date_str(target_date)
    engine = get_engine()
    if not engine:
        return {"success": False, "error": "Database tidak terhubung"}

    now = time.time()
    cache_key = req_date or "latest"
    with _CACHE_LOCK:
        if cache_key in _FOREIGN_CACHE:
            ts, cached = _FOREIGN_CACHE[cache_key]
            ttl = _LATEST_TTL if (cache_key == "latest" or cached.get("is_latest")) else _HISTORICAL_TTL
            if now - ts < ttl:
                return cached

    try:
        with engine.connect() as conn:
            latest_db_date = conn.execute(text("SELECT MAX(tanggal) FROM harga_saham")).scalar()
            if not latest_db_date:
                return {"success": False, "error": "Belum ada data harga saham di database"}
            latest_str = str(latest_db_date)[:10]

            if not req_date:
                eff_date = latest_str
            else:
                # Cari tanggal bursa <= req_date agar klik hari libur/kosong tetap aman
                eff_raw = conn.execute(
                    text("SELECT MAX(tanggal) FROM harga_saham WHERE tanggal <= :d"),
                    {"d": req_date},
                ).scalar()
                eff_date = str(eff_raw)[:10] if eff_raw else latest_str

            is_latest = (eff_date == latest_str)

            # Cek ulang cache berdasarkan eff_date aktual
            with _CACHE_LOCK:
                if eff_date in _FOREIGN_CACHE:
                    ts, cached = _FOREIGN_CACHE[eff_date]
                    ttl = _LATEST_TTL if is_latest else _HISTORICAL_TTL
                    if now - ts < ttl:
                        return cached

            # Ambil 20 hari bursa terakhir sampai eff_date
            recent_dates_rows = conn.execute(
                text("""
                    SELECT DISTINCT tanggal
                    FROM harga_saham
                    WHERE tanggal <= :d
                    ORDER BY tanggal DESC
                    LIMIT 20
                """),
                {"d": eff_date},
            ).fetchall()
            recent_dates = [str(r[0])[:10] for r in recent_dates_rows]
            if not recent_dates:
                return {"success": False, "error": f"Tidak ada data bursa untuk tanggal {eff_date}"}

            start_20d = recent_dates[-1]
            prev_date = recent_dates[1] if len(recent_dates) > 1 else None

            # 1. Tren Foreign Flow 20 Hari (Market-Wide per hari)
            trend_rows = conn.execute(
                text("""
                    SELECT
                        tanggal,
                        SUM(CAST(COALESCE(foreign_buy, 0) AS FLOAT) *
                            CASE WHEN volume > 0 AND COALESCE(value, 0) > 0
                                 THEN (CAST(value AS FLOAT) / CAST(volume AS FLOAT))
                                 ELSE CAST(close AS FLOAT) END) AS buy_val,
                        SUM(CAST(COALESCE(foreign_sell, 0) AS FLOAT) *
                            CASE WHEN volume > 0 AND COALESCE(value, 0) > 0
                                 THEN (CAST(value AS FLOAT) / CAST(volume AS FLOAT))
                                 ELSE CAST(close AS FLOAT) END) AS sell_val,
                        SUM(CAST(COALESCE(foreign_net, 0) AS FLOAT) *
                            CASE WHEN volume > 0 AND COALESCE(value, 0) > 0
                                 THEN (CAST(value AS FLOAT) / CAST(volume AS FLOAT))
                                 ELSE CAST(close AS FLOAT) END) AS net_val
                    FROM harga_saham
                    WHERE tanggal >= :start_d AND tanggal <= :end_d
                    GROUP BY tanggal
                    ORDER BY tanggal ASC
                """),
                {"start_d": start_20d, "end_d": eff_date},
            ).fetchall()

            trend_20d = []
            today_buy_val = 0.0
            today_sell_val = 0.0
            today_net_val = 0.0
            for r in trend_rows:
                d_s = str(r[0])[:10]
                b_v = float(r[1] or 0.0)
                s_v = float(r[2] or 0.0)
                n_v = float(r[3] or 0.0)
                trend_20d.append({
                    "date": d_s,
                    "buy_val": round(b_v, 2),
                    "sell_val": round(s_v, 2),
                    "net_val": round(n_v, 2),
                })
                if d_s == eff_date:
                    today_buy_val = b_v
                    today_sell_val = s_v
                    today_net_val = n_v

            tot_f_val = today_buy_val + today_sell_val
            buy_pct = round((today_buy_val / tot_f_val) * 100.0, 1) if tot_f_val > 0 else 50.0
            sell_pct = round(100.0 - buy_pct, 1)

            # 2. Data Saham di eff_date + prev_close + MA20 untuk Breadth & Top 5 Buy/Sell
            day_rows = conn.execute(
                text("""
                    SELECT
                        h.ticker,
                        CAST(h.open AS FLOAT) AS open_p,
                        CAST(h.close AS FLOAT) AS close_p,
                        COALESCE(h.volume, 0) AS vol,
                        CAST(COALESCE(h.value, 0) AS FLOAT) AS val,
                        COALESCE(h.foreign_buy, 0) AS f_buy,
                        COALESCE(h.foreign_sell, 0) AS f_sell,
                        COALESCE(h.foreign_net, 0) AS f_net
                    FROM harga_saham h
                    WHERE h.tanggal = :d
                """),
                {"d": eff_date},
            ).fetchall()

            prev_close_map: Dict[str, float] = {}
            if prev_date:
                prev_rows = conn.execute(
                    text("SELECT ticker, CAST(close AS FLOAT) FROM harga_saham WHERE tanggal = :pd"),
                    {"pd": prev_date},
                ).fetchall()
                prev_close_map = {str(r[0]): float(r[1] or 0.0) for r in prev_rows}

            # Hitung MA20 seluruh emiten pada eff_date (1 query agregasi super cepat)
            ma20_rows = conn.execute(
                text("""
                    SELECT ticker, AVG(CAST(close AS FLOAT)) AS ma20, COUNT(*) AS cnt
                    FROM harga_saham
                    WHERE tanggal >= :start_d AND tanggal <= :end_d AND close > 0
                    GROUP BY ticker
                """),
                {"start_d": start_20d, "end_d": eff_date},
            ).fetchall()
            ma20_map = {str(r[0]): float(r[1] or 0.0) for r in ma20_rows if int(r[2] or 0) >= 5}

            advancers = 0
            decliners = 0
            unchanged = 0
            above_ma20 = 0
            total_ma20 = 0
            per_stock_foreign: List[Dict[str, Any]] = []

            for r in day_rows:
                tkr = str(r[0])
                op = float(r[1] or 0.0)
                cl = float(r[2] or 0.0)
                vol = int(r[3] or 0)
                val = float(r[4] or 0.0)
                f_net = int(r[7] or 0)

                if cl <= 0:
                    continue

                ref_p = prev_close_map.get(tkr, op)
                chg_pct = round(((cl - ref_p) / ref_p) * 100.0, 2) if ref_p > 0 else 0.0
                if chg_pct > 0.05:
                    advancers += 1
                elif chg_pct < -0.05:
                    decliners += 1
                else:
                    unchanged += 1

                ma20_val = ma20_map.get(tkr)
                if ma20_val and ma20_val > 0:
                    total_ma20 += 1
                    if cl >= ma20_val:
                        above_ma20 += 1

                if f_net != 0:
                    vwap = (val / vol) if (vol > 0 and val > 0) else cl
                    f_net_val = f_net * vwap
                    per_stock_foreign.append({
                        "ticker": tkr,
                        "net_val": round(f_net_val, 2),
                        "net_lots": int(round(f_net / 100.0)),
                        "close": round(cl, 2),
                        "change_pct": chg_pct,
                    })

            top_foreign_buy = sorted(
                [x for x in per_stock_foreign if x["net_val"] > 0],
                key=lambda x: x["net_val"],
                reverse=True,
            )[:5]

            top_foreign_sell = sorted(
                [x for x in per_stock_foreign if x["net_val"] < 0],
                key=lambda x: x["net_val"],
            )[:5]

            above_ma20_pct = round((above_ma20 / total_ma20) * 100.0, 1) if total_ma20 > 0 else 0.0

            result = {
                "success": True,
                "date": eff_date,
                "is_latest": is_latest,
                "foreign_summary": {
                    "net_val": round(today_net_val, 2),
                    "buy_val": round(today_buy_val, 2),
                    "sell_val": round(today_sell_val, 2),
                    "buy_pct": buy_pct,
                    "sell_pct": sell_pct,
                    "status": "INFLOW" if today_net_val > 0 else ("OUTFLOW" if today_net_val < 0 else "NEUTRAL"),
                },
                "breadth": {
                    "advancers": advancers,
                    "decliners": decliners,
                    "unchanged": unchanged,
                    "total_active": advancers + decliners + unchanged,
                    "above_ma20_count": above_ma20,
                    "total_ma20": total_ma20,
                    "above_ma20_pct": above_ma20_pct,
                },
                "trend_20d": trend_20d,
                "top_buy": top_foreign_buy,
                "top_sell": top_foreign_sell,
            }

            with _CACHE_LOCK:
                _evict_if_needed(_FOREIGN_CACHE)
                _FOREIGN_CACHE[eff_date] = (now, result)
                if not req_date:
                    _FOREIGN_CACHE["latest"] = (now, result)

            return result
    except Exception as e:
        logger.error(f"Error in get_daily_foreign_insight({target_date}): {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_multi_broker_insight(
    target_date: Optional[str] = None,
    brokers: Optional[List[str]] = None,
    days: int = 1,
    limit: int = 8,
) -> Dict[str, Any]:
    """
    Agregasi aktivitas gabungan 1 atau lebih broker (misal AK + BK + ZP) pada tanggal tertentu
    dengan rentang 1D, 5D, atau 20D mundur dari tanggal kalender yang diklik.
    """
    req_date = _parse_date_str(target_date)
    days_clean = days if days in (1, 5, 20) else (1 if days <= 1 else (5 if days <= 5 else 20))
    limit_clean = max(3, min(20, int(limit or 8)))

    raw_brokers = brokers or ["AK", "BK"]
    clean_brokers: List[str] = []
    for b in raw_brokers:
        code = str(b).strip().upper()
        if code and len(code) <= 4 and code.isalnum() and code not in clean_brokers:
            clean_brokers.append(code)
    if not clean_brokers:
        clean_brokers = ["AK"]

    engine = get_engine()
    if not engine:
        return {"success": False, "error": "Database tidak terhubung"}

    now = time.time()
    cache_key = f"{req_date or 'latest'}|{','.join(sorted(clean_brokers))}|{days_clean}|{limit_clean}"
    with _CACHE_LOCK:
        if cache_key in _BROKER_CACHE:
            ts, cached = _BROKER_CACHE[cache_key]
            ttl = _LATEST_TTL if cached.get("is_latest") else _HISTORICAL_TTL
            if now - ts < ttl:
                return cached

    try:
        with engine.connect() as conn:
            latest_brok_date = conn.execute(text("SELECT MAX(date) FROM broker_summary")).scalar()
            if not latest_brok_date:
                return {"success": False, "error": "Belum ada data broker summary di database"}
            latest_str = str(latest_brok_date)[:10]

            if not req_date:
                eff_date = latest_str
            else:
                eff_raw = conn.execute(
                    text("SELECT MAX(date) FROM broker_summary WHERE date <= :d"),
                    {"d": req_date},
                ).scalar()
                eff_date = str(eff_raw)[:10] if eff_raw else latest_str

            is_latest = (eff_date == latest_str)

            # Cari rentang tanggal bursa dari broker_summary mundur sebanyak days_clean hari
            win_rows = conn.execute(
                text("""
                    SELECT DISTINCT date
                    FROM broker_summary
                    WHERE date <= :d
                    ORDER BY date DESC
                    LIMIT :lim
                """),
                {"d": eff_date, "lim": days_clean},
            ).fetchall()

            if not win_rows:
                return {
                    "success": True,
                    "date": eff_date,
                    "from_date": eff_date,
                    "to_date": eff_date,
                    "trading_days": 0,
                    "days_param": days_clean,
                    "brokers": clean_brokers,
                    "is_latest": is_latest,
                    "summary": {"total_buy_val": 0.0, "total_sell_val": 0.0, "total_net_val": 0.0, "buy_pct": 50.0, "sell_pct": 50.0, "active_stocks": 0},
                    "top_buy": [],
                    "top_sell": [],
                }

            win_dates = [str(r[0])[:10] for r in win_rows]
            start_date = win_dates[-1]
            end_date = win_dates[0]
            actual_days = len(win_dates)

            # Query agregasi multi-broker (portabel SQLite & Postgres)
            placeholders = ", ".join([f":b_{i}" for i in range(len(clean_brokers))])
            params: Dict[str, Any] = {f"b_{i}": clean_brokers[i] for i in range(len(clean_brokers))}
            params["start_d"] = start_date
            params["end_d"] = end_date

            agg_rows = conn.execute(
                text(f"""
                    SELECT
                        ticker,
                        SUM(COALESCE(buy_vol, 0)) AS buy_vol,
                        SUM(COALESCE(buy_val, 0)) AS buy_val,
                        SUM(COALESCE(sell_vol, 0)) AS sell_vol,
                        SUM(COALESCE(sell_val, 0)) AS sell_val,
                        SUM(COALESCE(net_vol, 0)) AS net_vol,
                        SUM(COALESCE(net_val, 0)) AS net_val
                    FROM broker_summary
                    WHERE date >= :start_d AND date <= :end_d
                      AND broker_code IN ({placeholders})
                    GROUP BY ticker
                """),
                params,
            ).fetchall()

            # Ambil harga penutupan terdekat pada end_date
            close_rows = conn.execute(
                text("""
                    SELECT ticker, CAST(close AS FLOAT)
                    FROM harga_saham
                    WHERE tanggal = (
                        SELECT MAX(tanggal) FROM harga_saham WHERE tanggal <= :ed
                    )
                """),
                {"ed": end_date},
            ).fetchall()
            close_map = {str(r[0]): float(r[1] or 0.0) for r in close_rows}

            total_buy_val = 0.0
            total_sell_val = 0.0
            total_net_val = 0.0
            buyers_raw: List[Dict[str, Any]] = []
            sellers_raw: List[Dict[str, Any]] = []

            for r in agg_rows:
                tkr = str(r[0])
                b_vol = int(r[1] or 0)
                b_val = float(r[2] or 0.0)
                s_vol = int(r[3] or 0)
                s_val = float(r[4] or 0.0)
                n_vol = int(r[5] or 0)
                n_val = float(r[6] or 0.0)

                total_buy_val += b_val
                total_sell_val += s_val
                total_net_val += n_val

                cl = close_map.get(tkr, 0.0)

                if n_val > 0:
                    avg_p = round(b_val / (b_vol * 100.0), 1) if b_vol > 0 else 0.0
                    buyers_raw.append({
                        "ticker": tkr,
                        "net_val": round(n_val, 2),
                        "net_vol": n_vol,
                        "avg_price": avg_p,
                        "close": round(cl, 2),
                    })
                elif n_val < 0:
                    avg_p = round(s_val / (s_vol * 100.0), 1) if s_vol > 0 else 0.0
                    sellers_raw.append({
                        "ticker": tkr,
                        "net_val": round(n_val, 2),
                        "net_vol": n_vol,
                        "avg_price": avg_p,
                        "close": round(cl, 2),
                    })

            buyers_raw.sort(key=lambda x: x["net_val"], reverse=True)
            sellers_raw.sort(key=lambda x: x["net_val"])

            top_buy = buyers_raw[:limit_clean]
            top_sell = sellers_raw[:limit_clean]

            # Tambah skala bar proporsional (bar_pct) agar mudah divisualisasikan
            max_buy = top_buy[0]["net_val"] if top_buy else 1.0
            for item in top_buy:
                item["bar_pct"] = max(8, min(100, int(round((item["net_val"] / max_buy) * 100))))

            max_sell = abs(top_sell[0]["net_val"]) if top_sell else 1.0
            for item in top_sell:
                item["bar_pct"] = max(8, min(100, int(round((abs(item["net_val"]) / max_sell) * 100))))

            tot_gross = total_buy_val + total_sell_val
            buy_pct = round((total_buy_val / tot_gross) * 100.0, 1) if tot_gross > 0 else 50.0
            sell_pct = round(100.0 - buy_pct, 1)

            result = {
                "success": True,
                "date": end_date,
                "from_date": start_date,
                "to_date": end_date,
                "trading_days": actual_days,
                "days_param": days_clean,
                "brokers": clean_brokers,
                "is_latest": is_latest,
                "summary": {
                    "total_buy_val": round(total_buy_val, 2),
                    "total_sell_val": round(total_sell_val, 2),
                    "total_net_val": round(total_net_val, 2),
                    "buy_pct": buy_pct,
                    "sell_pct": sell_pct,
                    "active_stocks": len(agg_rows),
                },
                "top_buy": top_buy,
                "top_sell": top_sell,
            }

            with _CACHE_LOCK:
                _evict_if_needed(_BROKER_CACHE)
                _BROKER_CACHE[cache_key] = (now, result)

            return result
    except Exception as e:
        logger.error(f"Error in get_multi_broker_insight({target_date}, {brokers}, {days}): {e}", exc_info=True)
        return {"success": False, "error": str(e)}
