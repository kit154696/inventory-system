"""SQLite connection management + transaction helper.

A single module-level connection is reused for the lifetime of the app
(desktop, single-user, single-process — no pooling needed).
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from utils.paths import get_db_path

_connection: sqlite3.Connection | None = None


def connect() -> sqlite3.Connection:
    global _connection
    if _connection is not None:
        return _connection

    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _connection = conn
    return conn


def connect_at(path: Path) -> sqlite3.Connection:
    """Open a connection at an explicit path, bypassing the AppData default.

    Used by tests/dev runs that want an isolated database file.
    """
    global _connection
    if _connection is not None:
        _connection.close()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    _connection = conn
    return conn


def disconnect() -> None:
    """Checkpoint the WAL into the main file and close the live connection.

    Must be called before swapping out the underlying .db file on disk
    (restore/import), so no stale connection or WAL sidecar file is left
    pointing at data that no longer matches what's on disk.
    """
    global _connection
    if _connection is None:
        return
    try:
        _connection.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except sqlite3.Error:
        pass
    _connection.close()
    _connection = None


@contextmanager
def transaction():
    """Wrap a block of writes in BEGIN IMMEDIATE / COMMIT, ROLLBACK on error."""
    conn = connect()
    conn.execute("BEGIN IMMEDIATE;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_database() -> sqlite3.Connection:
    """Ensure the AppData dir + database file + schema/seed data all exist."""
    from database import migrations

    conn = connect()
    migrations.run_migrations(conn)
    return conn
