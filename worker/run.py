"""
run.py — Main Orchestrator (Sequential: Pipeline → Scanner → Harvester → Scanner)
=================================================================================
Entry point utama. Menjalankan Pipeline OHLCV terlebih dahulu,
lalu Pre-Breakout Scanner awal, Harvester BrokSum, dan refresh Scanner.
Semua dalam SATU proses Python (hemat RAM).

Usage:
  python run.py                  # Single run (pipeline + scanner + harvester)
  python run.py --daemon         # Daemon mode (harvester loop terus)
  python run.py --pipeline-only  # Hanya pipeline
  python run.py --harvester-only # Hanya harvester
"""

import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import warnings
import logging
from datetime import datetime

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.WARNING)

from db_config import setup_tables, TEST_MODE

# ── Setup Logging ───────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Orchestrator")


def main():
    start_time = datetime.now()

    # Parse arguments
    args = set(sys.argv[1:])
    daemon_mode = "--daemon" in args
    pipeline_only = "--pipeline-only" in args
    harvester_only = "--harvester-only" in args
    scanner_only = "--scanner-only" in args
    no_sync_stocks = "--no-sync-stocks" in args

    mode_str = "🧪 TEST MODE (SQLite)" if TEST_MODE else "🚀 PRODUCTION (PostgreSQL)"
    logger.info("╔═══════════════════════════════════════════╗")
    logger.info("║     STOCK ENGINE v2 — Unified Runner      ║")
    logger.info("╚═══════════════════════════════════════════╝")
    logger.info(f"  Mode: {mode_str}")
    logger.info(f"  Daemon: {'Ya' if daemon_mode else 'Tidak'}")
    logger.info("")

    # ── Step 1: Setup Database ──────────────────────────────
    try:
        setup_tables()
    except Exception as e:
        logger.error(f"❌ FATAL: Gagal setup database: {e}")
        sys.exit(1)

    if scanner_only:
        try:
            from scanner_bali import run_scanner
            run_scanner()
        except Exception as e:
            logger.error(f"❌ Scanner crash: {e}")
            sys.exit(1)
        duration = datetime.now() - start_time
        logger.info("")
        logger.info("╔═══════════════════════════════════════════╗")
        logger.info(f"║  🏁 SELESAI — Durasi: {str(duration).split('.')[0]:>17s}  ║")
        logger.info("╚═══════════════════════════════════════════╝")
        return

    # ── Step 1b & 2: Primary All-in-One IDX Sync (Master Emiten + Harga & Flow) ────
    sync_daily_success = False
    pipeline_success = True if harvester_only else False
    idx_gaps_filled = []

    if not harvester_only and not ("--legacy-pipeline" in args):
        try:
            logger.info("═══════════════════════════════════════════")
            logger.info("  🚀 PRIMARY EOD SYNC: IDX TRADING SUMMARY")
            logger.info("═══════════════════════════════════════════")
            from sync_idx_daily import run_sync_daily
            sync_res = run_sync_daily(use_fallback=False)
            if sync_res.get("status") == "success":
                sync_daily_success = True
                pipeline_success = True
                idx_gaps_filled = sync_res.get("gaps_filled") or []
                logger.info(f"✅ Sync IDX All-in-One Sukses: {sync_res.get('stocks_synced', 0)} emiten, {sync_res.get('prices_synced', 0)} baris harga.")
        except Exception as e:
            logger.warning(f"⚠️ Primary IDX Sync gagal ({e}), mengaktifkan fallback berjenjang...")

    # Fallback berjenjang jika primary IDX sync belum berhasil atau --legacy-pipeline
    if not harvester_only and not sync_daily_success:
        if not no_sync_stocks:
            try:
                logger.info("═══════════════════════════════════════════")
                logger.info("  📋 FALLBACK: SINKRONISASI DAFTAR SAHAM")
                logger.info("═══════════════════════════════════════════")
                from sync_daftar_saham import run_sync
                sync_res = run_sync()
                src_str = "Portal Resmi BEI" if sync_res.get("source") == "idx_direct" else "Daftar Saham Lokal (Fallback)"
                logger.info(f"✅ Sync Emiten BEI Selesai ({src_str}): {sync_res.get('total_emiten', 0)} emiten terdaftar.")
            except Exception as e:
                logger.warning(f"⚠️ Sync daftar saham dilewati (fallback ke master database yang ada): {e}")

        try:
            logger.info("═══════════════════════════════════════════")
            logger.info("  📈 FALLBACK: PIPELINE OHLCV (YAHOO FINANCE)")
            logger.info("═══════════════════════════════════════════")
            from pipeline import run_pipeline
            pipeline_success = bool(run_pipeline())
        except Exception as e:
            logger.error(f"❌ Pipeline fallback crash: {e}")
            pipeline_success = False

    # ── Step 2b: Pre-Breakout Scanner (Initial Pass setelah Harga & Flow Masuk) ──
    if not daemon_mode and not pipeline_only and not harvester_only and pipeline_success:
        try:
            from scanner_bali import run_scanner
            run_scanner(touched_dates=idx_gaps_filled)
        except Exception as e:
            logger.warning(f"⚠️ Initial Scanner pass gagal: {e}")

    # ── Step 3: Harvester BrokSum ───────────────────────────
    harvester_success = True
    harv_touched_dates = []
    if not pipeline_only:
        try:
            from harvester import run_harvester
            harv_res = run_harvester(daemon_mode=daemon_mode)
            if isinstance(harv_res, dict):
                harv_touched_dates = harv_res.get("touched_dates") or []
                if harv_res.get("status") == "error":
                    harvester_success = False
        except Exception as e:
            logger.error(f"❌ Harvester crash: {e}")
            harvester_success = False

    # ── Step 4: Final Archiver Guarantee ────────────────────
    if not daemon_mode:
        try:
            from archiver import archive_and_delete_old_data
            archive_and_delete_old_data()
        except Exception as e:
            logger.error(f"❌ Final Archiver gagal: {e}")

    # ── Step 5: Pre-Breakout Scanner Engine (Final Refresh dengan BrokSum Terbaru) ──
    scanner_success = True
    if not daemon_mode and not pipeline_only:
        try:
            from scanner_bali import run_scanner
            combined_touched = list(set(idx_gaps_filled) | set(harv_touched_dates))
            run_scanner(touched_dates=combined_touched)
        except Exception as e:
            logger.error(f"❌ Scanner crash: {e}")
            scanner_success = False

    if not pipeline_success:
        logger.error("⚠️ Peringatan: Pipeline sempat gagal sebelumnya (lihat log di atas).")

    # ── Summary ─────────────────────────────────────────────
    duration = datetime.now() - start_time
    logger.info("")
    logger.info("╔═══════════════════════════════════════════╗")
    logger.info(f"║  🏁 SELESAI — Durasi: {str(duration).split('.')[0]:>17s}  ║")
    logger.info("╚═══════════════════════════════════════════╝")

    if (
        not pipeline_success
        or (not pipeline_only and not harvester_success)
        or (not daemon_mode and not pipeline_only and not scanner_success)
    ):
        sys.exit(1)


if __name__ == "__main__":
    main()
