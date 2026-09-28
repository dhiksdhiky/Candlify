"""
scripts/inject_historical_data.py
===================================
Script injeksi data historis 6 bulan (Maret - Agustus 2026) ke Neon DB.
- Sumber Maret - Juli 2026: production.db (SQLite)
- Sumber Agustus 2026: folder arship agustus (Excel)
- Target: Neon PostgreSQL (DATABASE_URL di .env)
- Idempoten: Menggunakan ON CONFLICT DO NOTHING / UPDATE
"""

import os
import sys
import time
import sqlite3
import pandas as pd
import psycopg2
from psycopg2 import extras
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

SQLITE_PATH = r"C:\Users\Lenovo\projects\200-299 Research\Persahaman duniawi\stock engine v2\production.db"
AGUSTUS_FOLDER = r"C:\Users\Lenovo\Downloads\arship agustus"

def get_pg_conn():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL belum diatur di .env")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(db_url)

def inject_harga_from_sqlite(pg_conn):
    print("\n--- 1. Inject Harga Saham (Maret - Juli 2026) dari SQLite ---")
    sqlite_conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    cur = sqlite_conn.cursor()
    
    query = """
        SELECT ticker, tanggal, open, high, low, close, volume
        FROM harga_saham
        WHERE tanggal >= '2026-03-01' AND tanggal <= '2026-07-31'
        ORDER BY tanggal ASC
    """
    cur.execute(query)
    rows = cur.fetchall()
    sqlite_conn.close()
    
    print(f"  Total baris harga diambil: {len(rows):,}")
    if not rows:
        return
    
    insert_sql = """
        INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (ticker, tanggal) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
    """
    
    with pg_conn.cursor() as pg_cur:
        extras.execute_values(pg_cur, insert_sql, rows, page_size=5000)
    pg_conn.commit()
    print("  ✅ Harga Saham (Maret - Juli 2026) berhasil di-inject!")

def inject_harga_from_excel(pg_conn):
    print("\n--- 2. Inject Harga Saham (Agustus 2026) dari Excel ---")
    fpath = os.path.join(AGUSTUS_FOLDER, "Archive_harga_saham_20260717_to_20260831.xlsx")
    df = pd.read_excel(fpath)
    df['tanggal'] = pd.to_datetime(df['tanggal']).dt.strftime('%Y-%m-%d')
    # Filter Agustus 2026 saja
    df = df[(df['tanggal'] >= '2026-08-01') & (df['tanggal'] <= '2026-08-31')]
    
    # Kolom: ticker, tanggal, open, high, low, close, volume
    records = []
    for _, r in df.iterrows():
        records.append((
            str(r['ticker']).strip().upper(),
            str(r['tanggal']),
            float(r['open']) if pd.notnull(r['open']) else 0.0,
            float(r['high']) if pd.notnull(r['high']) else 0.0,
            float(r['low']) if pd.notnull(r['low']) else 0.0,
            float(r['close']) if pd.notnull(r['close']) else 0.0,
            int(r['volume']) if pd.notnull(r['volume']) else 0
        ))
    
    print(f"  Total baris harga Agustus diambil: {len(records):,}")
    if not records:
        return
        
    insert_sql = """
        INSERT INTO harga_saham (ticker, tanggal, open, high, low, close, volume)
        VALUES %s
        ON CONFLICT (ticker, tanggal) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume;
    """
    with pg_conn.cursor() as pg_cur:
        extras.execute_values(pg_cur, insert_sql, records, page_size=5000)
    pg_conn.commit()
    print("  ✅ Harga Saham (Agustus 2026) berhasil di-inject!")

def inject_broksum_from_sqlite(pg_conn):
    print("\n--- 3. Inject Broker Summary (Maret - Juli 2026) dari SQLite ---")
    sqlite_conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
    cur = sqlite_conn.cursor()
    
    months = ['2026-03', '2026-04', '2026-05', '2026-06', '2026-07']
    
    insert_sql = """
        INSERT INTO broker_summary (ticker, date, broker_code, buy_vol, buy_val, buy_avg, sell_vol, sell_val, sell_avg, net_vol, net_val)
        VALUES %s
        ON CONFLICT (ticker, date, broker_code) DO NOTHING;
    """
    
    total_injected = 0
    for m in months:
        t0 = time.time()
        print(f"  Processing bulan {m}...")
        cur.execute(f"""
            SELECT ticker, date, broker_code, buy_vol, buy_val, buy_avg, sell_vol, sell_val, sell_avg, net_vol, net_val
            FROM broker_summary
            WHERE substr(date, 1, 7) = '{m}'
        """)
        rows = cur.fetchall()
        print(f"    Diambil: {len(rows):,} baris ({time.time() - t0:.1f}s)")
        
        t1 = time.time()
        with pg_conn.cursor() as pg_cur:
            extras.execute_values(pg_cur, insert_sql, rows, page_size=10000)
        pg_conn.commit()
        total_injected += len(rows)
        print(f"    ✅ Injected {len(rows):,} baris ke Neon ({time.time() - t1:.1f}s)")
        
    sqlite_conn.close()
    print(f"  ✅ Selesai! Total Broker Summary (Maret - Juli): {total_injected:,} baris.")

def inject_broksum_from_excel(pg_conn):
    print("\n--- 4. Inject Broker Summary (Agustus 2026) dari Excel ---")
    insert_sql = """
        INSERT INTO broker_summary (ticker, date, broker_code, buy_vol, buy_val, buy_avg, sell_vol, sell_val, sell_avg, net_vol, net_val)
        VALUES %s
        ON CONFLICT (ticker, date, broker_code) DO NOTHING;
    """
    
    files = [
        ("Archive_broker_summary_20260803_to_20260828.xlsx", "Part 1 (03-28 Ags)"),
        ("Archive_broker_summary_2026-08.xlsx", "Part 2 (28-31 Ags)")
    ]
    
    total_agustus = 0
    for fname, desc in files:
        fpath = os.path.join(AGUSTUS_FOLDER, fname)
        t0 = time.time()
        print(f"  Membaca {desc}: {fname}...")
        df = pd.read_excel(fpath)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        records = []
        for _, r in df.iterrows():
            records.append((
                str(r['ticker']).strip().upper(),
                str(r['date']),
                str(r['broker_code']).strip().upper()[:2],
                int(round(r['buy_vol'])) if pd.notnull(r['buy_vol']) else 0,
                float(r['buy_val']) if pd.notnull(r['buy_val']) else 0.0,
                float(r['buy_avg']) if pd.notnull(r['buy_avg']) else 0.0,
                int(round(r['sell_vol'])) if pd.notnull(r['sell_vol']) else 0,
                float(r['sell_val']) if pd.notnull(r['sell_val']) else 0.0,
                float(r['sell_avg']) if pd.notnull(r['sell_avg']) else 0.0,
                int(round(r['net_vol'])) if pd.notnull(r['net_vol']) else 0,
                float(r['net_val']) if pd.notnull(r['net_val']) else 0.0
            ))
            
        print(f"    Diambil: {len(records):,} baris ({time.time() - t0:.1f}s)")
        t1 = time.time()
        with pg_conn.cursor() as pg_cur:
            extras.execute_values(pg_cur, insert_sql, records, page_size=10000)
        pg_conn.commit()
        total_agustus += len(records)
        print(f"    ✅ Injected {len(records):,} baris ke Neon ({time.time() - t1:.1f}s)")
        
    print(f"  ✅ Selesai! Total Broker Summary Agustus: {total_agustus:,} baris.")

def verify_neon_status(pg_conn):
    print("\n=======================================================")
    print("  VERIFIKASI STATUS DATA AKHIR DI NEON POSTGRESQL")
    print("=======================================================")
    with pg_conn.cursor() as cur:
        # Total counts
        cur.execute("SELECT count(*) FROM harga_saham")
        cnt_h = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM broker_summary")
        cnt_b = cur.fetchone()[0]
        print(f"  Total Baris harga_saham  : {cnt_h:,}")
        print(f"  Total Baris broker_summary: {cnt_b:,}")
        
        print("\n  [Rincian Bulanan HARGA_SAHAM di Neon]")
        cur.execute("""
            SELECT TO_CHAR(tanggal, 'YYYY-MM') as m, count(*), count(distinct tanggal), count(distinct ticker)
            FROM harga_saham
            GROUP BY m
            ORDER BY m ASC
        """)
        for row in cur.fetchall():
            print(f"    Bulan {row[0]}: {row[1]:,} baris | {row[2]} hari bursa | {row[3]} emiten")

        print("\n  [Rincian Bulanan BROKER_SUMMARY di Neon]")
        cur.execute("""
            SELECT TO_CHAR(date, 'YYYY-MM') as m, count(*), count(distinct date), count(distinct ticker)
            FROM broker_summary
            GROUP BY m
            ORDER BY m ASC
        """)
        for row in cur.fetchall():
            print(f"    Bulan {row[0]}: {row[1]:,} baris | {row[2]} hari bursa | {row[3]} emiten")
    print("=======================================================")

def main():
    start_total = time.time()
    print("=======================================================")
    print("  🚀 INJEKSI DATA HISTORIS 7 BULAN KE NEON POSTGRESQL")
    print("=======================================================")
    
    pg_conn = get_pg_conn()
    try:
        inject_harga_from_sqlite(pg_conn)
        inject_harga_from_excel(pg_conn)
        inject_broksum_from_sqlite(pg_conn)
        inject_broksum_from_excel(pg_conn)
        verify_neon_status(pg_conn)
    finally:
        pg_conn.close()
        
    print(f"\n🎉 SELESAI SEMUA DALAM {time.time() - start_total:.1f} DETIK!")

if __name__ == "__main__":
    main()
