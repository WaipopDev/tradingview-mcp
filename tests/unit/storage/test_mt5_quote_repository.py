from __future__ import annotations

import sqlite3

from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.mt5_quote_repository import Mt5QuoteRepository


def test_mt5_quote_samples_are_deduplicated_by_symbol_and_time_bucket(tmp_path):
    db_path = tmp_path / "quotes.sqlite3"
    initialize_database(db_path)
    repo = Mt5QuoteRepository(db_path, bucket_seconds=60)

    assert repo.save_quote("XAUUSD", 1_700_000_001_000, 2000.1, 2000.3, 20) is True
    assert repo.save_quote("XAUUSD", 1_700_000_029_000, 2000.2, 2000.4, 20) is False
    assert repo.save_quote("xauusd", 1_700_000_061_000, 2000.4, 2000.6, 20) is True

    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM mt5_quote_samples").fetchone()[0] == 2


def test_mt5_quote_retention_cleanup_removes_only_old_samples(tmp_path):
    db_path = tmp_path / "quotes.sqlite3"
    initialize_database(db_path)
    repo = Mt5QuoteRepository(db_path, bucket_seconds=60)
    repo.save_quote("XAUUSD", 1_700_000_000_000, 2000.1, 2000.3)
    repo.save_quote("XAUUSD", 1_700_001_000_000, 2001.1, 2001.3)

    deleted = repo.cleanup_retention(cutoff_time_ms=1_700_000_500_000)

    assert deleted == 1
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM mt5_quote_samples").fetchone()[0] == 1
        assert conn.execute("SELECT bid FROM mt5_quote_samples").fetchone()[0] == 2001.1
