"""
worker/sync_daftar_saham.py — Automated Stock List & Board Synchronizer
=======================================================================
Mengunduh master data emiten resmi dari BEI (via downloader_idx.py),
memperbarui worker/daftar_saham.csv, dan menyinkronkan (upsert) ke
tabel database `daftar_saham` (baik Neon PostgreSQL maupun SQLite).

FITUR:
- Memperbarui papan pencatatan terbaru (Utama, Pengembangan, Pemantauan Khusus / FCA, Akselerasi).
- Mempertahankan kompatibilitas format CSV (separator ';', pemisah ribuan titik).
- Eksekusi aman tanpa menghapus atau mengganggu data harga & broksum yang sudah ada.
"""

from __future__ import annotations

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any

from sqlalchemy import text

# Pastikan path import module worker terbaca
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_config import engine, get_dialect, TEST_MODE
from downloader_idx import fetch_idx_stocks, StockRecord

logger = logging.getLogger("SyncDaftarSaham")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

BULAN_INDO = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}


def format_date_indo(date_str: str) -> str:
    """Konversi '1997-12-09' -> '09 Des 1997' untuk kompatibilitas format CSV lama."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        bln = BULAN_INDO.get(dt.month, "Jan")
        return f"{dt.day:02d} {bln} {dt.year}"
    except Exception:
        return date_str


def format_shares_dot(shares: int) -> str:
    """Format angka saham dengan pemisah titik: 1924688333 -> '1.924.688.333'."""
    return f"{shares:,}".replace(",", ".")


def update_csv_file(records: List[StockRecord], csv_path: str) -> None:
    """Menulis ulang worker/daftar_saham.csv dengan data terbaru dari IDX."""
    # Urutkan berdasarkan Kode
    sorted_records = sorted(records, key=lambda x: x.code)
    
    lines = ["No;Kode;Nama Perusahaan;Tanggal Pencatatan;Saham;Papan Pencatatan\n"]
    for i, r in enumerate(sorted_records, 1):
        tgl_indo = format_date_indo(r.listing_date)
        saham_str = format_shares_dot(r.shares)
        line = f"{i};{r.code};{r.name};{tgl_indo};{saham_str};{r.listing_board}\n"
        lines.append(line)

    with open(csv_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    logger.info("📄 File %s berhasil diperbarui (%d baris emiten).", csv_path, len(sorted_records))


def sync_to_database(records: List[StockRecord]) -> int:
    """Menyinkronkan data emiten ke tabel daftar_saham di database."""
    dialect = get_dialect()
    logger.info("🗄️ Melakukan upsert ke tabel daftar_saham di DB (%s)...", dialect)

    upsert_stmt = text("""
        INSERT INTO daftar_saham (
            kode, no, nama_perusahaan, tanggal_pencatatan, saham, papan_pencatatan, tanggal_update
        ) VALUES (
            :kode, :no, :nama, :tgl, :saham, :papan, CURRENT_DATE
        )
        ON CONFLICT (kode) DO UPDATE SET
            no = EXCLUDED.no,
            nama_perusahaan = EXCLUDED.nama_perusahaan,
            tanggal_pencatatan = EXCLUDED.tanggal_pencatatan,
            saham = EXCLUDED.saham,
            papan_pencatatan = EXCLUDED.papan_pencatatan,
            tanggal_update = CURRENT_DATE
    """)

    sorted_records = sorted(records, key=lambda x: x.code)
    params_list = []
    for i, r in enumerate(sorted_records, 1):
        tgl_db = None
        if r.listing_date:
            try:
                tgl_db = datetime.strptime(r.listing_date, "%Y-%m-%d").date()
            except Exception:
                tgl_db = None

        params_list.append({
            "kode": r.code,
            "no": i,
            "nama": r.name,
            "tgl": tgl_db,
            "saham": r.shares,
            "papan": r.listing_board,
        })

    with engine.begin() as conn:
        conn.execute(upsert_stmt, params_list)

    updated_count = len(params_list)
    logger.info("✅ Database daftar_saham tersinkronisasi: %d emiten terupdate.", updated_count)
    return updated_count


def load_records_from_csv(csv_path: str) -> List[StockRecord]:
    """Fallback: Muat data emiten dari file worker/daftar_saham.csv lokal jika portal BEI terhalang."""
    if not os.path.exists(csv_path):
        return []
    import csv
    indo_to_month = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
        "Mei": "05", "Jun": "06", "Jul": "07", "Agu": "08",
        "Sep": "09", "Okt": "10", "Nov": "11", "Des": "12"
    }
    records: List[StockRecord] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader, 1):
            code = (row.get("Kode") or "").strip().upper()
            if not code:
                continue
            name = (row.get("Nama Perusahaan") or "").strip()
            raw_tgl = (row.get("Tanggal Pencatatan") or "").strip()
            tgl_iso = ""
            if raw_tgl:
                parts = raw_tgl.split()
                if len(parts) == 3:
                    d, m, y = parts
                    m_num = indo_to_month.get(m, "01")
                    tgl_iso = f"{y}-{m_num}-{d.zfill(2)}"
            raw_saham = (row.get("Saham") or "0").replace(".", "").replace(",", "").strip()
            try:
                shares = int(raw_saham)
            except ValueError:
                shares = 0
            board = (row.get("Papan Pencatatan") or "").strip() or "Pengembangan"
            records.append(StockRecord(
                code=code,
                name=name,
                listing_date=tgl_iso,
                shares=shares,
                listing_board=board,
                no=i
            ))
    return records


def run_sync() -> Dict[str, Any]:
    """Eksekusi proses sinkronisasi daftar saham secara menyeluruh."""
    logger.info("🚀 Memulai sinkronisasi daftar saham & papan pencatatan IDX...")
    csv_path = os.path.join(os.path.dirname(__file__), "daftar_saham.csv")
    records: List[StockRecord] = []
    source = "idx_direct"

    try:
        records = fetch_idx_stocks()
        if records:
            # 1. Update file CSV lokal
            update_csv_file(records, csv_path)
            logger.info("✅ Berhasil mengunduh %d emiten langsung dari portal BEI.", len(records))
    except Exception as e:
        logger.warning("⚠️ Sinkronisasi langsung ke portal BEI terkendala: %s. Beralih ke fallback file CSV lokal.", e)
        records = []

    if not records:
        logger.info("📄 Menggunakan fallback master emiten dari %s...", csv_path)
        records = load_records_from_csv(csv_path)
        source = "local_csv_fallback"

    if not records:
        raise RuntimeError("Gagal memuat daftar emiten: data dari BEI dan CSV kosong.")

    # 2. Update Database Neon / SQLite
    db_updated = sync_to_database(records)

    # Hitung sebaran papan
    board_dist: Dict[str, int] = {}
    for r in records:
        board_dist[r.listing_board] = board_dist.get(r.listing_board, 0) + 1

    logger.info("📊 Sebaran Papan Pencatatan:")
    for b_name, count in sorted(board_dist.items(), key=lambda x: x[1], reverse=True):
        logger.info("   • %-25s: %3d emiten", b_name, count)

    return {
        "success": True,
        "source": source,
        "total_emiten": len(records),
        "db_updated": db_updated,
        "board_distribution": board_dist
    }


if __name__ == "__main__":
    result = run_sync()
    print("Hasil sinkronisasi:", result)
