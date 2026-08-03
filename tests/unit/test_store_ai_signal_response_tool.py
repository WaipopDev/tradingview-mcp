from __future__ import annotations

from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.server import store_ai_signal_response
from tradingview_mcp.core.storage.repositories import SignalAiResponseRepository


def test_store_ai_signal_response_tool_persists_cached_response(tmp_path, monkeypatch):
    db_path = tmp_path / "signals.sqlite3"
    monkeypatch.setenv("TRADINGVIEW_MCP_DB_PATH", str(db_path))
    initialize_database(db_path)

    result = store_ai_signal_response(
        symbol="XAUUSD",
        timeframe="15m",
        signal_fingerprint="abc123",
        ai_response="SELL 4090-4100 SL 4102 TP 4075/4062",
        source="telegram",
    )

    assert result["stored"] is True
    assert result["symbol"] == "XAUUSD"
    assert result["timeframe"] == "15m"
    assert result["signal_fingerprint"] == "abc123"
    assert SignalAiResponseRepository(db_path).get_cached_response("XAUUSD", "15m", "abc123") == "SELL 4090-4100 SL 4102 TP 4075/4062"
