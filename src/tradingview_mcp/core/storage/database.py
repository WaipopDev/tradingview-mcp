"""SQLite database helpers for cached trading snapshots and signals."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Union

PathLike = Union[str, os.PathLike[str]]


def default_database_path() -> Path:
    """Return the default SQLite path, overridable for tests/deployments."""
    configured = os.environ.get("TRADINGVIEW_MCP_DB_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def connect_database(path: PathLike | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with row dictionaries and foreign keys enabled."""
    db_path = Path(path).expanduser() if path is not None else default_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def initialize_database(path: PathLike | None = None) -> Path:
    """Create all storage tables if they do not exist and return the DB path."""
    from tradingview_mcp.core.storage.migrations import POST_SCHEMA_COLUMNS, SCHEMA_SQL

    db_path = Path(path).expanduser() if path is not None else default_database_path()
    with connect_database(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        for table, columns in POST_SCHEMA_COLUMNS.items():
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
            for column, column_type in columns.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
    return db_path
