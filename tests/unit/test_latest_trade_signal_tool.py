from __future__ import annotations

import json

from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import TradeSignalRepository
from tradingview_mcp.server import latest_trade_signal


def test_latest_trade_signal_reads_compact_payload_from_configured_db(tmp_path, monkeypatch):
    db_path = tmp_path / "signals.sqlite3"
    monkeypatch.setenv("TRADINGVIEW_MCP_DB_PATH", str(db_path))
    initialize_database(db_path)
    repo = TradeSignalRepository(db_path)
    repo.insert_trade_signal(
        {
            "symbol": "XAUUSD",
            "exchange": "OANDA",
            "instrument": "OANDA:XAUUSD",
            "timeframe": "15m",
            "price": 4078.2,
            "bias": "SELL",
            "decision": "TRADE",
            "total_score": 74,
            "entry_low": 4088,
            "entry_high": 4093,
            "sl": 4102,
            "tp1": 4075,
            "tp2": 4062,
            "technical_json": {"source_symbol": "OANDA:XAUUSD"},
            "score_breakdown_json": {"mtf_alignment": 25},
            "reason_codes_json": json.dumps(["MTF_SELL_ALIGNMENT"]),
            "created_at": "2026-08-03T10:00:00+00:00",
        }
    )

    result = latest_trade_signal("XAUUSD", timeframe="15m")

    assert result["symbol"] == "XAUUSD"
    assert result["instrument"] == "OANDA:XAUUSD"
    assert result["bias"] == "SELL"
    assert result["decision"] == "TRADE"
    assert result["score"] == 74
    assert result["plan"]["entry_zone"] == "4088-4093"
    assert result["technical"]["source_symbol"] == "OANDA:XAUUSD"
    assert result["score_breakdown"] == {"mtf_alignment": 25}
    assert result["reason_codes"] == ["MTF_SELL_ALIGNMENT"]


def test_latest_trade_signal_returns_error_envelope_when_empty(tmp_path, monkeypatch):
    db_path = tmp_path / "signals.sqlite3"
    monkeypatch.setenv("TRADINGVIEW_MCP_DB_PATH", str(db_path))
    initialize_database(db_path)

    result = latest_trade_signal("XAUUSD")

    assert result["error"]["code"] == "NO_SIGNAL_FOUND"
    assert result["symbol"] == "XAUUSD"
