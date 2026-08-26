from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path


def _load_check_entry_now_module():
    path = Path(__file__).resolve().parents[3] / "scripts" / "hermes_runtime" / "trad_check_entry_now.py"
    spec = importlib.util.spec_from_file_location("trad_check_entry_now_runtime", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_entry_message_includes_price_and_reason():
    mod = _load_check_entry_now_module()

    message = mod.no_entry_message("XAUUSD", 4265.4, "งดส่ง SELL: engine score 44/100 ต่ำกว่าเกณฑ์ 60")

    assert "XAUUSD ตอนนี้: 4265.4" in message
    assert "ยังไม่มีจุดเข้าตามเกณฑ์ตอนนี้" in message
    assert "engine score 44/100" in message


def test_no_entry_message_handles_missing_price():
    mod = _load_check_entry_now_module()

    message = mod.no_entry_message("XAUUSD", None, "no data")

    assert "XAUUSD ตอนนี้: -" in message


def _low_score_db(tmp_path):
    db_path = tmp_path / "trad.sqlite3"
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE trade_signals (
          id INTEGER, symbol TEXT, timeframe TEXT, price REAL, bias TEXT,
          decision TEXT, total_score INTEGER, regime TEXT,
          sd_range_json TEXT, technical_json TEXT, created_at TEXT
        )
        """
    )
    sd = {"sd1_low": 4257.763, "sd1_high": 4273.037, "sd2_low": 4250.126, "sd2_high": 4280.674}
    tech = {
        "price_data": {"open": 4263.1, "high": 4266.8, "low": 4262.5, "close": 4265.4, "volume": 1200},
        "support_resistance": {"pivot": 4193.5767},
        "market_structure": {"trend": "Neutral/Ranging"},
        "market_sentiment": {"momentum": "Bearish"},
        "rsi": {"value": 47.62},
        "macd": {"crossover": "Bearish"},
        "atr": {"value": 7.637},
    }
    from datetime import datetime, timezone
    con.execute(
        "INSERT INTO trade_signals VALUES (940,'XAUUSD','15m',4265.4,'WAIT','WAIT_CONFIRMATION',44,'range_mean_reversion',?,?,?)",
        (json.dumps(sd), json.dumps(tech), datetime.now(timezone.utc).isoformat()),
    )
    con.commit()
    con.close()
    return db_path


def test_main_dry_run_reports_no_entry_reason(tmp_path, capsys):
    mod = _load_check_entry_now_module()
    db_path = _low_score_db(tmp_path)

    exit_code = mod.main([
        "--db-path", str(db_path),
        "--symbol", "XAUUSD",
        "--timeframe", "15m",
        "--dry-run",
        "--no-refresh",
    ])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ยังไม่มีจุดเข้าตามเกณฑ์ตอนนี้" in out
    assert "setup score 50/100" in out


def test_main_dry_run_on_stale_signal_says_stale(tmp_path, capsys):
    mod = _load_check_entry_now_module()
    db_path = tmp_path / "trad.sqlite3"
    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE trade_signals (
          id INTEGER, symbol TEXT, timeframe TEXT, price REAL, bias TEXT,
          decision TEXT, total_score INTEGER, regime TEXT,
          sd_range_json TEXT, technical_json TEXT, created_at TEXT
        )
        """
    )
    con.execute(
        "INSERT INTO trade_signals VALUES (1,'XAUUSD','15m',4200.0,'WAIT','WAIT_CONFIRMATION',50,'range','{}','{}','2020-01-01T00:00:00+00:00')"
    )
    con.commit()
    con.close()

    exit_code = mod.main([
        "--db-path", str(db_path),
        "--symbol", "XAUUSD",
        "--timeframe", "15m",
        "--dry-run",
        "--no-refresh",
    ])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "ข้อมูลเก่าเกินไป" in out
