"""
lib/db.py — Unified Thread-Safe Database Layer
==============================================
Single source of truth for SQLAlchemy Engine connection pool across Candlify V2.
Features:
- Thread-safe lazy initialization with double-checked locking
- Serverless-friendly connection pool recycling (pool_recycle=300)
- Pre-ping liveness probe (pool_pre_ping=True)
- Connect timeout guard to prevent worker hanging
"""

import os
import logging
import threading
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("CandlifyDB")

_db_engine: Optional[Engine] = None
_db_lock = threading.Lock()

def get_db_engine() -> Optional[Engine]:
    """
    Mengembalikan instance singleton SQLAlchemy Engine yang thread-safe.
    Mendukung PostgreSQL (Neon DB) dan fallback SQLite jika ditentukan.
    """
    global _db_engine
    if _db_engine is not None:
        return _db_engine

    with _db_lock:
        if _db_engine is not None:
            return _db_engine

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("⚠️ DATABASE_URL belum diatur di file .env")
            return None

        # Standarisasi scheme dialect SQLAlchemy 2.0
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        try:
            is_sqlite = db_url.startswith("sqlite")
            if is_sqlite:
                _db_engine = create_engine(db_url, echo=False)
            else:
                _db_engine = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=5,
                    max_overflow=5,
                    connect_args={"connect_timeout": 8}
                )
            logger.info("✅ Database Engine berhasil diinisialisasi.")
            return _db_engine
        except Exception as e:
            logger.error(f"❌ Gagal membangun engine database: {e}")
            return None

# Alias untuk kompatibilitas mundur
get_engine = get_db_engine
