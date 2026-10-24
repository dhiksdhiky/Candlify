"""
harvester.py — Broker Summary Harvester Orchestrator
======================================================
Mengatur batch scraping broker summary dari IndoPremier.
Bergantung pada data harga_saham yang sudah ada dari pipeline.

Error Handling:
  - Soft Block → Circuit Breaker: cooldown 10 menit, lalu lanjut
  - Hard Block → masuk retry queue
  - Network error → masuk retry queue
  - Server-wide 502 / Outage → Probe cooldown 60s pada gagal ke-5, abort batch pada gagal ke-8
  - Retry Phase: ulang semua target yang gagal (kecuali abort karena server outage)
  - TEST_MODE: limit 10 target, delay 2-5 detik
"""

import os
import sys
import io
import time
import random
import logging
import pandas as pd
import requests
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_config import (
    engine, SessionLocal, log_to_db,
    get_date_cutoff_sql, TEST_MODE,
    GAP_EXCLUDE_SQL, today_jkt, get_dialect,
    get_backfill_floor
)
from scraper import BroksumScraper, SoftBlockError
from archiver import archive_and_delete_old_data
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("Harvester")

# ── Konfigurasi ─────────────────────────────────────────────
TARGET_LIMIT = 500 if not TEST_MODE else 10
DELAY_MIN = 7 if not TEST_MODE else 2
DELAY_MAX = 20 if not TEST_MODE else 5
COOLDOWN_SOFT_BLOCK = 600 if not TEST_MODE else 30  # 10 menit prod, 30s test
COOLDOWN_RETRY = 30 if not TEST_MODE else 5
COOLDOWN_BATCH = 120 if not TEST_MODE else 10
REST_INTERVAL = 60 * 60 * 3 if not TEST_MODE else 30  # 3 jam prod, 30s test

TELEGRAM_BOT_TOKEN = os.getenv("TELE_BOT_DHIKSDHIKY")
TELEGRAM_CHAT_ID = os.getenv("TELE_CHAT_ID_DHIKA")


class BatchHarvester:
    def __init__(self):
        self.scraper = BroksumScraper()
        self.touched_dates = set()
        self.last_batch_aborted = False

    def get_pending_targets(self) -> list:
        """
        Cari pasangan (ticker, tanggal) di harga_saham yang belum punya
        broker_summary. Hanya ambil yang volume > 0, berada di dalam batas retensi
        (backfill_floor), dan tidak terdaftar di harvester_gaps (attempts >= 3).
        Diurutkan dari tanggal terbaru & nilai transaksi terbesar (DESC) agar
        data hari H langsung lengkap lebih dulu saat pulih dari outage multi-hari.
        """
        gap_threshold = today_jkt() - timedelta(days=30)
        backfill_floor = get_backfill_floor()
        query = text(f"""
            SELECT h.ticker, h.tanggal
            FROM harga_saham h
            JOIN daftar_saham ds ON h.ticker = ds.kode
            WHERE h.volume > 0
            AND h.tanggal >= :backfill_floor
            AND NOT EXISTS (
                SELECT 1 FROM broker_summary b
                WHERE b.ticker = h.ticker AND b.date = h.tanggal
            )
            AND {GAP_EXCLUDE_SQL}
            ORDER BY h.tanggal DESC, COALESCE(h.value, 0) DESC, h.volume DESC
            LIMIT :limit
        """)
        try:
            with SessionLocal() as db:
                results = db.execute(query, {
                    "limit": TARGET_LIMIT,
                    "gap_threshold": gap_threshold,
                    "backfill_floor": backfill_floor
                }).fetchall()
                return results
        except SQLAlchemyError as e:
            logger.error(f"❌ DB Error saat fetch targets: {e}")
            log_to_db("harvester", "CRITICAL", "Gagal fetch pending targets", exc_info=e)
            return []

    def record_gap(self, ticker: str, target_date, reason: str):
        """Catat gap terisolasi ke tabel harvester_gaps."""
        try:
            dialect = get_dialect()
            if dialect == "sqlite":
                sql = text("""
                    INSERT INTO harvester_gaps (ticker, date, reason, attempts, last_attempt)
                    VALUES (:ticker, :date, :reason, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        attempts = harvester_gaps.attempts + 1,
                        last_attempt = CURRENT_TIMESTAMP,
                        reason = :reason
                """)
            else:
                sql = text("""
                    INSERT INTO harvester_gaps (ticker, date, reason, attempts, last_attempt)
                    VALUES (:ticker, :date, :reason, 1, NOW())
                    ON CONFLICT (ticker, date) DO UPDATE SET
                        attempts = harvester_gaps.attempts + 1,
                        last_attempt = NOW(),
                        reason = :reason
                """)
            with SessionLocal() as db:
                db.execute(sql, {"ticker": ticker, "date": target_date, "reason": reason})
                db.commit()
        except Exception as e:
            logger.warning(f"⚠️ Gagal catat gap ({ticker}, {target_date}): {e}")

    def _normalize_date(self, target_date):
        if isinstance(target_date, str):
            from datetime import datetime as dt
            return dt.strptime(target_date[:10], "%Y-%m-%d").date()
        elif isinstance(target_date, datetime):
            return target_date.date()
        return target_date

    def process_target(self, ticker: str, target_date) -> str:
        """
        Proses satu target scraping.
        Returns: 'success', 'soft_block', atau 'error'
        """
        try:
            norm_date = self._normalize_date(target_date)
            logger.info(f"🕷️ Scraping {ticker} [{norm_date}]...")
            self.scraper.fetch_and_save(ticker, norm_date)
            self.touched_dates.add(norm_date)
            return 'success'
        except SoftBlockError as sbe:
            logger.error(f"🛑 CIRCUIT BREAKER: {sbe}")
            return 'soft_block'
        except Exception as e:
            logger.warning(f"⚠️ Gagal {ticker} [{target_date}]: {str(e)[:250]}")
            return 'error'

    def run_batch(self) -> bool:
        """
        Eksekusi satu batch harvesting.
        Returns: True jika masih ada data pending, False jika sudah complete atau dihentikan karena IPOT outage.
        """
        self.last_batch_aborted = False
        logger.info("═══════════════════════════════════════════")
        logger.info("  🕷️ HARVESTER BATCH DIMULAI")
        logger.info("═══════════════════════════════════════════")

        targets = self.get_pending_targets()
        total_targets = len(targets)

        if total_targets == 0:
            logger.info("✅ Tidak ada data pending. Database sudah up-to-date.")
            return False

        logger.info(f"📋 {total_targets} target ditemukan.")

        success_count = 0
        deferred_queue = []
        consecutive_failures = 0
        throttle_detected = False
        has_any_success = False
        aborted_by_outage = False

        # ── Fase Utama ──────────────────────────────────────
        for i, row in enumerate(targets):
            ticker, target_date = row[0], row[1]
            status = self.process_target(ticker, target_date)

            if status == 'success':
                success_count += 1
                consecutive_failures = 0
                has_any_success = True
            else:
                consecutive_failures += 1
                if consecutive_failures == 5:
                    probe_wait = 60 if not TEST_MODE else 2
                    logger.warning(
                        f"🚨 IPOT-wide throttle/outage terdeteksi (5 non-success berurutan). "
                        f"Skip gap marking & cooldown {probe_wait}s sebelum probe ulang..."
                    )
                    throttle_detected = True
                    time.sleep(probe_wait)
                elif consecutive_failures >= 8:
                    logger.error(
                        "🛑 Server IndoPremier (IPOT) masih down/502 setelah probe ulang "
                        "(>=8 gagal beruntun). Menghentikan batch lebih awal agar tidak membuang "
                        "kuota runner (target tetap aman di antrean untuk ditarik otomatis saat IPOT pulih)."
                    )
                    throttle_detected = True
                    aborted_by_outage = True
                    break

                if status == 'soft_block':
                    logger.warning(f"💤 Cooldown {COOLDOWN_SOFT_BLOCK}s (Soft-Block)...")
                    log_to_db("harvester", "WARNING", "Circuit Breaker aktif", ticker=ticker)
                    time.sleep(COOLDOWN_SOFT_BLOCK)
                    deferred_queue.append((ticker, target_date))
                    logger.info("🔄 Melanjutkan setelah cooldown.")
                else:
                    deferred_queue.append((ticker, target_date))

            if i < total_targets - 1:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        # ── Fase Retry ──────────────────────────────────────
        if deferred_queue and not aborted_by_outage:
            logger.info(
                f"🔄 Cooldown {COOLDOWN_RETRY}s sebelum retry "
                f"({len(deferred_queue)} target)..."
            )
            time.sleep(COOLDOWN_RETRY)

            for i, (ticker, target_date) in enumerate(deferred_queue):
                logger.info(f"🔁 [RETRY] {ticker} [{target_date}]...")
                status = self.process_target(ticker, target_date)

                if status == 'success':
                    success_count += 1
                    consecutive_failures = 0
                    has_any_success = True
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= 5:
                        throttle_detected = True
                    if consecutive_failures >= 8:
                        logger.error("🛑 IPOT outage berlanjut pada fase retry. Menghentikan retry lebih awal.")
                        aborted_by_outage = True
                        break

                    if status == 'soft_block':
                        logger.warning(f"💤 Cooldown {COOLDOWN_SOFT_BLOCK}s pada retry...")
                        time.sleep(COOLDOWN_SOFT_BLOCK)
                    else:
                        log_to_db("harvester", "WARNING", "Gagal setelah retry", ticker=ticker)

                    # F1: Catat gap HANYA jika bukan IPOT throttle dan run ini punya minimal 1 success!
                    if has_any_success and not throttle_detected:
                        self.record_gap(ticker, target_date, reason=status)

                if i < len(deferred_queue) - 1:
                    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        logger.info("═══════════════════════════════════════════")
        logger.info(
            f"  🕷️ BATCH SELESAI | ✅ {success_count}/{total_targets}"
        )
        logger.info("═══════════════════════════════════════════")
        if aborted_by_outage:
            self.last_batch_aborted = True
            return False
        return True


def run_harvester(daemon_mode: bool = True) -> dict:
    """
    Entry point harvester.
    - daemon_mode=True: loop terus sampai manual stop
    - daemon_mode=False: loop sampai semua data sinkron, lalu berhenti (Auto-Sync)
    Returns dict berisi status ('completed' / 'aborted_outage' / 'error') dan list touched_dates.
    """
    harvester = BatchHarvester()
    mode_str = "Daemon" if daemon_mode else "Auto-Sync"
    logger.info(f"🚀 Harvester Started (Mode: {mode_str})")

    last_archive_time = time.time()
    while True:
        try:
            has_more = harvester.run_batch()

            if not has_more:
                if harvester.last_batch_aborted:
                    if not daemon_mode:
                        logger.warning(
                            "⚠️ Harvester Auto-Sync dihentikan sementara karena server IPOT sedang down/maintenance "
                            "(target sisa tetap aman di antrean)."
                        )
                        return {
                            "status": "aborted_outage",
                            "touched_dates": sorted(harvester.touched_dates)
                        }
                    logger.warning(f"💤 Server IPOT sedang down. Istirahat {REST_INTERVAL}s sebelum cek ulang...")
                    time.sleep(REST_INTERVAL)
                    continue

                # Hanya panggil archiver di dalam loop jika daemon_mode=True (karena di single-run, run.py Step 4 sudah memanggil archiver)
                if daemon_mode:
                    try:
                        archive_and_delete_old_data()
                        last_archive_time = time.time()
                    except Exception as e:
                        logger.error(f"❌ Archiver gagal saat drain selesai: {e}")

                if not daemon_mode:
                    logger.info("🏁 Harvester Auto-Sync selesai.")
                    return {
                        "status": "completed",
                        "touched_dates": sorted(harvester.touched_dates)
                    }

                logger.info(f"💤 Semua sinkron. Istirahat {REST_INTERVAL}s...")
                time.sleep(REST_INTERVAL)
            else:
                # S1: Fallback time-based jika drain menggantung > 4 jam
                if time.time() - last_archive_time > 4 * 3600:
                    try:
                        archive_and_delete_old_data()
                        last_archive_time = time.time()
                    except Exception as e:
                        logger.error(f"❌ Fallback archiver gagal: {e}")

                logger.info(f"⏳ Cooldown {COOLDOWN_BATCH}s sebelum batch berikutnya...")
                time.sleep(COOLDOWN_BATCH)

        except KeyboardInterrupt:
            logger.info("🛑 Harvester dihentikan manual.")
            return {
                "status": "interrupted",
                "touched_dates": sorted(harvester.touched_dates)
            }
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
            log_to_db("harvester", "CRITICAL", f"Crash: {e}")
            if not daemon_mode:
                return {
                    "status": "error",
                    "touched_dates": sorted(harvester.touched_dates)
                }
            time.sleep(300)


if __name__ == "__main__":
    # Bisa dipanggil langsung: python harvester.py [--once]
    once = "--once" in sys.argv
    run_harvester(daemon_mode=not once)
