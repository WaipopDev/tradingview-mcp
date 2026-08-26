from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path


def _load_entry_alert_module():
    path = Path(__file__).resolve().parents[3] / "scripts" / "hermes_runtime" / "trad_entry_alert.py"
    spec = importlib.util.spec_from_file_location("trad_entry_alert_runtime", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _order(**overrides):
    base = {
        "direction": "BUY",
        "decision": "TRADE",
        "score": 60,
        "signal_score": 60,
    }
    base.update(overrides)
    return base


def test_global_entry_floor_allows_trade_at_min_score():
    mod = _load_entry_alert_module()

    assert mod.global_entry_floor_reason(_order()) is None


def test_global_entry_floor_allows_wait_confirmation_when_both_scores_pass():
    mod = _load_entry_alert_module()

    reason = mod.global_entry_floor_reason(
        _order(decision="WAIT_CONFIRMATION", score=80, signal_score=65)
    )

    assert reason is None


def test_global_entry_floor_blocks_trade_below_min_score():
    mod = _load_entry_alert_module()

    reason = mod.global_entry_floor_reason(_order(score=59))

    assert reason is not None
    assert "setup score 59/100" in reason


def test_global_entry_floor_blocks_weak_engine_score_even_if_setup_score_is_high():
    mod = _load_entry_alert_module()

    reason = mod.global_entry_floor_reason(
        _order(decision="WAIT_CONFIRMATION", score=80, signal_score=44)
    )

    assert reason is not None
    assert "engine score 44/100" in reason


def _order58_row():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE signal (
          id INTEGER, symbol TEXT, timeframe TEXT, price REAL, bias TEXT,
          decision TEXT, total_score INTEGER, regime TEXT,
          sd_range_json TEXT, technical_json TEXT, created_at TEXT
        )
        """
    )
    sd = {
        "sd1_low": 4257.763,
        "sd1_high": 4273.037,
        "sd2_low": 4250.126,
        "sd2_high": 4280.674,
    }
    tech = {
        "price_data": {
            "current_price": 4265.4,
            "open": 4265.4,
            "high": 4265.4,
            "low": 4265.4,
            "close": 4265.4,
            "volume": 1,
        },
        "support_resistance": {"pivot": 4193.5767},
        "market_structure": {"trend": "Neutral/Ranging"},
        "market_sentiment": {"momentum": "Bearish"},
        "rsi": {"value": 47.62},
        "macd": {"crossover": "Bearish"},
        "atr": {"value": 7.637},
    }
    con.execute(
        "INSERT INTO signal VALUES (940,'XAUUSD','15m',4265.4,'WAIT','WAIT_CONFIRMATION',44,'range_mean_reversion',?,?, '2026-08-06T10:45:35+00:00')",
        (json.dumps(sd), json.dumps(tech)),
    )
    return con, con.execute("SELECT * FROM signal").fetchone()


def test_order58_incomplete_one_tick_candle_is_rejected():
    mod = _load_entry_alert_module()
    con, row = _order58_row()
    try:
        reason = mod.signal_quality_reason(row)
    finally:
        con.close()

    assert reason is not None
    assert "OHLC" in reason
    assert "volume=1" in reason


def test_order58_invalid_sell_geometry_is_rejected():
    mod = _load_entry_alert_module()
    con, row = _order58_row()
    try:
        order, _ = mod.derive_order(row)
        reason = mod.order_geometry_reason(order)
    finally:
        con.close()

    assert reason is not None
    assert "SELL" in reason
    assert order["sl"] > order["entry_high"]


def test_duplicate_guard_ignores_invalid_historical_order():
    mod = _load_entry_alert_module()
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE trade_plan_outcomes (
          id INTEGER, symbol TEXT, timeframe TEXT, direction TEXT,
          entry_low REAL, entry_high REAL, sl REAL, tp1 REAL, tp2 REAL, tp3 REAL,
          status TEXT, result TEXT, created_at TEXT, closed_at TEXT
        )
        """
    )
    con.execute(
        """
        INSERT INTO trade_plan_outcomes VALUES
        (58,'XAUUSD','15m','SELL',4193.5767,4273.037,4201.5767,4257.763,4250.126,NULL,
         'closed','SL','2099-01-01T00:00:00+00:00','2099-01-01T00:00:00+00:00')
        """
    )
    candidate = {
        "symbol": "XAUUSD", "timeframe": "15m", "direction": "SELL",
        "entry_low": 4265.0, "entry_high": 4270.0, "sl": 4276.0,
        "tp1": 4255.0, "tp2": 4250.0, "tp3": None,
        "price": 4265.0, "atr": 7.0, "decision": "TRADE", "score": 80,
        "raw_bias": "SELL",
    }

    assert mod.recent_similar_zone_reason(con, candidate) is None
