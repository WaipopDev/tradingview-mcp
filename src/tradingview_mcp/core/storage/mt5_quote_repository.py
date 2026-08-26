"""Throttled persistence for broker-native MT5 quote samples."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from tradingview_mcp.core.storage.database import PathLike, connect_database, initialize_database


class Mt5QuoteRepository:
    """Store at most one quote sample per symbol/time bucket."""

    def __init__(self, db_path: PathLike | None = None, *, bucket_seconds: int = 60):
        if bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be positive")
        self.db_path = initialize_database(db_path)
        self.bucket_seconds = int(bucket_seconds)

    def save_quote(
        self,
        symbol: str,
        tick_time_ms: int,
        bid: float,
        ask: float,
        spread_points: float | None = None,
    ) -> bool:
        """Insert a quote if its symbol/time bucket has not been sampled."""
        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be empty")
        tick_time_ms = int(tick_time_ms)
        bucket_ms = (tick_time_ms // (self.bucket_seconds * 1000)) * (self.bucket_seconds * 1000)
        now = datetime.now(timezone.utc).isoformat()
        with connect_database(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO mt5_quote_samples
                    (symbol, tick_time_ms, bucket_start_ms, bid, ask, spread_points, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'MT5', ?)
                """,
                (normalized, tick_time_ms, bucket_ms, float(bid), float(ask), spread_points, now),
            )
        return cursor.rowcount == 1

    def cleanup_retention(self, cutoff_time_ms: int) -> int:
        """Delete samples older than the supplied tick-time cutoff."""
        with connect_database(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM mt5_quote_samples WHERE tick_time_ms < ?",
                (int(cutoff_time_ms),),
            )
        return cursor.rowcount

    def count(self, symbol: str | None = None) -> int:
        sql = "SELECT COUNT(*) FROM mt5_quote_samples"
        params: tuple[Any, ...] = ()
        if symbol:
            sql += " WHERE symbol = ?"
            params = (symbol.strip().upper(),)
        with connect_database(self.db_path) as conn:
            return int(conn.execute(sql, params).fetchone()[0])
