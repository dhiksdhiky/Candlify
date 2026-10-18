"""
lib/database_monitor.py — Glory Engine & Neon Database Monitoring Service
========================================================================
Menyediakan integrasi langsung ke tabel Neon DB:
- Master emiten (daftar_saham) & upload file Excel dari IDX
- Riwayat sinkronisasi harian (harga_saham & broker_summary)
- Tracking arsip bulanan (archive_status)
- Monitoring kendala & suspensi (bot_error_logs & harvester_gaps)
"""

import io
import re
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy import text
from lib.db import get_engine

logger = logging.getLogger("candlify.database_monitor")


def get_calendar_history(month_str: str) -> Dict[str, Any]:
    """
    Ambil riwayat sinkronisasi harian khusus bulan tertentu (YYYY-MM).
    Sangat cepat & ringan untuk navigasi kalender.
    """
    engine = get_engine()
    try:
        parts = month_str.split('-')
        year = int(parts[0])
        month = int(parts[1])
        first_day = date(year, month, 1)
        if month == 12:
            next_month_first_day = date(year + 1, 1, 1)
        else:
            next_month_first_day = date(year, month + 1, 1)
    except Exception as e:
        logger.warning(f"Format month_str tidak valid ({month_str}): {e}")
        today = date.today()
        first_day = today.replace(day=1)
        if today.month == 12:
            next_month_first_day = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month_first_day = today.replace(month=today.month + 1, day=1)
        month_str = first_day.strftime("%Y-%m")

    history_data: List[Dict[str, Any]] = []
    with engine.connect() as db:
        try:
            sql_history = text("""
                SELECT 
                    h.tanggal as date,
                    COUNT(DISTINCT h.ticker) as harga_total,
                    SUM(CASE WHEN h.volume > 0 THEN 1 ELSE 0 END) as target_harvester,
                    (SELECT COUNT(DISTINCT b.ticker) FROM broker_summary b WHERE b.date = h.tanggal) as broker_total
                FROM harga_saham h
                WHERE h.tanggal >= :first_day AND h.tanggal < :next_month_first_day
                GROUP BY h.tanggal
                ORDER BY h.tanggal ASC
            """)
            hist_rows = db.execute(sql_history, {
                "first_day": first_day, 
                "next_month_first_day": next_month_first_day
            }).fetchall()

            for r in hist_rows:
                history_data.append({
                    "date": str(r.date),
                    "ohlcv_scraped": int(r.harga_total) if r.harga_total else 0,
                    "target_harvester": int(r.target_harvester) if r.target_harvester else 0,
                    "broksum_synced": int(r.broker_total) if r.broker_total else 0
                })
        except Exception as e:
            logger.warning(f"Error fetching calendar history for {month_str}: {e}")

    return {
        "status": "success",
        "month": month_str,
        "history": history_data
    }


def get_database_metrics(target_month: Optional[str] = None) -> Dict[str, Any]:
    """
    Ambil status kesehatan, kapasitas baris, dan riwayat sinkronisasi Neon DB.
    """
    engine = get_engine()
    with engine.connect() as db:
        # 1. Total Emiten di Daftar Saham
        try:
            sql_saham = text("SELECT COUNT(*) as total, MAX(tanggal_update) as last_update FROM daftar_saham")
            saham_row = db.execute(sql_saham).fetchone()
            saham_total = int(saham_row.total) if saham_row and saham_row.total else 0
            saham_date = str(saham_row.last_update) if saham_row and saham_row.last_update else "N/A"
        except Exception as e:
            logger.warning(f"Error fetching daftar_saham: {e}")
            try: db.rollback()
            except Exception: pass
            saham_total = 0
            saham_date = "N/A"

        # 2. Daftar Bulan yang Tersedia (Available Months)
        is_sqlite = engine.dialect.name == "sqlite"
        if is_sqlite:
            sql_months = text("SELECT DISTINCT strftime('%Y-%m', tanggal) as m FROM harga_saham WHERE tanggal IS NOT NULL ORDER BY m DESC")
        else:
            sql_months = text("SELECT DISTINCT TO_CHAR(tanggal, 'YYYY-MM') as m FROM harga_saham WHERE tanggal IS NOT NULL ORDER BY m DESC")
        try:
            available_months = [str(r[0]) for r in db.execute(sql_months).fetchall() if r[0]]
        except Exception as e:
            logger.warning(f"Error fetching available months: {e}")
            try: db.rollback()
            except Exception: pass
            available_months = []

        # Tentukan bulan aktif kalender
        if target_month and target_month in available_months:
            active_month = target_month
        elif available_months:
            active_month = available_months[0]
        else:
            active_month = date.today().strftime("%Y-%m")

        try:
            parts = active_month.split('-')
            year = int(parts[0])
            month = int(parts[1])
            first_day = date(year, month, 1)
            if month == 12:
                next_month_first_day = date(year + 1, 1, 1)
            else:
                next_month_first_day = date(year, month + 1, 1)
        except Exception:
            today = date.today()
            first_day = today.replace(day=1)
            if today.month == 12:
                next_month_first_day = today.replace(year=today.year + 1, month=1, day=1)
            else:
                next_month_first_day = today.replace(month=today.month + 1, day=1)
            active_month = first_day.strftime("%Y-%m")

        history_data: List[Dict[str, Any]] = []
        try:
            sql_history = text("""
                SELECT 
                    h.tanggal as date,
                    COUNT(DISTINCT h.ticker) as harga_total,
                    SUM(CASE WHEN h.volume > 0 THEN 1 ELSE 0 END) as target_harvester,
                    SUM(CASE WHEN COALESCE(h.frequency, 0) > 0 THEN 1 ELSE 0 END) as idx_official_total,
                    (SELECT COUNT(DISTINCT b.ticker) FROM broker_summary b WHERE b.date = h.tanggal) as broker_total
                FROM harga_saham h
                WHERE h.tanggal >= :first_day AND h.tanggal < :next_month_first_day
                GROUP BY h.tanggal
                ORDER BY h.tanggal ASC
            """)
            hist_rows = db.execute(sql_history, {
                "first_day": first_day, 
                "next_month_first_day": next_month_first_day
            }).fetchall()

            for r in hist_rows:
                history_data.append({
                    "date": str(r.date),
                    "ohlcv_scraped": int(r.harga_total) if r.harga_total else 0,
                    "target_harvester": int(r.target_harvester) if r.target_harvester else 0,
                    "idx_official_synced": int(r.idx_official_total) if hasattr(r, 'idx_official_total') and r.idx_official_total else 0,
                    "broksum_synced": int(r.broker_total) if r.broker_total else 0
                })
        except Exception as e:
            logger.warning(f"Error fetching history data: {e}")
            try: db.rollback()
            except Exception: pass

        pipeline_data = history_data[-1] if history_data else {
            "date": "N/A", "ohlcv_scraped": 0, "target_harvester": 0, "broksum_synced": 0
        }

        # 3. Recent Bot Errors (48 Jam Terakhir)
        errors: List[Dict[str, Any]] = []
        try:
            sql_errors = text("""
                SELECT bot_name, error_level, error_message, timestamp
                FROM bot_error_logs
                WHERE timestamp >= NOW() - INTERVAL '48 HOURS'
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            error_rows = db.execute(sql_errors).fetchall()
            for r in error_rows:
                t_str = r.timestamp.strftime('%Y-%m-%d %H:%M') if hasattr(r.timestamp, 'strftime') else str(r.timestamp)
                errors.append({
                    "bot_name": str(r.bot_name),
                    "level": str(r.error_level),
                    "message": str(r.error_message),
                    "time": t_str
                })
        except Exception as e:
            logger.warning(f"Error fetching bot_error_logs: {e}")
            try: db.rollback()
            except Exception: pass

        # 4. Archive Status & DB Stats
        archive_list: List[Dict[str, Any]] = []
        db_stats = {"total_harga": 0, "total_broksum": 0, "min_date": "N/A", "max_date": "N/A"}
        try:
            sql_archive = text("""
                SELECT month, status, completed_at 
                FROM archive_status 
                ORDER BY month DESC 
                LIMIT 5
            """)
            archive_rows = db.execute(sql_archive).fetchall()
            for r in archive_rows:
                c_str = r.completed_at.strftime('%Y-%m-%d %H:%M') if hasattr(r.completed_at, 'strftime') and r.completed_at else str(r.completed_at)
                archive_list.append({
                    "month": str(r.month),
                    "status": str(r.status),
                    "completed_at": c_str
                })

            sql_stats = text("""
                SELECT 
                    (SELECT COUNT(*) FROM harga_saham) as total_harga,
                    (SELECT COUNT(*) FROM broker_summary) as total_broksum,
                    (SELECT MIN(tanggal) FROM harga_saham) as min_date,
                    (SELECT MAX(tanggal) FROM harga_saham) as max_date,
                    (SELECT COUNT(*) FROM harga_saham WHERE COALESCE(frequency, 0) > 0) as total_idx_official
            """)
            stats_row = db.execute(sql_stats).fetchone()
            if stats_row:
                db_stats = {
                    "total_harga": int(stats_row.total_harga) if stats_row.total_harga else 0,
                    "total_broksum": int(stats_row.total_broksum) if stats_row.total_broksum else 0,
                    "total_idx_official": int(stats_row.total_idx_official) if hasattr(stats_row, 'total_idx_official') and stats_row.total_idx_official else 0,
                    "min_date": str(stats_row.min_date) if stats_row.min_date else "N/A",
                    "max_date": str(stats_row.max_date) if stats_row.max_date else "N/A"
                }
        except Exception as e:
            logger.warning(f"Error fetching archive & stats: {e}")
            try: db.rollback()
            except Exception: pass

        # 5. Harvester Gaps (Suspensi / Gap Emiten)
        gap_list: List[Dict[str, Any]] = []
        try:
            sql_gaps = text("""
                SELECT ticker, date, reason, attempts, last_attempt 
                FROM harvester_gaps 
                ORDER BY date DESC, attempts DESC 
                LIMIT 20
            """)
            gap_rows = db.execute(sql_gaps).fetchall()
            for r in gap_rows:
                la_str = r.last_attempt.strftime('%Y-%m-%d %H:%M') if hasattr(r.last_attempt, 'strftime') and r.last_attempt else str(r.last_attempt)
                gap_list.append({
                    "ticker": str(r.ticker),
                    "date": str(r.date),
                    "reason": str(r.reason or 'Data Kosong / Suspensi'),
                    "attempts": int(r.attempts) if r.attempts else 1,
                    "last_attempt": la_str
                })
        except Exception as e:
            logger.warning(f"Error fetching harvester_gaps: {e}")
            try: db.rollback()
            except Exception: pass

    return {
        "status": "success",
        "data": {
            "current_month": active_month,
            "available_months": available_months,
            "saham": {"total": saham_total, "last_update": saham_date},
            "pipeline": pipeline_data,
            "history": history_data,
            "errors": errors,
            "archive": {
                "history": archive_list,
                "stats": db_stats
            },
            "gaps": gap_list
        }
    }


def _parse_idx_date(date_str) -> Optional[date]:
    if pd.isna(date_str):
        return None
    if isinstance(date_str, datetime):
        return date_str.date()
    if isinstance(date_str, date):
        return date_str

    months_map = {
        'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'Mei': '05', 'Jun': '06',
        'Jul': '07', 'Agu': '08', 'Agt': '08', 'Sep': '09', 'Okt': '10', 'Nov': '11', 'Des': '12'
    }
    try:
        parts = str(date_str).strip().split()
        if len(parts) == 3:
            day, month_id, year = parts
            month = months_map.get(month_id, '01')
            return datetime.strptime(f"{year}-{month}-{day.zfill(2)}", "%Y-%m-%d").date()
    except Exception:
        pass
    return None


def _clean_numeric(value) -> int:
    if pd.isna(value):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    clean_str = re.sub(r'[^\d]', '', str(value))
    return int(clean_str) if clean_str else 0


def _clean_string(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r'\s+', ' ', str(value)).strip()


def extract_date_from_filename(filename: str) -> date:
    """Ekstrak tanggal YYYYMMDD dari nama file jika ada, atau gunakan tanggal hari ini."""
    match = re.search(r'\d{8}', filename or '')
    if match:
        try:
            return datetime.strptime(match.group(), "%Y%m%d").date()
        except ValueError:
            pass
    return datetime.now().date()


def process_saham_excel(excel_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Eksekusi strategi Wipe & Replace tabel daftar_saham secara atomik dari file Excel IDX.
    """
    try:
        df = pd.read_excel(io.BytesIO(excel_bytes), engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Gagal membaca format file Excel: {e}")

    # Cek kolom dasar IDX
    required_columns = ['No', 'Kode', 'Nama Perusahaan', 'Tanggal Pencatatan', 'Saham', 'Papan Pencatatan']
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Kolom Excel tidak sesuai standar IDX. Kolom hilang: {', '.join(missing)}")

    update_date = extract_date_from_filename(filename)
    engine = get_engine()

    insert_rows = []
    for _, row in df.iterrows():
        kode = _clean_string(row['Kode']).upper()
        if not kode:
            continue

        insert_rows.append({
            "no": _clean_numeric(row['No']),
            "kode": kode,
            "nama_perusahaan": _clean_string(row['Nama Perusahaan']),
            "tanggal_pencatatan": _parse_idx_date(row['Tanggal Pencatatan']),
            "saham": _clean_numeric(row['Saham']),
            "papan_pencatatan": _clean_string(row['Papan Pencatatan']),
            "tanggal_update": update_date
        })

    if not insert_rows:
        raise ValueError("Tidak ada data emiten valid yang ditemukan dalam file Excel.")

    with engine.begin() as conn:
        # Safety net: cek jumlah data emiten aktif sebelum wipe
        try:
            curr_count = conn.execute(text("SELECT COUNT(*) FROM daftar_saham")).scalar() or 0
        except Exception:
            curr_count = 0

        # Jika data lama >= 500 tapi data upload baru < 500, batalkan transaksi demi keamanan
        if curr_count >= 500 and len(insert_rows) < 500:
            raise ValueError(
                f"Proses dibatalkan demi keamanan: Data baru ({len(insert_rows)} emiten) terlalu sedikit "
                f"dibandingkan master data aktif ({curr_count} emiten). Minimal 500 emiten valid."
            )

        # Wipe tabel daftar_saham
        conn.execute(text("DELETE FROM daftar_saham"))

        # Bulk insert
        insert_sql = text("""
            INSERT INTO daftar_saham (no, kode, nama_perusahaan, tanggal_pencatatan, saham, papan_pencatatan, tanggal_update)
            VALUES (:no, :kode, :nama_perusahaan, :tanggal_pencatatan, :saham, :papan_pencatatan, :tanggal_update)
        """)
        conn.execute(insert_sql, insert_rows)

    return {
        "status": "success",
        "message": f"Berhasil memperbarui master data {len(insert_rows)} emiten",
        "total_active": len(insert_rows),
        "tanggal_update": str(update_date)
    }
