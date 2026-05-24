import sqlite3
import os
from pathlib import Path

DB_PATH = os.environ.get("DB_PATH", "bills.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS bills (
            id             TEXT PRIMARY KEY,
            total_cost     REAL NOT NULL,
            court_name     TEXT,
            note           TEXT,
            split_mode     TEXT NOT NULL,
            host_name      TEXT,
            created_at     TEXT NOT NULL,
            session_hours  REAL,
            bank_account   TEXT
        );

        CREATE TABLE IF NOT EXISTS bill_players (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id  TEXT NOT NULL,
            name     TEXT NOT NULL,
            hours    REAL,
            amount   REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(id)
        );

        CREATE TABLE IF NOT EXISTS user_group (
            user_id     TEXT PRIMARY KEY,
            group_id    TEXT NOT NULL,
            updated_at  TEXT NOT NULL
        );
    """)
    for migration in [
        "ALTER TABLE bills ADD COLUMN session_hours REAL",
        "ALTER TABLE bills ADD COLUMN bank_account TEXT",
    ]:
        try:
            conn.execute(migration)
            conn.commit()
        except Exception:
            pass  # column already exists
    conn.close()
