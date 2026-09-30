"""
lib/utils.py — Shared Utilities, Validation, and Market-Hours Helpers
=====================================================================
Centralized helpers for timezone, market session detection, ticker sanitization,
and dynamic TTL calculations.
"""

import re
from datetime import datetime, timezone, timedelta

# ── Timezone & Market Hours Helper ────────────────────────────
WIB_TZ = timezone(timedelta(hours=7))  # Asia/Jakarta (UTC+7)

def now_wib() -> datetime:
    """Mengembalikan datetime terkini dalam zona waktu Asia/Jakarta (WIB)."""
    return datetime.now(WIB_TZ)

def is_idx_market_open() -> bool:
    """
    Cek apakah saat ini jam operasional Bursa Efek Indonesia.
    Jadwal perdagangan reguler BEI: Senin - Jumat 08:45 - 16:30 WIB.
    """
    now = now_wib()
    # 0 = Monday, 4 = Friday, 5 = Saturday, 6 = Sunday
    if now.weekday() > 4:
        return False
    current_minute = now.hour * 60 + now.minute
    market_open = 8 * 60 + 45    # 08:45 WIB
    market_close = 16 * 60 + 30  # 16:30 WIB
    return market_open <= current_minute <= market_close

def get_smart_ttl(interval: str) -> int:
    """Hitung TTL candlestick dinamis: pendek saat jam bursa, panjang saat bursa tutup."""
    if not is_idx_market_open():
        return 3600  # 1 jam saat bursa tutup / weekend

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

def get_bandar_ttl() -> int:
    """TTL cache bandarmologi: pendek saat jam bursa (2 menit), panjang di luar jam bursa (1 jam)."""
    return 120 if is_idx_market_open() else 3600

# ── Symbol Sanitization & Validation ──────────────────────────
SYMBOL_REGEX = re.compile(r'^[A-Z0-9]{1,10}$')

def clean_symbol(symbol: str) -> str:
    """
    Membersihkan dan memvalidasi ticker saham IDX.
    Menghilangkan prefix 'IDX:' dan suffix '.JK', trim spasi, serta uppercase.
    """
    if not symbol:
        raise ValueError("Kode simbol tidak boleh kosong.")
    cleaned = symbol.replace("IDX:", "").replace(".JK", "").upper().strip()
    if not SYMBOL_REGEX.match(cleaned):
        raise ValueError(f"Kode simbol '{cleaned}' tidak valid. Harus alfanumerik 1-10 karakter.")
    return cleaned
