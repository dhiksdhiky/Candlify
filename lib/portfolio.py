"""
v2/lib/portfolio.py — Watchlist & Risk Management Module (Neon PostgreSQL)
==========================================================================
Menyediakan operasi data cloud untuk:
- Watchlist CRUD dengan kategori 'Breakout' (dan custom category)
- Live price & change enrichment dari screener in-memory cache
- Perhitungan usia pantauan (e.g. 'Hari ini', '2h lalu') untuk review berkala
- Pengaturan profil risiko & modal (Capital & Max Risk %)
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
# Centralized DB engine & utils
from lib.db import get_engine, get_db_engine
from lib.utils import clean_symbol

def _format_age(created_at: datetime) -> str:
    """Format human-readable age untuk review berkala watchlist."""
    if not created_at:
        return "Baru"
    
    now = datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    delta = now - created_at
    if delta.total_seconds() < 0:
        return "Baru saja"

    days = delta.days
    hours = delta.seconds // 3600
    minutes = delta.seconds // 60

    if days == 0:
        if minutes <= 5:
            return "Baru saja"
        if hours < 1:
            return f"{minutes}m lalu"
        return f"{hours}j lalu"
    elif days == 1:
        return "Kemarin"
    elif days < 7:
        return f"{days}h lalu"
    elif days < 28:
        return f"{days // 7}mgg lalu"
    else:
        return f"{max(1, days // 30)}bln lalu"


def get_all_watchlists(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ambil seluruh daftar saham watchlist dari Neon DB.
    Otomatis memperkaya data dengan harga real-time, % change harian, dan volume dari cache screener.
    """
    engine = get_engine()
    
    query = """
        SELECT id, symbol, category, target_entry, notes, is_active, created_at, updated_at
        FROM candlify_watchlists
        WHERE is_active = TRUE
    """
    params = {}
    if category and category.lower() != "all":
        query += " AND LOWER(category) = LOWER(:category)"
        params["category"] = category

    query += " ORDER BY created_at DESC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    # Import lazy cache screener untuk live data enrichment tanpa membebani network
    stock_map = {}
    try:
        from lib.screener import get_all_stocks_cached
        cached_stocks = get_all_stocks_cached() or []
        for s in cached_stocks:
            stock_map[s["symbol"]] = s
    except Exception as e:
        logger.warning(f"Gagal memuat cache screener untuk watchlist enrichment: {e}")

    items = []
    for r in rows:
        sym = r["symbol"]
        live = stock_map.get(sym, {})

        items.append({
            "id": r["id"],
            "symbol": sym,
            "category": r["category"],
            "target_entry": r["target_entry"],
            "notes": r["notes"] or "",
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "age": _format_age(r["created_at"]),
            # Live Metrics
            "price": live.get("price"),
            "change_pct": live.get("change_pct", 0.0),
            "volume": live.get("volume", 0),
            "market_cap": live.get("market_cap", 0),
            "name": live.get("name", sym),
            "board": live.get("board", "Utama"),
            "is_fca": live.get("is_fca", False)
        })

    return items


def add_to_watchlist(symbol: str, category: str = "Breakout", notes: str = "", target_entry: Optional[float] = None) -> Dict[str, Any]:
    """Tambah saham ke watchlist Neon DB (atau update jika kombinasi simbol & kategori sudah ada)."""
    clean_sym = clean_symbol(symbol)

    clean_category = (category or "Breakout").strip()
    engine = get_engine()

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM candlify_watchlists WHERE symbol = :symbol AND LOWER(category) = LOWER(:category) AND is_active = TRUE"),
            {"symbol": clean_sym, "category": clean_category}
        ).fetchone()

        if existing:
            row = conn.execute(
                text("""
                    UPDATE candlify_watchlists
                    SET notes = :notes, target_entry = :target_entry, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    RETURNING id, symbol, category, target_entry, notes, created_at
                """),
                {"id": existing[0], "notes": notes or "", "target_entry": target_entry}
            ).mappings().one()
        else:
            query = """
                INSERT INTO candlify_watchlists (symbol, category, target_entry, notes, is_active, updated_at)
                VALUES (:symbol, :category, :target_entry, :notes, TRUE, CURRENT_TIMESTAMP)
                RETURNING id, symbol, category, target_entry, notes, created_at
            """
            row = conn.execute(
                text(query),
                {
                    "symbol": clean_sym,
                    "category": clean_category,
                    "target_entry": target_entry,
                    "notes": notes or ""
                }
            ).mappings().one()

    return {
        "success": True,
        "message": f"Saham {clean_sym} berhasil ditambahkan ke Watchlist ({clean_category})",
        "data": dict(row)
    }


def update_watchlist_item(item_id: int, notes: Optional[str] = None, target_entry: Optional[float] = None, category: Optional[str] = None) -> Dict[str, Any]:
    """Update catatan atau target entry watchlist item."""
    engine = get_engine()

    updates = []
    params = {"id": item_id}

    if notes is not None:
        updates.append("notes = :notes")
        params["notes"] = notes
    if target_entry is not None:
        updates.append("target_entry = :target_entry")
        params["target_entry"] = target_entry
    if category is not None:
        updates.append("category = :category")
        params["category"] = category.strip()

    if not updates:
        return {"success": True, "message": "Tidak ada perubahan"}

    updates.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE candlify_watchlists SET {', '.join(updates)} WHERE id = :id RETURNING id, symbol, category, target_entry, notes"

    with engine.begin() as conn:
        res = conn.execute(text(sql), params).mappings().one_or_none()

    if not res:
        raise ValueError(f"Watchlist item ID {item_id} tidak ditemukan")

    return {
        "success": True,
        "message": "Watchlist berhasil diperbarui",
        "data": dict(res)
    }


def delete_from_watchlist(item_id: int) -> Dict[str, Any]:
    """Hapus saham dari watchlist Neon DB."""
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text("DELETE FROM candlify_watchlists WHERE id = :id RETURNING symbol"),
            {"id": item_id}
        ).fetchone()

    if not res:
        raise ValueError(f"Watchlist item ID {item_id} tidak ditemukan")

    return {
        "success": True,
        "message": f"Saham {res[0]} berhasil dihapus dari Watchlist"
    }


def get_risk_settings() -> Dict[str, Any]:
    """Ambil pengaturan modal, toleransi risiko akun, dan data source dari Neon DB."""
    engine = get_engine()
    default_settings = {
        "total_capital": 100000000, # Rp 100.000.000
        "risk_pct": 1.0,            # 1.0% (Rp 1.000.000 per trade)
        "default_category": "Breakout",
        "daily_source": "neon_db"   # "neon_db" atau "yahoo"
    }

    try:
        with engine.connect() as conn:
            raw = conn.execute(
                text("SELECT value FROM candlify_user_settings WHERE key = 'risk_management'")
            ).scalar()
            if raw:
                data = json.loads(raw) if isinstance(raw, str) else raw
                default_settings.update(data)
    except Exception as e:
        logger.warning(f"Gagal mengambil settings dari DB, menggunakan fallback default: {e}")

    # Hitung nominal risiko otomatis
    capital = default_settings.get("total_capital", 100000000)
    risk_pct = default_settings.get("risk_pct", 1.0)
    default_settings["risk_nominal"] = int(round(capital * (risk_pct / 100.0)))
    default_settings.setdefault("max_exposure_pct", 0.20)

    return default_settings


def save_risk_settings(
    total_capital: float, 
    risk_pct: float, 
    default_category: str = "Breakout",
    daily_source: str = "neon_db"
) -> Dict[str, Any]:
    """Simpan pengaturan modal, risiko, dan data source ke Neon DB."""
    if total_capital <= 0:
        raise ValueError("Modal total harus lebih besar dari 0")
    if risk_pct <= 0 or risk_pct > 100:
        raise ValueError("Toleransi risiko harus antara 0.1% dan 100%")

    payload = {
        "total_capital": float(total_capital),
        "risk_pct": float(risk_pct),
        "default_category": default_category or "Breakout",
        "daily_source": daily_source if daily_source in ("neon_db", "yahoo") else "neon_db"
    }

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO candlify_user_settings (key, value, updated_at)
                VALUES ('risk_management', :val, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE
                SET value = :val, updated_at = CURRENT_TIMESTAMP
            """),
            {"val": json.dumps(payload)}
        )

    payload["risk_nominal"] = int(round(total_capital * (risk_pct / 100.0)))
    return {
        "success": True,
        "message": "Pengaturan modal, risiko, dan sumber data berhasil disimpan",
        "data": payload
    }


# ── Watchlist Categories Management (Neon PostgreSQL) ─────────

def get_watchlist_categories() -> List[str]:
    """Ambil daftar kategori watchlist tersimpan dari Neon DB."""
    engine = get_engine()
    default_cats = ["Breakout"]
    try:
        with engine.connect() as conn:
            raw = conn.execute(
                text("SELECT value FROM candlify_user_settings WHERE key = 'watchlist_categories'")
            ).scalar()
            if raw:
                cats = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(cats, list) and len(cats) > 0:
                    cleaned = []
                    for c in cats:
                        if isinstance(c, str) and c.strip() and c.strip() not in cleaned:
                            cleaned.append(c.strip())
                    if "Breakout" not in cleaned:
                        cleaned.insert(0, "Breakout")
                    return cleaned
    except Exception as e:
        logger.warning(f"Gagal mengambil watchlist_categories: {e}")
    return default_cats


def save_watchlist_categories(categories: List[str]) -> List[str]:
    """Simpan daftar kategori watchlist ke Neon DB."""
    cleaned = []
    for c in categories:
        if isinstance(c, str) and c.strip() and c.strip() not in cleaned:
            cleaned.append(c.strip())
    if "Breakout" not in cleaned:
        cleaned.insert(0, "Breakout")

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO candlify_user_settings (key, value, updated_at)
                VALUES ('watchlist_categories', :val, CURRENT_TIMESTAMP)
                ON CONFLICT (key) DO UPDATE
                SET value = :val, updated_at = CURRENT_TIMESTAMP
            """),
            {"val": json.dumps(cleaned)}
        )
    return cleaned


def add_watchlist_category(name: str) -> List[str]:
    """Tambah kategori watchlist baru ke Neon DB."""
    clean = (name or "").strip()
    if not clean:
        raise ValueError("Nama kategori tidak boleh kosong")
    if len(clean) > 50:
        raise ValueError("Nama kategori maksimal 50 karakter")

    current = get_watchlist_categories()
    if any(c.lower() == clean.lower() for c in current):
        raise ValueError(f"Kategori '{clean}' sudah ada")

    current.append(clean)
    return save_watchlist_categories(current)


def rename_watchlist_category(old_name: str, new_name: str) -> List[str]:
    """Ubah nama kategori watchlist dan update seluruh saham di kategori tersebut."""
    old_clean = (old_name or "").strip()
    new_clean = (new_name or "").strip()
    if not new_clean:
        raise ValueError("Nama kategori baru tidak boleh kosong")
    if old_clean.lower() == "breakout":
        raise ValueError("Kategori default 'Breakout' tidak boleh diubah namanya")

    current = get_watchlist_categories()
    if not any(c.lower() == old_clean.lower() for c in current):
        raise ValueError(f"Kategori '{old_name}' tidak ditemukan")
    if any(c.lower() == new_clean.lower() and c.lower() != old_clean.lower() for c in current):
        raise ValueError(f"Kategori '{new_name}' sudah ada")

    updated = [new_clean if c.lower() == old_clean.lower() else c for c in current]
    save_watchlist_categories(updated)

    # Sinkronisasikan nama kategori di database candlify_watchlists
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE candlify_watchlists SET category = :new_cat, updated_at = CURRENT_TIMESTAMP WHERE LOWER(category) = LOWER(:old_cat)"),
            {"new_cat": new_clean, "old_cat": old_clean}
        )
    return updated


def delete_watchlist_category(name: str) -> List[str]:
    """Hapus kategori watchlist dan pindahkan saham di dalamnya ke 'Breakout'."""
    clean = (name or "").strip()
    if clean.lower() == "breakout":
        raise ValueError("Kategori default 'Breakout' tidak boleh dihapus")

    current = get_watchlist_categories()
    if not any(c.lower() == clean.lower() for c in current):
        raise ValueError(f"Kategori '{name}' tidak ditemukan")

    updated = [c for c in current if c.lower() != clean.lower()]
    save_watchlist_categories(updated)

    # Pindahkan saham yang berada di kategori ini ke 'Breakout' agar data aman
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE candlify_watchlists SET category = 'Breakout', updated_at = CURRENT_TIMESTAMP WHERE LOWER(category) = LOWER(:cat)"),
            {"cat": clean}
        )
    return updated


def get_stock_watchlists(symbol: str) -> Dict[str, Any]:
    """Ambil seluruh kategori watchlist aktif untuk suatu saham tertentu beserta notes & target entry."""
    try:
        clean_sym = clean_symbol(symbol)
    except ValueError:
        return {"success": False, "symbol": symbol, "categories": [], "items": []}

    engine = get_engine()
    query = """
        SELECT id, symbol, category, target_entry, notes, created_at, updated_at
        FROM candlify_watchlists
        WHERE is_active = TRUE AND symbol = :symbol
        ORDER BY created_at ASC
    """
    with engine.connect() as conn:
        rows = conn.execute(text(query), {"symbol": clean_sym}).mappings().all()

    items = [dict(r) for r in rows]
    categories = [r["category"] for r in rows if r.get("category")]

    latest_target = None
    latest_notes = ""
    for r in reversed(items):
        if r.get("target_entry") is not None and latest_target is None:
            latest_target = r["target_entry"]
        if r.get("notes") and not latest_notes:
            latest_notes = r["notes"]

    return {
        "success": True,
        "symbol": clean_sym,
        "categories": categories,
        "target_entry": latest_target,
        "notes": latest_notes,
        "items": items
    }


def sync_stock_watchlists(
    symbol: str,
    categories: List[str],
    notes: Optional[str] = None,
    target_entry: Optional[float] = None
) -> Dict[str, Any]:
    """
    Sinkronisasi multi-watchlist untuk suatu saham (tambah, update, atau hapus kategori).
    Jika categories kosong [], saham dihapus dari seluruh watchlist.
    """
    clean_sym = clean_symbol(symbol)

    cleaned_cats = []
    for c in categories:
        if isinstance(c, str) and c.strip() and c.strip() not in cleaned_cats:
            cleaned_cats.append(c.strip())

    engine = get_engine()
    with engine.begin() as conn:
        curr_rows = conn.execute(
            text("SELECT id, category FROM candlify_watchlists WHERE symbol = :symbol AND is_active = TRUE"),
            {"symbol": clean_sym}
        ).mappings().all()

        curr_map = {r["category"].lower(): r["id"] for r in curr_rows}
        desired_lower = {c.lower() for c in cleaned_cats}

        # 1. Hapus entri kategori yang di-uncheck
        for cat_lower, item_id in curr_map.items():
            if cat_lower not in desired_lower:
                conn.execute(
                    text("DELETE FROM candlify_watchlists WHERE id = :id"),
                    {"id": item_id}
                )

        # 2. Update existing atau Insert kategori yang baru dipilih
        for cat in cleaned_cats:
            cat_lower = cat.lower()
            if cat_lower in curr_map:
                conn.execute(
                    text("""
                        UPDATE candlify_watchlists
                        SET category = :cat, target_entry = :target_entry, notes = :notes, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """),
                    {
                        "id": curr_map[cat_lower],
                        "cat": cat,
                        "target_entry": target_entry,
                        "notes": notes or ""
                    }
                )
            else:
                conn.execute(
                    text("""
                        INSERT INTO candlify_watchlists (symbol, category, target_entry, notes, is_active, updated_at)
                        VALUES (:symbol, :category, :target_entry, :notes, TRUE, CURRENT_TIMESTAMP)
                    """),
                    {
                        "symbol": clean_sym,
                        "category": cat,
                        "target_entry": target_entry,
                        "notes": notes or ""
                    }
                )

    action_msg = f"Watchlist {clean_sym} diperbarui: {', '.join(cleaned_cats) if cleaned_cats else 'Dihapus dari semua watchlist'}"
    return {
        "success": True,
        "symbol": clean_sym,
        "categories": cleaned_cats,
        "message": action_msg
    }


# ── Trading Plan & Journal Module (Neon PostgreSQL) ──────────

def get_all_trading_plans(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Ambil seluruh trading plan dari Neon DB, diperkaya dengan harga live & live PnL.
    """
    engine = get_engine()
    query = """
        SELECT id, symbol, category, order_type, entry_price, sl_price, tp1_price, tp2_price,
               lot_size, risk_amount, risk_reward_ratio, status, exit_price,
               realized_pnl, realized_pnl_pct, entry_date, exit_date, notes,
               created_at, updated_at
        FROM candlify_trading_plans
    """
    params = {}
    if status_filter and status_filter.upper() != "ALL":
        query += " WHERE UPPER(status) = :status"
        params["status"] = status_filter.upper()

    query += " ORDER BY CASE WHEN status = 'HOLDING' THEN 1 WHEN status = 'ANTRI' THEN 2 ELSE 3 END, updated_at DESC"

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    # Live stock cache enrichment
    stock_map = {}
    try:
        from lib.screener import get_all_stocks_cached
        cached = get_all_stocks_cached() or []
        for s in cached:
            stock_map[s["symbol"]] = s
    except Exception as e:
        logger.warning(f"Gagal memuat cache screener untuk trading plan: {e}")

    items = []
    for r in rows:
        sym = r["symbol"]
        live = stock_map.get(sym, {})
        curr_price = live.get("price") or r["entry_price"]
        entry_price = r["entry_price"] or 1.0
        sl_price = r["sl_price"] or entry_price
        tp1_price = r["tp1_price"] or entry_price
        lot_size = r["lot_size"] or 0
        total_shares = lot_size * 100
        status_val = r["status"] or "ANTRI"

        # Perhitungan Live PnL & Status Signals
        unrealized_pnl = 0.0
        unrealized_pnl_pct = 0.0
        tp1_hit = False
        tp2_hit = False
        sl_hit = False
        distance_to_entry_pct = 0.0

        if status_val == "HOLDING":
            unrealized_pnl = round((curr_price - entry_price) * total_shares, 2)
            unrealized_pnl_pct = round(((curr_price - entry_price) / entry_price) * 100.0, 2)
            tp1_hit = curr_price >= tp1_price if tp1_price else False
            tp2_hit = curr_price >= r["tp2_price"] if r.get("tp2_price") else False
            sl_hit = curr_price <= sl_price if sl_price else False
        elif status_val == "ANTRI":
            distance_to_entry_pct = round(((curr_price - entry_price) / entry_price) * 100.0, 2)

        items.append({
            "id": r["id"],
            "symbol": sym,
            "category": r["category"] or "Breakout",
            "order_type": r["order_type"] or "LIMIT",
            "entry_price": r["entry_price"],
            "sl_price": r["sl_price"],
            "tp1_price": r["tp1_price"],
            "tp2_price": r["tp2_price"],
            "lot_size": lot_size,
            "total_shares": total_shares,
            "total_invested": round(entry_price * total_shares, 2),
            "risk_amount": r["risk_amount"],
            "risk_reward_ratio": r["risk_reward_ratio"],
            "status": status_val,
            "exit_price": r["exit_price"],
            "realized_pnl": r["realized_pnl"],
            "realized_pnl_pct": r["realized_pnl_pct"],
            "entry_date": r["entry_date"].isoformat() if r["entry_date"] else None,
            "exit_date": r["exit_date"].isoformat() if r["exit_date"] else None,
            "notes": r["notes"] or "",
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            "updated_at": r["updated_at"].isoformat() if r["updated_at"] else None,
            # Live Data
            "current_price": curr_price,
            "change_pct": live.get("change_pct", 0.0),
            "name": live.get("name", sym),
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "tp1_hit": tp1_hit,
            "tp2_hit": tp2_hit,
            "sl_hit": sl_hit,
            "distance_to_entry_pct": distance_to_entry_pct
        })

    return items


def create_trading_plan(
    symbol: str,
    entry_price: float,
    sl_price: float,
    tp1_price: float,
    tp2_price: Optional[float] = None,
    lot_size: Optional[int] = None,
    category: str = "Breakout",
    order_type: str = "LIMIT",
    status: str = "ANTRI",
    notes: str = ""
) -> Dict[str, Any]:
    """Buat rencana trading baru dengan auto position-sizing."""
    clean_sym = clean_symbol(symbol)
    if entry_price <= 0:
        raise ValueError("Harga entry harus lebih besar dari 0")
    if sl_price <= 0:
        raise ValueError("Harga stop loss harus lebih besar dari 0")
    if sl_price >= entry_price:
        raise ValueError("Harga stop loss harus lebih rendah dari harga entry")
    if tp1_price <= entry_price:
        raise ValueError("Harga TP1 harus lebih tinggi dari harga entry")

    risk_per_share = entry_price - sl_price
    reward_per_share = tp1_price - entry_price
    rr_ratio = round(reward_per_share / risk_per_share, 2) if risk_per_share > 0 else 1.0

    if not lot_size or lot_size <= 0:
        settings = get_risk_settings()
        max_risk_rp = float(settings.get("risk_nominal") or 1000000.0)
        total_capital = float(settings.get("total_capital") or 100000000.0)
        max_exposure_pct = float(settings.get("max_exposure_pct") or 0.20)

        # 1. Risk-based allocation
        calc_lots = int(max_risk_rp / (risk_per_share * 100)) if risk_per_share > 0 else 1

        # 2. Maximum capital exposure cap (default max 20% total equity per stock untuk proteksi gap-down ARB)
        max_exposure_rp = total_capital * max_exposure_pct
        cap_lots = int(max_exposure_rp / (entry_price * 100)) if entry_price > 0 else calc_lots

        # Dual-constraint: ambil yang terkecil antara toleransi risiko vs plafon eksposur
        lot_size = max(1, min(calc_lots, cap_lots))

    risk_amount = round(risk_per_share * lot_size * 100, 2)

    engine = get_engine()
    query = """
        INSERT INTO candlify_trading_plans (
            symbol, category, order_type, entry_price, sl_price, tp1_price, tp2_price,
            lot_size, risk_amount, risk_reward_ratio, status, notes,
            entry_date, created_at, updated_at
        ) VALUES (
            :symbol, :category, :order_type, :entry_price, :sl_price, :tp1_price, :tp2_price,
            :lot_size, :risk_amount, :risk_reward_ratio, :status, :notes,
            CASE WHEN :status = 'HOLDING' THEN CURRENT_TIMESTAMP ELSE NULL END,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        RETURNING id, symbol, category, order_type, entry_price, sl_price, tp1_price, tp2_price,
                  lot_size, risk_amount, risk_reward_ratio, status, notes, created_at
    """
    with engine.begin() as conn:
        row = conn.execute(
            text(query),
            {
                "symbol": clean_sym,
                "category": category or "Breakout",
                "order_type": order_type.upper() if order_type else "LIMIT",
                "entry_price": float(entry_price),
                "sl_price": float(sl_price),
                "tp1_price": float(tp1_price),
                "tp2_price": float(tp2_price) if tp2_price else None,
                "lot_size": int(lot_size),
                "risk_amount": risk_amount,
                "risk_reward_ratio": rr_ratio,
                "status": status.upper() if status else "ANTRI",
                "notes": notes or ""
            }
        ).mappings().one()

    return {
        "success": True,
        "message": f"Trading plan {clean_sym} berhasil dibuat ({lot_size} Lot, R:R 1:{rr_ratio})",
        "data": dict(row)
    }


def update_trading_plan(plan_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update atribut trading plan (status, trailing stop, TP, exit, atau notes)."""
    engine = get_engine()
    with engine.connect() as conn:
        curr = conn.execute(
            text("SELECT * FROM candlify_trading_plans WHERE id = :id"),
            {"id": plan_id}
        ).mappings().one_or_none()

    if not curr:
        raise ValueError(f"Trading plan ID {plan_id} tidak ditemukan")

    sql_parts = []
    params = {"id": plan_id}

    # Nilai dasar untuk kalkulasi ulang risk & RR
    new_entry = float(updates["entry_price"]) if "entry_price" in updates and updates["entry_price"] is not None else float(curr["entry_price"])
    new_sl = float(updates["sl_price"]) if "sl_price" in updates and updates["sl_price"] is not None else (float(curr["sl_price"]) if curr.get("sl_price") is not None else None)
    new_tp1 = float(updates["tp1_price"]) if "tp1_price" in updates and updates["tp1_price"] is not None else (float(curr["tp1_price"]) if curr.get("tp1_price") is not None else None)
    new_lot = int(updates["lot_size"]) if "lot_size" in updates and updates["lot_size"] is not None else int(curr["lot_size"] or 0)

    if "entry_price" in updates and updates["entry_price"] is not None:
        if new_entry <= 0:
            raise ValueError("Harga entry harus lebih besar dari 0")
        sql_parts.append("entry_price = :entry_price")
        params["entry_price"] = new_entry

    if "sl_price" in updates and updates["sl_price"] is not None:
        if new_sl <= 0:
            raise ValueError("Harga stop loss harus lebih besar dari 0")
        sql_parts.append("sl_price = :sl_price")
        params["sl_price"] = new_sl

    if "tp1_price" in updates and updates["tp1_price"] is not None:
        sql_parts.append("tp1_price = :tp1_price")
        params["tp1_price"] = new_tp1

    if "tp2_price" in updates:
        sql_parts.append("tp2_price = :tp2_price")
        params["tp2_price"] = float(updates["tp2_price"]) if updates["tp2_price"] is not None else None

    if "lot_size" in updates and updates["lot_size"] is not None:
        sql_parts.append("lot_size = :lot_size")
        params["lot_size"] = new_lot

    if "category" in updates and updates["category"] is not None:
        sql_parts.append("category = :category")
        params["category"] = updates["category"].strip()

    if "order_type" in updates and updates["order_type"] is not None:
        sql_parts.append("order_type = :order_type")
        params["order_type"] = updates["order_type"].strip().upper()

    if "entry_date" in updates:
        sql_parts.append("entry_date = :entry_date")
        params["entry_date"] = updates["entry_date"]

    if "notes" in updates:
        sql_parts.append("notes = :notes")
        params["notes"] = updates["notes"] or ""

    # Kalkulasi ulang risk_amount dan risk_reward_ratio jika ada perubahan entry, SL, TP1, atau Lot
    if any(k in updates for k in ["entry_price", "sl_price", "tp1_price", "lot_size"]):
        if new_sl is not None and new_entry > new_sl:
            risk_per_share = new_entry - new_sl
            risk_amt = round(risk_per_share * new_lot * 100, 2)
            sql_parts.append("risk_amount = :risk_amount")
            params["risk_amount"] = risk_amt

            if new_tp1 is not None and new_tp1 > new_entry:
                rr = round((new_tp1 - new_entry) / risk_per_share, 2)
                sql_parts.append("risk_reward_ratio = :risk_reward_ratio")
                params["risk_reward_ratio"] = rr

    if "status" in updates and updates["status"]:
        new_status = updates["status"].upper()
        sql_parts.append("status = :status")
        params["status"] = new_status

        if new_status == "HOLDING" and curr["status"] != "HOLDING" and not curr["entry_date"] and "entry_date" not in updates:
            sql_parts.append("entry_date = CURRENT_TIMESTAMP")

        if new_status in ("CLOSED", "CLOSED_WIN", "CLOSED_LOSS", "CLOSED_BEP") or new_status.startswith("CLOSED"):
            exit_price = float(updates.get("exit_price") or curr.get("exit_price") or new_entry)
            shares = new_lot * 100
            realized_pnl = round((exit_price - new_entry) * shares, 2)
            realized_pnl_pct = round(((exit_price - new_entry) / new_entry) * 100.0, 2)

            sql_parts.append("exit_price = :exit_price")
            sql_parts.append("realized_pnl = :realized_pnl")
            sql_parts.append("realized_pnl_pct = :realized_pnl_pct")
            if updates.get("exit_date"):
                sql_parts.append("exit_date = :exit_date")
                params["exit_date"] = updates["exit_date"]
            else:
                sql_parts.append("exit_date = CURRENT_TIMESTAMP")
            params["exit_price"] = exit_price
            params["realized_pnl"] = realized_pnl
            params["realized_pnl_pct"] = realized_pnl_pct

    if not sql_parts:
        return {"success": True, "message": "Tidak ada perubahan", "data": dict(curr)}

    sql_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE candlify_trading_plans SET {', '.join(sql_parts)} WHERE id = :id RETURNING *"

    with engine.begin() as conn:
        updated_row = conn.execute(text(sql), params).mappings().one()

    return {
        "success": True,
        "message": f"Trading plan {curr['symbol']} berhasil diperbarui",
        "data": dict(updated_row)
    }


def delete_trading_plan(plan_id: int) -> Dict[str, Any]:
    """Hapus trading plan dari Neon DB."""
    engine = get_engine()
    with engine.begin() as conn:
        res = conn.execute(
            text("DELETE FROM candlify_trading_plans WHERE id = :id RETURNING symbol"),
            {"id": plan_id}
        ).fetchone()

    if not res:
        raise ValueError(f"Trading plan ID {plan_id} tidak ditemukan")

    return {
        "success": True,
        "message": f"Trading plan {res[0]} berhasil dihapus"
    }


def get_trading_plan_stats() -> Dict[str, Any]:
    """Ambil ringkasan performa trading plan dan portofolio swing."""
    all_plans = get_all_trading_plans()
    holding = [p for p in all_plans if p["status"] == "HOLDING"]
    antri = [p for p in all_plans if p["status"] == "ANTRI"]
    closed = [p for p in all_plans if "CLOSED" in p["status"]]

    total_unrealized_pnl = sum(p.get("unrealized_pnl", 0.0) for p in holding)
    total_invested_holding = sum(p.get("total_invested", 0.0) for p in holding)
    total_realized_pnl = sum(p.get("realized_pnl", 0.0) for p in closed if p.get("realized_pnl") is not None)

    wins = [p for p in closed if p["status"] == "CLOSED_WIN" or (p.get("realized_pnl") or 0) > 0]
    win_rate = round((len(wins) / len(closed)) * 100.0, 1) if closed else 0.0

    tp1_hits = [p for p in holding if p.get("tp1_hit")]

    return {
        "success": True,
        "holding_count": len(holding),
        "antri_count": len(antri),
        "closed_count": len(closed),
        "total_invested_holding": total_invested_holding,
        "total_unrealized_pnl": total_unrealized_pnl,
        "total_realized_pnl": total_realized_pnl,
        "win_rate": win_rate,
        "tp1_hits_count": len(tp1_hits)
    }



