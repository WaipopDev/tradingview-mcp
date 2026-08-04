from __future__ import annotations

import json
import sqlite3

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
            "instrument": "OANDA:XAUUSD",
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
            "technical_json": json.dumps({"source_symbol": "OANDA:XAUUSD", "reported_symbol": "OANDA:XAUUSD"}),
            "levels_json": json.dumps({"support": [4075, 4062], "resistance": [4090, 4100]}),
            "score_breakdown_json": json.dumps({"mtf_alignment": 25, "oi_volume_proxy": 10}),
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

    assert latest is not None
    assert latest["symbol"] == "XAUUSD"
    assert latest["exchange"] == "OANDA"
    assert latest["instrument"] == "OANDA:XAUUSD"
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
    assert latest["technical"]["source_symbol"] == "OANDA:XAUUSD"
    assert latest["levels"]["support"] == [4075, 4062]
    assert latest["score_breakdown"] == {"mtf_alignment": 25, "oi_volume_proxy": 10}
    assert latest["reason_codes"] == ["MTF_SELL_ALIGNMENT", "RR_OK"]
    assert latest["data_age_seconds"] >= 0


def test_trade_signal_repository_returns_none_when_no_signal(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = TradeSignalRepository(db_path)

    assert repo.get_latest_trade_signal("XAUUSD") is None


def test_initialize_database_migrates_trade_signal_new_payload_columns(tmp_path):
    db_path = tmp_path / "old_signals.sqlite3"
    old_schema = """
    CREATE TABLE trade_signals (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      symbol TEXT NOT NULL,
      exchange TEXT DEFAULT 'OANDA',
      timeframe TEXT DEFAULT '15m',
      price REAL,
      bias TEXT NOT NULL,
      decision TEXT NOT NULL,
      entry_low REAL,
      entry_high REAL,
      sl REAL,
      tp1 REAL,
      tp2 REAL,
      tp3 REAL,
      confidence TEXT,
      total_score INTEGER,
      regime TEXT,
      sd_range_json TEXT,
      oi_proxy_json TEXT,
      volume_json TEXT,
      levels_json TEXT,
      reason_codes_json TEXT,
      ai_gate_json TEXT,
      source_score_id INTEGER,
      status TEXT DEFAULT 'active',
      created_at TEXT NOT NULL
    );
    """
    with sqlite3.connect(db_path) as conn:
        conn.executescript(old_schema)

    initialize_database(db_path)

    with sqlite3.connect(db_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(trade_signals)").fetchall()}

    assert {"instrument", "technical_json", "score_breakdown_json"}.issubset(columns)
