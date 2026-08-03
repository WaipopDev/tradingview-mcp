from __future__ import annotations

from tradingview_mcp.core.jobs.score_latest_signal import store_compact_trade_signal
from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import TradeSignalRepository


def test_store_compact_trade_signal_persists_and_returns_latest(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = store_compact_trade_signal(
        {
            "symbol": "XAUUSD",
            "exchange": "OANDA",
            "timeframe": "15m",
            "price": 4078.2,
            "bias": "BUY",
            "decision": "WAIT_CONFIRMATION",
            "score": 61,
            "plan": {"entry_zone": "4075-4078", "sl": 4068, "tp": [4088, 4098]},
            "reason_codes": ["LOW_VOL_WAIT_CONFIRMATION"],
            "created_at": "2026-08-03T10:05:00+00:00",
        },
        db_path=db_path,
    )

    assert result["id"] == 1
    assert result["latest"]["symbol"] == "XAUUSD"
    assert result["latest"]["score"] == 61
    assert result["latest"]["plan"]["entry_zone"] == "4075-4078"

    repo_latest = TradeSignalRepository(db_path).get_latest_trade_signal("XAUUSD")
    assert repo_latest is not None
    assert repo_latest["reason_codes"] == ["LOW_VOL_WAIT_CONFIRMATION"]


def test_store_compact_trade_signal_defaults_created_at(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = store_compact_trade_signal(
        {
            "symbol": "XAUUSD",
            "bias": "WAIT",
            "decision": "WAIT_CONFIRMATION",
            "plan": {"entry_zone": "4075", "tp": []},
        },
        db_path=db_path,
    )

    assert result["id"] == 1
    assert result["latest"]["created_at"]
