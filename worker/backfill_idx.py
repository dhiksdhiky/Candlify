"""
worker/backfill_idx.py — Fast Multi-Week Historical IDX Backfiller
==================================================================
Mengisi data historis harga saham & foreign flow dari BEI (GetStockSummary)
untuk N hari bursa ke belakang (default: 20 hari bursa / ~4 minggu).

Fitur:
- Melewatkan akhir pekan (Sabtu & Minggu).
- Otomatis mendeteksi hari libur bursa nasional (0 emiten).
- Resume-friendly: Lewatkan tanggal yang sudah terisi lengkap di database.
- Eksekusi ultra-cepat via execute_values (~1,5 detik per hari bursa).
- Jeda sopan (polite delay) 1,5 detik antar request ke BEI.
"""

from __future__ import annotations

import os
import sys
import time
import argparse
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Set

from sqlalchemy import text

# Pastikan path import module worker terbaca
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import engine, get_dialect, today_jkt
from sync_idx_daily import run_sync_daily

logger = logging.getLogger("IDXBackfiller")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )


def get_existing_dates_in_db() -> Set[date]:
    """Mengambil daftar tanggal bursa yang sudah memiliki data foreign flow lengkap di DB."""
    existing_dates: Set[date] = set()
    try:
        with engine.connect() as conn:
            # Dianggap lengkap jika punya minimal 500 emiten dengan frequency > 0 (data resmi IDX)
            query = text("""
                SELECT tanggal, COUNT(*) as cnt 
                FROM harga_saham 
                WHERE frequency > 0 
                GROUP BY tanggal 
                HAVING COUNT(*) >= 500
            """)
            rows = conn.execute(query).fetchall()
            for r in rows:
                if isinstance(r[0], date):
                    existing_dates.add(r[0])
                elif isinstance(r[0], str):
                    try:
                        existing_dates.add(datetime.strptime(r[0], "%Y-%m-%d").date())
                    except Exception:
                        pass
        logger.info("📊 Tanggal yang sudah lengkap di DB: %d hari bursa.", len(existing_dates))
    except Exception as e:
        logger.warning("⚠️ Gagal mengecek tanggal di DB (%s), lanjut tanpa skip cache.", e)

    return existing_dates


def run_backfill(
    target_trading_days: int = 20,
    delay_seconds: float = 1.5,
    skip_existing: bool = True
) -> Dict[str, Any]:
    """
    Menjalankan proses backfill historis BEI.
    """
    start_time = time.time()
    logger.info("╔════════════════════════════════════════════════════════════╗")
    logger.info("║         FAST IDX HISTORICAL EOD & FLOW BACKFILLER          ║")
    logger.info("╚════════════════════════════════════════════════════════════╝")
    logger.info("  🎯 Target Hari Bursa : %d hari (~4 minggu)", target_trading_days)
    logger.info("  ⏱️ Delay Antar Req   : %.1f detik", delay_seconds)
    logger.info("  🔄 Skip Existing DB  : %s", "Ya" if skip_existing else "Tidak")
    logger.info("")

    existing_dates = get_existing_dates_in_db() if skip_existing else set()

    synced_trading_days: List[str] = []
    skipped_existing_days: List[str] = []
    holiday_days: List[str] = []

    current_dt = today_jkt()

    # Maksimal scan mundur 60 hari kalender untuk mendapatkan N hari bursa
    max_calendar_days = target_trading_days * 3
    days_scanned = 0

    while len(synced_trading_days) + len(skipped_existing_days) < target_trading_days and days_scanned < max_calendar_days:
        days_scanned += 1
        current_dt -= timedelta(days=1)

        # 1. Lewatkan hari libur akhir pekan
        if current_dt.weekday() in (5, 6):  # 5=Sabtu, 6=Minggu
            continue

        date_str_formatted = current_dt.strftime("%Y-%m-%d")
        date_str_param = current_dt.strftime("%Y%m%d")

        # 2. Cek apakah sudah ada di DB
        if current_dt in existing_dates:
            logger.info("⏩ [%d/%d] %s: Data sudah lengkap di DB (dilewati).",
                        len(synced_trading_days) + len(skipped_existing_days) + 1,
                        target_trading_days, date_str_formatted)
            skipped_existing_days.append(date_str_formatted)
            continue

        # 3. Tarik data dari BEI
        logger.info("📥 [%d/%d] Mengambil data tanggal %s...",
                    len(synced_trading_days) + len(skipped_existing_days) + 1,
                    target_trading_days, date_str_formatted)
        try:
            res = run_sync_daily(date_str=date_str_param, use_fallback=False)
            if res.get("status") == "success" and res.get("prices_synced", 0) > 0:
                synced_trading_days.append(date_str_formatted)
                logger.info("✅ [%d/%d] %s: Berhasil sinkronisasi %d saham (%.2fs).",
                            len(synced_trading_days) + len(skipped_existing_days),
                            target_trading_days, date_str_formatted,
                            res.get("prices_synced", 0), res.get("duration_seconds", 0))
                time.sleep(delay_seconds)
            else:
                logger.info("ℹ️ %s: Libur bursa / tidak ada perdagangan (0 saham).", date_str_formatted)
                holiday_days.append(date_str_formatted)
        except Exception as e:
            logger.warning("⚠️ %s: Gagal mengambil data (%s), lanjut ke hari sebelumnya.", date_str_formatted, e)

    total_duration = time.time() - start_time
    total_available = len(synced_trading_days) + len(skipped_existing_days)

    logger.info("")
    logger.info("════════════════════════════════════════════════════════════")
    logger.info("  🏁 BACKFILL SELESAI!")
    logger.info("  📅 Total Hari Bursa Siap : %d / %d hari", total_available, target_trading_days)
    logger.info("  ✨ Baru Ditarik          : %d hari", len(synced_trading_days))
    logger.info("  ⚡ Sudah Ada Sebelumnya  : %d hari", len(skipped_existing_days))
    logger.info("  🏖️ Libur Bursa Dideteksi : %d hari", len(holiday_days))
    logger.info("  ⏱️ Total Waktu Proses    : %.2f detik", total_duration)
    logger.info("════════════════════════════════════════════════════════════")

    return {
        "status": "completed",
        "target_days": target_trading_days,
        "total_available_days": total_available,
        "synced_days_count": len(synced_trading_days),
        "synced_days": synced_trading_days,
        "skipped_existing_count": len(skipped_existing_days),
        "total_duration_seconds": round(total_duration, 2)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fast IDX Historical Backfiller")
    parser.add_argument("--days", type=int, default=20, help="Jumlah hari bursa ke belakang (default: 20)")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay antar request dalam detik (default: 1.5)")
    parser.add_argument("--force", action="store_true", help="Paksa tarik ulang tanggal yang sudah ada di DB")

    args = parser.parse_args()
    run_backfill(
        target_trading_days=args.days,
        delay_seconds=args.delay,
        skip_existing=not args.force
    )
