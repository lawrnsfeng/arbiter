"""SQLite storage for a small stock list."""

import sqlite3


def connect(path: str) -> sqlite3.Connection:
    """Open the database at `path` and make sure the schema exists."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS items (name TEXT PRIMARY KEY, qty INTEGER NOT NULL)")
    return conn


def add_item(conn: sqlite3.Connection, name: str, qty: int) -> None:
    """Insert or update the stock count for `name`."""
    conn.execute(
        "INSERT INTO items (name, qty) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET qty = excluded.qty",
        (name, qty),
    )
    conn.commit()


def list_items(conn: sqlite3.Connection) -> list[tuple[str, int]]:
    """Return every item as (name, qty), sorted by name."""
    return conn.execute("SELECT name, qty FROM items ORDER BY name").fetchall()
