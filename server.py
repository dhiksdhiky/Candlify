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

import logging
from typing import Optional, List
from fastapi import FastAPI, Query, Header, Response, HTTPException, status, File, UploadFile, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

logger = logging.getLogger("CandlifyServer")

# Pastikan path import v2 terbaca
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from pydantic import BaseModel, Field
from lib.history import get_candlesticks
from lib.bandarmologi import (
    get_bandarmologi,
    get_broksum_range,
    get_historical_price_table,
    get_broker_daily_activity,
    get_broker_flow,
    get_stock_market_intelligence
)
from lib.screener import get_screened_stocks, get_pre_breakout_signals, get_stock_board_map
from lib.database_monitor import get_database_metrics, process_saham_excel, get_calendar_history
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

is_prod = os.getenv("ENV", "").lower() == "production" or os.getenv("DISABLE_DOCS", "false").lower() == "true"
app = FastAPI(
    title="Candlify v2 API",
    version="2.0.0",
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
    openapi_url=None if is_prod else "/openapi.json"
)

# ── Security & Mutation Auth Dependency ──────────────────────
def verify_mutation_auth(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
):
    """
    Guard autentikasi sederhana untuk endpoint mutasi (POST, PUT, DELETE) & upload data.
    Jika CANDLIFY_API_KEY diset di environment, request wajib menyertakan API Key
    via header 'X-API-Key' atau 'Authorization: Bearer <token>'.
    Jika tidak diset (default lokal / personal dev), request langsung diizinkan.
    """
    expected = os.getenv("CANDLIFY_API_KEY", "").strip()
    if not expected:
        return True

    token = (x_api_key or "").strip()
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Akses ditolak: API Key tidak valid atau belum disertakan."
        )
    return True

# 1. GZip Compression Middleware (P1 #10)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 2. CORS Middleware (Sanitized & Configurable)
cors_env = os.getenv("CORS_ORIGINS", "*").strip()
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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

    b_map = get_stock_board_map()
    sym_clean = result.get("symbol", "").upper()
    board_val = b_map.get(sym_clean, "Pengembangan")
    result["board"] = board_val
    result["is_fca"] = ("Pemantauan" in board_val)

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

    b_map = get_stock_board_map()
    sym_clean = result.get("symbol", "").upper()
    board_val = b_map.get(sym_clean, "Pengembangan")
    result["board"] = board_val
    result["is_fca"] = ("Pemantauan" in board_val)

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

@app.get("/api/stock/historical-data")
def api_stock_historical_data(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, PGJO)"),
    timeframe: str = Query("daily", description="Timeframe: daily, weekly, monthly"),
    limit: int = Query(60, ge=1, le=200, description="Jumlah baris data")
):
    """
    Endpoint Tabel Riwayat Harga Saham & Turnover (Gambar 3 Stockbit):
    Date | Close | Change | Value (Turnover).
    """
    try:
        result = get_historical_price_table(symbol=symbol, timeframe=timeframe, limit=limit)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data historis tidak ditemukan"))

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return result

@app.get("/api/bandarmologi/broker-activity")
def api_broker_activity(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, PGJO)"),
    broker: Optional[str] = Query(None, description="Kode broker sekuritas (e.g. XL, CC, YP)"),
    broker_code: Optional[str] = Query(None, description="Alias untuk broker"),
    month: Optional[str] = Query(None, description="Bulan (YYYY-MM), e.g. 2026-10")
):
    """
    Endpoint Kalender Aktivitas Harian Broker Spesifik (Gambar 2 Stockbit):
    Menampilkan jejak beli/jual, lot, avg price, dan status per tanggal bursa.
    """
    target_broker = (broker_code or broker or "XL").strip().upper()
    try:
        result = get_broker_daily_activity(symbol=symbol, broker_code=target_broker, month_str=month)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data aktivitas broker tidak ditemukan"))

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return result

@app.get("/api/bandarmologi/broker-flow")
def api_broker_flow(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, PGJO)"),
    days: int = Query(30, ge=5, le=180, description="Jumlah hari bursa lookback"),
    metric: str = Query("val", description="Metrik: 'val' (Rupiah) atau 'vol' (Lot)"),
    brokers: Optional[str] = Query(None, description="Kode broker koma-terpisah e.g. CC,YU,XL,MG,SQ")
):
    """
    Endpoint Garis Visualisasi Akumulasi/Distribusi Multi-Broker (Gambar 1 Stockbit):
    Menghitung saldo flow kumulatif per tanggal untuk perbandingan visual.
    """
    try:
        broker_list = [b.strip().upper() for b in brokers.split(",") if b.strip()] if brokers else None
        result = get_broker_flow(symbol=symbol, days=days, metric=metric, broker_list=broker_list)
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {err}")

    if not result.get("success", False):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error", "Data broker flow tidak ditemukan"))

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=300"
    return result

@app.get("/api/bandarmologi/intelligence")
def api_market_intelligence(
    response: Response,
    symbol: str = Query(..., description="Kode saham (e.g. BBRI, GOTO)")
):
    """
    Endpoint Market Intelligence BEI (Official IDX Data):
    - Foreign Flow (1D, 5D, 20D)
    - Trade Size (Whale vs Ritel)
    - Pasar Nego (Crossing Saham)
    - Notasi Khusus BEI & Tradeable Shares
    """
    try:
        result = get_stock_market_intelligence(symbol=symbol)
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Intelligence Error: {err}")

    response.headers["Cache-Control"] = "public, s-maxage=60, stale-while-revalidate=120"
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

@app.get("/api/screener/pre-breakout")
def api_screener_pre_breakout(
    response: Response,
    date: Optional[str] = Query(None, description="Tanggal sinyal (YYYY-MM-DD), default tanggal terbaru"),
    min_score: int = Query(60, ge=0, le=100, description="Minimum skor kualitas sinyal (0-100)"),
    limit: int = Query(50, ge=1, le=200, description="Jumlah maksimal sinyal")
):
    """
    Endpoint Sinyal Pre-Breakout Base:
    Mendeteksi saham yang sedang konsolidasi ketat dengan volume kering
    dan konfirmasi akumulasi broker summary (Smart Money/HMB).
    """
    try:
        result = get_pre_breakout_signals(target_date=date, min_score=min_score, limit=limit)
    except Exception as err:
        logger.error(f"Error in api_screener_pre_breakout: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Pre-breakout error: {err}")

    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Gagal memuat sinyal pre-breakout dari database")
        )

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

@app.post("/api/watchlist", dependencies=[Depends(verify_mutation_auth)])
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
        logger.error(f"Error in api_add_watchlist: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menambahkan ke watchlist")

@app.put("/api/watchlist/{item_id}", dependencies=[Depends(verify_mutation_auth)])
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
        logger.error(f"Error in api_update_watchlist: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memperbarui watchlist")

@app.delete("/api/watchlist/{item_id}", dependencies=[Depends(verify_mutation_auth)])
def api_delete_watchlist(item_id: int):
    """Hapus saham dari watchlist."""
    try:
        res = delete_from_watchlist(item_id=item_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_delete_watchlist: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menghapus watchlist")

# ── Watchlist Categories Endpoints ────────────────────────────

@app.get("/api/watchlist/categories")
def api_get_categories():
    """Ambil daftar kategori watchlist aktif."""
    try:
        cats = get_watchlist_categories()
        return {"success": True, "categories": cats}
    except Exception as err:
        logger.error(f"Error in api_get_categories: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat kategori")

@app.post("/api/watchlist/categories", dependencies=[Depends(verify_mutation_auth)])
def api_add_category(payload: CategoryCreateReq):
    """Tambah kategori watchlist baru."""
    try:
        cats = add_watchlist_category(payload.name)
        return {"success": True, "categories": cats, "message": f"Kategori '{payload.name}' berhasil ditambahkan"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_add_category: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menambahkan kategori")

@app.put("/api/watchlist/categories/{name}", dependencies=[Depends(verify_mutation_auth)])
def api_rename_category(name: str, payload: CategoryRenameReq):
    """Ubah nama kategori watchlist."""
    try:
        cats = rename_watchlist_category(name, payload.new_name)
        return {"success": True, "categories": cats, "message": f"Kategori berhasil diubah menjadi '{payload.new_name}'"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_rename_category: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal mengubah kategori")

@app.delete("/api/watchlist/categories/{name}", dependencies=[Depends(verify_mutation_auth)])
def api_delete_category(name: str):
    """Hapus kategori watchlist dan fallback saham ke Breakout."""
    try:
        cats = delete_watchlist_category(name)
        return {"success": True, "categories": cats, "message": f"Kategori '{name}' berhasil dihapus (saham dipindahkan ke Breakout)"}
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_delete_category: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menghapus kategori")

# ── Stock Multi-Watchlist Sync Endpoints ──────────────────────

@app.get("/api/watchlist/stock/{symbol}")
def api_get_stock_watchlists(symbol: str):
    """Ambil seluruh kategori watchlist aktif untuk suatu saham tertentu."""
    try:
        data = get_stock_watchlists(symbol)
        return data
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal memuat status watchlist saham: {err}")

@app.post("/api/watchlist/sync-stock", dependencies=[Depends(verify_mutation_auth)])
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
        logger.error(f"Error in api_sync_stock_watchlists: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal sinkronisasi watchlist")

# ── User Risk Settings Endpoints ──────────────────────────────

@app.get("/api/settings/risk")
def api_get_risk_settings():
    """Ambil pengaturan modal & toleransi risiko akun."""
    try:
        settings = get_risk_settings()
        return {"success": True, "data": settings}
    except Exception as err:
        logger.error(f"Error in api_get_risk_settings: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat settings")

@app.post("/api/settings/risk", dependencies=[Depends(verify_mutation_auth)])
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
        logger.error(f"Error in api_save_risk_settings: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menyimpan settings")

# ── Trading Plan & Journal Endpoints ─────────────────────────

@app.get("/api/trading-plans")
def api_get_trading_plans(status_param: Optional[str] = Query(None, alias="status", description="Filter status: ALL, ANTRI, HOLDING, CLOSED")):
    """Ambil seluruh trading plan dengan status live."""
    try:
        items = get_all_trading_plans(status_filter=status_param)
        return {"success": True, "count": len(items), "data": items}
    except Exception as err:
        logger.error(f"Error in api_get_trading_plans: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat trading plan")

@app.get("/api/trading-plans/stats")
def api_get_trading_plan_stats():
    """Ambil ringkasan performa dan portofolio swing trading."""
    try:
        stats_data = get_trading_plan_stats()
        return stats_data
    except Exception as err:
        logger.error(f"Error in api_get_trading_plan_stats: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat statistik trading plan")

@app.post("/api/trading-plans", dependencies=[Depends(verify_mutation_auth)])
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
        logger.error(f"Error in api_create_trading_plan: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal membuat trading plan")

@app.put("/api/trading-plans/{plan_id}", dependencies=[Depends(verify_mutation_auth)])
def api_update_trading_plan(plan_id: int, payload: PlanUpdateReq):
    """Update trading plan (status, trailing stop, TP, exit, atau catatan)."""
    try:
        updates = payload.model_dump(exclude_unset=True)
        res = update_trading_plan(plan_id=plan_id, updates=updates)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_update_trading_plan: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memperbarui trading plan")

@app.delete("/api/trading-plans/{plan_id}", dependencies=[Depends(verify_mutation_auth)])
def api_delete_trading_plan(plan_id: int):
    """Hapus trading plan."""
    try:
        res = delete_trading_plan(plan_id=plan_id)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_delete_trading_plan: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal menghapus trading plan")

# ── Database & Glory Engine Monitor Endpoints ───────────────

@app.get("/api/database/health")
def api_database_health(month: Optional[str] = None):
    """Ambil status kesehatan, total baris emiten, dan riwayat sinkronisasi Neon DB."""
    try:
        metrics = get_database_metrics(target_month=month)
        return metrics
    except Exception as err:
        logger.error(f"Error in api_database_health: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat status database")

@app.get("/api/database/calendar")
def api_database_calendar(month: str = Query(...)):
    """Ambil data riwayat sinkronisasi kalender per bulan (YYYY-MM)."""
    try:
        return get_calendar_history(month_str=month)
    except Exception as err:
        logger.error(f"Error in api_database_calendar: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memuat kalender")

@app.post("/api/database/upload", dependencies=[Depends(verify_mutation_auth)])
def api_database_upload(file: UploadFile = File(...)):
    """Upload dan replace master data emiten dari file Excel IDX (.xlsx)."""
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File harus berformat Excel (.xlsx)")
    try:
        contents = file.file.read()
        res = process_saham_excel(excel_bytes=contents, filename=file.filename)
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as err:
        logger.error(f"Error in api_database_upload: {err}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal memproses file Excel")

@app.get("/api/stock")
def api_stock_alias(action: Optional[str] = Query("health")):
    """Alias endpoint kompatibilitas stock engine."""
    return get_database_metrics()

@app.get("/api/docs")
def api_list_docs():
    """Mengembalikan daftar semua dokumen panduan di folder docs/ secara dinamis."""
    docs_dir = os.path.join(BASE_DIR, "docs")
    if not os.path.exists(docs_dir):
        return {"success": True, "total": 0, "docs": []}

    files = [f for f in sorted(os.listdir(docs_dir)) if f.endswith(".md")]
    docs_list = []
    
    for f in files:
        file_path = os.path.join(docs_dir, f)
        title = f.replace(".md", "").replace("_", " ")
        subtitle = "Dokumentasi & Panduan Resmi Candlify"
        icon = "📖"
        
        try:
            with open(file_path, "r", encoding="utf-8") as doc_f:
                lines = doc_f.readlines()
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith("# "):
                        raw_title = line_str[2:].strip()
                        parts = raw_title.split(" ", 1)
                        if len(parts) > 1 and any(ord(c) > 127 for c in parts[0]):
                            icon = parts[0]
                            title = parts[1]
                        else:
                            title = raw_title
                        break
                        
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith(">"):
                        cleaned = line_str.replace(">", "").replace("**", "").replace("*", "").strip()
                        if cleaned:
                            subtitle = cleaned.split("—")[0].strip() if "—" in cleaned else cleaned[:100]
                            break
        except Exception as err:
            logger.warning(f"Gagal membaca metadata {f}: {err}")

        slug = f.replace(".md", "").lower()
        docs_list.append({
            "filename": f,
            "slug": slug,
            "title": title,
            "subtitle": subtitle,
            "icon": icon,
        })
        
    return {"success": True, "total": len(docs_list), "docs": docs_list}

@app.get("/api/docs/bandarmology")
def api_get_bandarmology_doc():
    """Mengembalikan isi dokumen panduan Pre-Breakout & Bandarmologi dalam format Markdown (Legacy)."""
    doc_path = os.path.join(BASE_DIR, "docs", "BANDARMOLOGY_PRE_BREAKOUT.md")
    if not os.path.exists(doc_path):
        raise HTTPException(status_code=404, detail="Dokumen panduan tidak ditemukan")
    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "success": True,
            "title": "Buku Panduan Pre-Breakout & Bandarmology",
            "markdown": content
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Gagal membaca dokumen: {err}")

@app.get("/api/docs/{slug}")
def api_get_doc_by_slug(slug: str):
    """Mengembalikan isi dokumen markdown berdasarkan slug atau filename."""
    docs_dir = os.path.join(BASE_DIR, "docs")
    if not os.path.exists(docs_dir):
        raise HTTPException(status_code=404, detail="Folder docs tidak ditemukan")

    target_file = None
    slug_lower = slug.lower().strip()
    for f in os.listdir(docs_dir):
        if not f.endswith(".md"):
            continue
        base_name = f.replace(".md", "").lower()
        if base_name == slug_lower or f.lower() == slug_lower:
            target_file = f
            break

    if not target_file:
        raise HTTPException(status_code=404, detail=f"Dokumen '{slug}' tidak ditemukan")

    file_path = os.path.join(docs_dir, target_file)
    try:
        with open(file_path, "r", encoding="utf-8") as doc_f:
            content = doc_f.read()
            
        title = target_file.replace(".md", "").replace("_", " ")
        icon = "📖"
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("# "):
                raw_title = line_str[2:].strip()
                parts = raw_title.split(" ", 1)
                if len(parts) > 1 and any(ord(c) > 127 for c in parts[0]):
                    icon = parts[0]
                    title = parts[1]
                else:
                    title = raw_title
                break

        return {
            "success": True,
            "filename": target_file,
            "slug": slug_lower,
            "title": title,
            "icon": icon,
            "markdown": content
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Gagal membaca file dokumen: {err}")

@app.get("/api/health")
def health():
    db_status = "unconfigured"
    try:
        from lib.db import get_db_engine
        engine = get_db_engine()
        if engine:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "connected"
        else:
            db_status = "no_url"
    except Exception as err:
        db_status = f"error: {str(err)[:60]}"

    from lib.utils import now_wib
    return {
        "status": "ok" if db_status in ("connected", "unconfigured") else "degraded",
        "version": "v2-lean",
        "engine": "Candlify Unified Hardened",
        "database": db_status,
        "timestamp": now_wib().isoformat()
    }

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
