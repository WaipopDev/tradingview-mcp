from __future__ import annotations

import importlib.util
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
        "score": 70,
    }
    base.update(overrides)
    return base


def test_global_entry_floor_allows_trade_at_min_score():
    mod = _load_entry_alert_module()

    assert mod.global_entry_floor_reason(_order()) is None


def test_global_entry_floor_blocks_non_trade_even_with_high_score():
    mod = _load_entry_alert_module()

    reason = mod.global_entry_floor_reason(_order(decision="WAIT_CONFIRMATION", score=95))

    assert reason is not None
    assert "decision=TRADE" in reason


def test_global_entry_floor_blocks_trade_below_min_score():
    mod = _load_entry_alert_module()

    reason = mod.global_entry_floor_reason(_order(score=69))

    assert reason is not None
    assert "ต่ำกว่า hard floor 70" in reason
