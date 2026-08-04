from __future__ import annotations

from tradingview_mcp.core.jobs.analyze_and_store_signal import analyze_and_store_signal
from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import SignalAiResponseRepository


def _trade_tech() -> dict:
    return {
        "symbol": "OANDA:XAUUSD",
        "price_data": {"current_price": 4078.2, "change_percent": -0.3},
        "market_structure": {"trend": "Bearish", "trend_strength": "Strong", "momentum_aligned": True},
        "market_sentiment": {"volatility": "Medium", "buy_sell_signal": "SELL"},
        "rsi": {"value": 42, "signal": "Bearish"},
        "macd": {"crossover": "Bearish"},
        "bollinger_bands": {"width": 0.035, "squeeze": False, "position": "Lower Half"},
        "volume_analysis": {"signal": "High", "ratio": 2.1},
        "atr": {"value": 8.0, "volatility": "Medium", "percent_of_price": 0.2},
        "support_resistance": {"support_levels": [4075, 4062], "resistance_levels": [4090, 4100]},
    }


def _trade_mtf() -> dict:
    return {
        "alignment": {"status": "MOSTLY BEARISH", "net_score": -3, "confidence": "High"},
        "timeframes": {"15m": {}, "1h": {}, "4h": {}, "1D": {}},
    }


def test_analyze_and_store_signal_returns_ai_gate_for_trade_condition(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = analyze_and_store_signal(
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: _trade_tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: _trade_mtf(),
    )

    assert result["decision"] == "TRADE"
    assert result["ai_gate"]["should_ask_ai"] is True
    assert result["ai_gate"]["reason"] == "TRADE_SIGNAL_NEEDS_AI_SUMMARY"
    assert result["ai_gate"]["signal_fingerprint"]


def test_analyze_and_store_signal_reuses_cached_ai_response_for_same_signal(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    first = analyze_and_store_signal(
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: _trade_tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: _trade_mtf(),
    )
    SignalAiResponseRepository(db_path).insert_ai_response(
        symbol="XAUUSD",
        timeframe="15m",
        signal_fingerprint=first["ai_gate"]["signal_fingerprint"],
        ai_response="SELL 4090-4100 SL 4102 TP 4075/4062",
    )

    second = analyze_and_store_signal(
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: _trade_tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: _trade_mtf(),
    )

    assert second["ai_gate"]["should_ask_ai"] is False
    assert second["ai_gate"]["reason"] == "CACHED_AI_RESPONSE_REUSABLE"
    assert second["ai_gate"]["cached_response"] == "SELL 4090-4100 SL 4102 TP 4075/4062"
