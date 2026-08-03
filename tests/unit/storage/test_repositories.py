from __future__ import annotations

import json

from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import TradeSignalRepository


def test_trade_signal_repository_reads_latest_signal_as_compact_payload(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = TradeSignalRepository(db_path)

    repo.insert_trade_signal(
        {
            "symbol": "XAUUSD",
            "exchange": "OANDA",
            "timeframe": "15m",
            "price": 4078.2,
            "bias": "SELL",
            "decision": "TRADE",
            "entry_low": 4088.0,
            "entry_high": 4093.0,
            "sl": 4102.0,
            "tp1": 4075.0,
            "tp2": 4062.0,
            "tp3": 4050.0,
            "confidence": "High",
            "total_score": 74,
            "regime": "range_mean_reversion",
            "sd_range_json": json.dumps({"anchor": 4100, "sd1_low": 4075, "sd1_high": 4125}),
            "oi_proxy_json": json.dumps({"magnet": 4100, "flow_bias": "SELL_WEAK"}),
            "volume_json": json.dumps({"state": "above_average", "ratio": 1.8}),
            "levels_json": json.dumps({"support": [4075, 4062], "resistance": [4090, 4100]}),
            "reason_codes_json": json.dumps(["MTF_SELL_ALIGNMENT", "RR_OK"]),
            "created_at": "2026-08-03T10:00:00+00:00",
        }
    )
    repo.insert_trade_signal(
        {
            "symbol": "XAUUSD",
            "exchange": "OANDA",
            "timeframe": "5m",
            "price": 4081.0,
            "bias": "WAIT",
            "decision": "WAIT_CONFIRMATION",
            "created_at": "2026-08-03T10:01:00+00:00",
        }
    )

    latest = repo.get_latest_trade_signal("XAUUSD", timeframe="15m")

    assert latest["symbol"] == "XAUUSD"
    assert latest["exchange"] == "OANDA"
    assert latest["timeframe"] == "15m"
    assert latest["price"] == 4078.2
    assert latest["bias"] == "SELL"
    assert latest["decision"] == "TRADE"
    assert latest["score"] == 74
    assert latest["plan"] == {
        "entry_zone": "4088-4093",
        "sl": 4102.0,
        "tp": [4075.0, 4062.0, 4050.0],
    }
    assert latest["sd_range"]["sd1_low"] == 4075
    assert latest["oi_proxy"]["magnet"] == 4100
    assert latest["volume"]["ratio"] == 1.8
    assert latest["levels"]["support"] == [4075, 4062]
    assert latest["reason_codes"] == ["MTF_SELL_ALIGNMENT", "RR_OK"]
    assert latest["data_age_seconds"] >= 0


def test_trade_signal_repository_returns_none_when_no_signal(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = TradeSignalRepository(db_path)

    assert repo.get_latest_trade_signal("XAUUSD") is None
