from __future__ import annotations

import json
import time

import pytest

from tradingview_mcp.core.services.mt5_market_data_service import (
    Mt5SnapshotError,
    analyze_mt5_coin,
    load_mt5_snapshot,
    run_mt5_multi_timeframe_analysis,
)


def _frame(close: float, trend: str, *, rsi: float = 55.0) -> dict:
    return {
        "bar": {"time": 1_786_000_000, "open": close - 1, "high": close + 2, "low": close - 2, "close": close, "tick_volume": 1200},
        "previous_bar": {"time": 1_785_999_100, "open": close - 2, "high": close + 1, "low": close - 3, "close": close - 1, "tick_volume": 1000},
        "rsi": rsi,
        "rsi_previous": rsi - 2,
        "atr": 8.0,
        "ema20": close - 2,
        "ema50": close - 4,
        "ema200": close - 20,
        "macd": 2.1,
        "macd_signal": 1.4,
        "macd_histogram": 0.7,
        "bb_upper": close + 10,
        "bb_middle": close,
        "bb_lower": close - 10,
        "adx": 28,
        "avg_tick_volume": 1000,
        "trend": trend,
        "support": [close - 12, close - 20],
        "resistance": [close + 12, close + 20],
    }


def _snapshot(now_ms: int | None = None) -> dict:
    now_ms = now_ms or int(time.time() * 1000)
    return {
        "schema_version": 1,
        "source": "MT5",
        "broker": "Demo-Server",
        "symbol": "GOLD",
        "canonical_symbol": "XAUUSD",
        "generated_at_msc": now_ms,
        "tick": {"time_msc": now_ms, "bid": 4260.10, "ask": 4260.30, "last": 0, "spread_points": 20, "digits": 2, "point": 0.01},
        "timeframes": {
            "15m": _frame(4260.2, "Bullish"),
            "1h": _frame(4259.8, "Bullish"),
            "4h": _frame(4255.0, "Bullish"),
            "1D": _frame(4240.0, "Bullish"),
        },
    }


def test_load_mt5_snapshot_validates_freshness_and_symbol(tmp_path):
    path = tmp_path / "GOLD.json"
    path.write_text(json.dumps(_snapshot()), encoding="utf-8")

    loaded = load_mt5_snapshot(path, symbol="XAUUSD", max_age_seconds=5)

    assert loaded["symbol"] == "GOLD"
    assert loaded["canonical_symbol"] == "XAUUSD"


def test_load_mt5_snapshot_rejects_stale_tick(tmp_path):
    path = tmp_path / "GOLD.json"
    path.write_text(json.dumps(_snapshot(int(time.time() * 1000) - 10_000)), encoding="utf-8")

    with pytest.raises(Mt5SnapshotError, match="stale"):
        load_mt5_snapshot(path, max_age_seconds=5)


def test_analyze_mt5_coin_maps_snapshot_to_existing_technical_contract(tmp_path):
    path = tmp_path / "GOLD.json"
    path.write_text(json.dumps(_snapshot()), encoding="utf-8")

    technical = analyze_mt5_coin("XAUUSD", "MT5", "15m", snapshot_path=path)

    assert technical["symbol"] == "MT5:GOLD"
    assert technical["price_data"]["current_price"] == pytest.approx(4260.2)
    assert technical["price_data"]["volume"] == 1200
    assert technical["rsi"]["value"] == 55
    assert technical["atr"]["value"] == 8
    assert technical["market_structure"]["trend"] == "Bullish"
    assert technical["support_resistance"]["support_levels"] == [4248.2, 4240.2]
    assert technical["source"] == "MT5"


def test_run_mt5_multi_timeframe_analysis_builds_required_alignment(tmp_path):
    path = tmp_path / "GOLD.json"
    path.write_text(json.dumps(_snapshot()), encoding="utf-8")

    mtf = run_mt5_multi_timeframe_analysis("MT5:GOLD", "MT5", snapshot_path=path)

    assert set(mtf["timeframes"]) == {"15m", "1h", "4h", "1D"}
    assert mtf["alignment"]["net_score"] == 4
    assert mtf["alignment"]["status"] == "FULLY ALIGNED BULLISH"
    assert mtf["source"] == "MT5"
