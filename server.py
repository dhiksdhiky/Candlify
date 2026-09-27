"""
v2/server.py — Candlify v2 Fast, Lean & Non-Blocking Server
===========================================================
Fixes:
- P0 #1: Synchronous def endpoint (FastAPI runs on internal worker threadpool, zero event-loop blocking)
- P0 #4: Stockbit token read from Authorization header / X-Stockbit-Token (not leaking in URL)
- P1 #5: Vercel CDN Caching (Cache-Control: public, s-maxage=60, stale-while-revalidate=300)
- P1 #10: GZip Compression for fast candle transfer
- CORS sanitized (no conflicting allow_credentials with wildcard origin)
"""

import os
import sys

# Windows console UTF-8 safety
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from typing import Optional, List
from fastapi import FastAPI, Query, Header, Response, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

# Pastikan path import v2 terbaca
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from typing import Optional
from pydantic import BaseModel, Field
from lib.history import get_candlesticks
from lib.bandarmologi import get_bandarmologi, get_broksum_range
from lib.screener import get_screened_stocks
from lib.portfolio import (
    get_all_watchlists,
    add_to_watchlist,
    update_watchlist_item,
    delete_from_watchlist,
    get_risk_settings,
    save_risk_settings,
    get_watchlist_categories,
    add_watchlist_category,
    rename_watchlist_category,
    delete_watchlist_category,
    get_stock_watchlists,
    sync_stock_watchlists,
    get_all_trading_plans,
    create_trading_plan,
    update_trading_plan,
    delete_trading_plan,
    get_trading_plan_stats
)

# ── Pydantic Request Models ──────────────────────────────────
class WatchlistCreateReq(BaseModel):
    symbol: str
    category: Optional[str] = "Breakout"
    notes: Optional[str] = ""
    target_entry: Optional[float] = None

class WatchlistUpdateReq(BaseModel):
    notes: Optional[str] = None
    target_entry: Optional[float] = None
    category: Optional[str] = None

class StockWatchlistSyncReq(BaseModel):
    symbol: str
    categories: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    target_entry: Optional[float] = None

class CategoryCreateReq(BaseModel):
    name: str

class CategoryRenameReq(BaseModel):
    new_name: str

class RiskSettingsReq(BaseModel):
    total_capital: float = Field(..., gt=0)
    risk_pct: float = Field(..., gt=0, le=100)
    default_category: Optional[str] = "Breakout"
    daily_source: Optional[str] = "neon_db"

class PlanCreateReq(BaseModel):
    symbol: str
    entry_price: float = Field(..., gt=0)
    sl_price: float = Field(..., gt=0)
    tp1_price: float = Field(..., gt=0)
    tp2_price: Optional[float] = None
    lot_size: Optional[int] = None
    category: Optional[str] = "Breakout"
    order_type: Optional[str] = "LIMIT"
    status: Optional[str] = "ANTRI"
    notes: Optional[str] = ""

class PlanUpdateReq(BaseModel):
    entry_price: Optional[float] = None
    sl_price: Optional[float] = None
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    lot_size: Optional[int] = None
    category: Optional[str] = None
    order_type: Optional[str] = None
    status: Optional[str] = None
    entry_date: Optional[str] = None
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    notes: Optional[str] = None

app = FastAPI(title="Candlify v2 API", version="2.0.0")

# 1. GZip Compression Middleware (P1 #10)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. CORS Middleware (Sanitized)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── API Routes ───────────────────────────────────────────────

# P0 #1: Pakai synchronous `def` alih-alih `async def` agar dieksekusi di threadpool
# dan TIDAK PERNAH memblokir asyncio main event loop saat Yahoo/DB lambat!
@app.get("/api/history")
def api_history(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, TLKM, ASII)"),
    interval: str = Query("4h", description="Timeframe (5m, 15m, 1h, 4h, 1d, 1w)"),
    range: Optional[str] = Query(None, description="Rentang data opsional (e.g. 1mo, 1y)"),
    source: Optional[str] = Query(None, description="Pilihan sumber data: 'neon_db' atau 'yahoo'"),
    authorization: Optional[str] = Header(None, description="Bearer token Stockbit"),
    x_stockbit_token: Optional[str] = Header(None, description="Alternatif header token Stockbit"),
    stockbit_token: Optional[str] = Query(None, description="Fallback query param token Stockbit")
):
    """
    Endpoint Candlestick Multi-Timeframe KLineCharts:
    - Non-blocking (Threadpool)
    - CDN Caching (Cache-Control headers)
    - Token secure (Header Authorization)
    """
    # P0 #4: Ekstrak token dari header lebih dahulu untuk keamanan
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
    elif x_stockbit_token:
        token = x_stockbit_token.strip()
    elif stockbit_token:
        token = stockbit_token.strip()

    try:
        result = get_candlesticks(
            symbol=symbol,
            interval=interval,
            range_val=range,
            stockbit_token=token,
            source=source
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data tidak ditemukan"))

    # P1 #5: Pasang Cache-Control untuk Vercel Edge / CDN Caching
    # Jika data stale, TTL CDN 10 detik. Jika fresh, s-maxage=60s dan stale-while-revalidate=300s
    if result.get("stale"):
        response.headers["Cache-Control"] = "public, s-maxage=10, max-age=10"
        response.headers["X-Data-Status"] = "stale"
    else:
        response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
        response.headers["X-Data-Status"] = "fresh"

    return result

@app.get("/api/bandarmologi")
def api_bandarmologi(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, TLKM, ASII)"),
    days: int = Query(180, description="Rentang hari kalender lookback")
):
    """
    Endpoint Bandarmologi KLineCharts:
    - HMB (Harga Modal Bandar)
    - Net Flow Bandar (Top 3 Buyers vs Top 3 Sellers)
    - Top Accumulators breakdown
    - Available date range
    """
    try:
        result = get_bandarmologi(symbol=symbol, days_lookback=days)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data broker summary tidak ditemukan"))

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return result

@app.get("/api/bandarmologi/broksum")
def api_bandarmologi_broksum(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, TLKM, ASII)"),
    from_date: Optional[str] = Query(None, description="Tanggal mulai (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="Tanggal akhir (YYYY-MM-DD)")
):
    """
    Endpoint Detail Broker Summary Teragregasi untuk Rentang Tanggal Tertentu:
    Mendukung filter dinamis (1D, 1W, 2W, 1M, 3M, 6M, atau custom date range).
    """
    try:
        result = get_broksum_range(symbol=symbol, from_date=from_date, to_date=to_date)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data broker summary tidak ditemukan"))

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return result

@app.get("/api/screen")
def api_screen(
    response: Response,
    preset: Optional[str] = Query("all", description="Filter preset: all, swing, breakout, vol_bb, oversold, bigcap"),
    search: Optional[str] = Query(None, description="Cari ticker atau nama perusahaan"),
    sort: Optional[str] = Query("change_desc", description="Sorting: change_desc, change_asc, volume_desc, market_cap_desc, surge_desc, price_desc")
):
    """
    Endpoint Screener Seluruh Saham BEI (880+ Emiten):
    Mendukung filter preset strategi, pencarian real-time, dan sorting.
    Super cepat & hemat kuota (< 1ms via cache in-memory).
    """
    try:
        result = get_screened_stocks(preset=preset, search=search, sort=sort)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Screener Error: {err}")

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=120"
    return result

# ── Watchlist Endpoints (Neon PostgreSQL Cloud) ───────────────

@app.get("/api/watchlist")
def api_get_watchlist(
    category: Optional[str] = Query(None, description="Filter kategori watchlist (e.g. Breakout)")
):
    """Ambil daftar saham pantauan di watchlist lengkap dengan live data."""
    try:
        items = get_all_watchlists(category=category)
        return {"success": True, "count": len(items), "data": items}
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat watchlist: {err}")

@app.post("/api/watchlist")
def api_add_watchlist(payload: WatchlistCreateReq):
    """Tambah saham ke watchlist."""
    try:
        res = add_to_watchlist(
            symbol=payload.symbol,
            category=payload.category or "Breakout",
            notes=payload.notes or "",
            target_entry=payload.target_entry
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menambahkan ke watchlist: {err}")

@app.put("/api/watchlist/{item_id}")
def api_update_watchlist(item_id: int, payload: WatchlistUpdateReq):
    """Update catatan atau target entry watchlist item."""
    try:
        res = update_watchlist_item(
            item_id=item_id,
            notes=payload.notes,
            target_entry=payload.target_entry,
            category=payload.category
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memperbarui watchlist: {err}")

@app.delete("/api/watchlist/{item_id}")
def api_delete_watchlist(item_id: int):
    """Hapus saham dari watchlist."""
    try:
        res = delete_from_watchlist(item_id=item_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menghapus watchlist: {err}")

# ── Watchlist Categories Endpoints ────────────────────────────

@app.get("/api/watchlist/categories")
def api_get_categories():
    """Ambil daftar kategori watchlist aktif."""
    try:
        cats = get_watchlist_categories()
        return {"success": True, "categories": cats}
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat kategori: {err}")

@app.post("/api/watchlist/categories")
def api_add_category(payload: CategoryCreateReq):
    """Tambah kategori watchlist baru."""
    try:
        cats = add_watchlist_category(payload.name)
        return {"success": True, "categories": cats, "message": f"Kategori '{payload.name}' berhasil ditambahkan"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menambahkan kategori: {err}")

@app.put("/api/watchlist/categories/{name}")
def api_rename_category(name: str, payload: CategoryRenameReq):
    """Ubah nama kategori watchlist."""
    try:
        cats = rename_watchlist_category(name, payload.new_name)
        return {"success": True, "categories": cats, "message": f"Kategori berhasil diubah menjadi '{payload.new_name}'"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengubah kategori: {err}")

@app.delete("/api/watchlist/categories/{name}")
def api_delete_category(name: str):
    """Hapus kategori watchlist dan fallback saham ke Breakout."""
    try:
        cats = delete_watchlist_category(name)
        return {"success": True, "categories": cats, "message": f"Kategori '{name}' berhasil dihapus (saham dipindahkan ke Breakout)"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menghapus kategori: {err}")

# ── Stock Multi-Watchlist Sync Endpoints ──────────────────────

@app.get("/api/watchlist/stock/{symbol}")
def api_get_stock_watchlists(symbol: str):
    """Ambil seluruh kategori watchlist aktif untuk suatu saham tertentu."""
    try:
        data = get_stock_watchlists(symbol)
        return data
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat status watchlist saham: {err}")

@app.post("/api/watchlist/sync-stock")
def api_sync_stock_watchlists(payload: StockWatchlistSyncReq):
    """Sinkronisasi multi-watchlist untuk suatu saham."""
    try:
        res = sync_stock_watchlists(
            symbol=payload.symbol,
            categories=payload.categories,
            notes=payload.notes,
            target_entry=payload.target_entry
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal sinkronisasi watchlist: {err}")

# ── User Risk Settings Endpoints ──────────────────────────────

@app.get("/api/settings/risk")
def api_get_risk_settings():
    """Ambil pengaturan modal & toleransi risiko akun."""
    try:
        settings = get_risk_settings()
        return {"success": True, "data": settings}
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat settings: {err}")

@app.post("/api/settings/risk")
def api_save_risk_settings(payload: RiskSettingsReq):
    """Simpan pengaturan modal, toleransi risiko akun, dan data source."""
    try:
        res = save_risk_settings(
            total_capital=payload.total_capital,
            risk_pct=payload.risk_pct,
            default_category=payload.default_category or "Breakout",
            daily_source=payload.daily_source or "neon_db"
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menyimpan settings: {err}")

# ── Trading Plan & Journal Endpoints ─────────────────────────

@app.get("/api/trading-plans")
def api_get_trading_plans(status_param: Optional[str] = Query(None, alias="status", description="Filter status: ALL, ANTRI, HOLDING, CLOSED")):
    """Ambil seluruh trading plan dengan status live."""
    try:
        items = get_all_trading_plans(status_filter=status_param)
        return {"success": True, "count": len(items), "data": items}
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat trading plan: {err}")

@app.get("/api/trading-plans/stats")
def api_get_trading_plan_stats():
    """Ambil ringkasan performa dan portofolio swing trading."""
    try:
        stats_data = get_trading_plan_stats()
        return stats_data
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat statistik trading plan: {err}")

@app.post("/api/trading-plans")
def api_create_trading_plan(payload: PlanCreateReq):
    """Buat trading plan baru dengan alokasi lot otomatis."""
    try:
        res = create_trading_plan(
            symbol=payload.symbol,
            entry_price=payload.entry_price,
            sl_price=payload.sl_price,
            tp1_price=payload.tp1_price,
            tp2_price=payload.tp2_price,
            lot_size=payload.lot_size,
            category=payload.category or "Breakout",
            order_type=payload.order_type or "LIMIT",
            status=payload.status or "ANTRI",
            notes=payload.notes or ""
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal membuat trading plan: {err}")

@app.put("/api/trading-plans/{plan_id}")
def api_update_trading_plan(plan_id: int, payload: PlanUpdateReq):
    """Update trading plan (status, trailing stop, TP, exit, atau catatan)."""
    try:
        updates = payload.model_dump(exclude_unset=True)
        res = update_trading_plan(plan_id=plan_id, updates=updates)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memperbarui trading plan: {err}")

@app.delete("/api/trading-plans/{plan_id}")
def api_delete_trading_plan(plan_id: int):
    """Hapus trading plan."""
    try:
        res = delete_trading_plan(plan_id=plan_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal menghapus trading plan: {err}")

@app.get("/api/health")
def health():
    return {"status": "ok", "version": "v2-lean", "engine": "Candlify Unified Hardened"}

# ── Mount Frontend Static Files ─────────────────────────────
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
if os.path.exists(PUBLIC_DIR):
    app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="public")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n=======================================================")
    print(f"🕯️ CANDLIFY v2 LEAN SERVER RUNNING")
    print(f"👉 Buka browser: http://localhost:{port}")
    print(f"=======================================================\n")
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True)
