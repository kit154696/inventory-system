"""Versioned schema migrations. Never drop/rewrite existing tables — only
additive changes go here, each recorded in schema_version so it runs once.
"""
import sqlite3

from database.seed_data import CATEGORIES, INITIAL_ITEMS

_SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT NOT NULL,
    spec        TEXT DEFAULT '-',
    cat_code    TEXT NOT NULL REFERENCES categories(code),
    cat_name    TEXT NOT NULL,
    unit        TEXT NOT NULL,
    min_qty     INTEGER DEFAULT 5,
    location    TEXT DEFAULT 'กองพัสดุ',
    last_price  REAL DEFAULT 0,
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    type       TEXT NOT NULL CHECK(type IN ('IN','OUT')),
    doc_no     TEXT NOT NULL,
    ref        TEXT DEFAULT '',
    note       TEXT DEFAULT '',
    user_name  TEXT DEFAULT '',
    approver   TEXT DEFAULT '',
    checker    TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transaction_lines (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_id   INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    item_id INTEGER NOT NULL REFERENCES items(id),
    code    TEXT NOT NULL,
    name    TEXT NOT NULL,
    spec    TEXT DEFAULT '-',
    unit    TEXT NOT NULL,
    qty     REAL NOT NULL,
    price   REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_items_code ON items(code);
CREATE INDEX IF NOT EXISTS idx_items_cat ON items(cat_code);
CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(type);
CREATE INDEX IF NOT EXISTS idx_txlines_txid ON transaction_lines(tx_id);
CREATE INDEX IF NOT EXISTS idx_txlines_itemid ON transaction_lines(item_id);
"""


def _migration_0001_schema(conn: sqlite3.Connection):
    conn.executescript(_SCHEMA_V1)


def _migration_0002_seed(conn: sqlite3.Connection):
    conn.executemany(
        "INSERT OR IGNORE INTO categories (code, name) VALUES (?, ?)",
        list(CATEGORIES.items()),
    )
    conn.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        ("orgName", "องค์การบริหารส่วนตำบลตัวอย่าง"),
    )
    for item in INITIAL_ITEMS:
        cat_name = CATEGORIES.get(item["cat"], "อื่นๆ")
        conn.execute(
            """INSERT OR IGNORE INTO items
               (code, name, spec, cat_code, cat_name, unit, min_qty, location, last_price)
               VALUES (?, ?, '-', ?, ?, ?, 5, 'กองพัสดุ', 0)""",
            (item["code"], item["name"], item["cat"], cat_name, item["unit"]),
        )


MIGRATIONS = [
    (1, _migration_0001_schema),
    (2, _migration_0002_seed),
]


def run_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
    )
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_version")}

    for version, fn in MIGRATIONS:
        if version in applied:
            continue
        conn.execute("BEGIN IMMEDIATE;")
        try:
            fn(conn)
            conn.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (version,)
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
