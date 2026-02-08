import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

DATABASE_PATH = os.getenv("DATABASE_PATH", "app.db")


def get_connection() -> sqlite3.Connection:
    """Create a new database connection with foreign keys enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    # Enable foreign key constraint enforcement
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
