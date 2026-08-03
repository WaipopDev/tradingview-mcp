from __future__ import annotations

from tradingview_mcp.core.jobs.analyze_and_store_signal import analyze_and_store_signal
from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import TradeSignalRepository


def _tech(price: float = 4078.2) -> dict:
    return {
        "price_data": {"current_price": price, "change_percent": -0.3},
        "market_structure": {"trend": "Bearish", "trend_strength": "Strong", "momentum_aligned": True},
        "market_sentiment": {"volatility": "Medium", "buy_sell_signal": "SELL"},
        "rsi": {"value": 42, "signal": "Bearish"},
        "macd": {"crossover": "Bearish"},
        "bollinger_bands": {"width": 0.035, "squeeze": False, "position": "Lower Half"},
        "volume_analysis": {"signal": "High", "ratio": 2.1},
        "atr": {"value": 8.0, "volatility": "Medium", "percent_of_price": 0.2},
        "support_resistance": {
            "support_levels": [4075, 4062],
            "resistance_levels": [4090, 4100],
        },
    }


def _mtf() -> dict:
    return {
        "alignment": {"status": "MOSTLY BEARISH", "net_score": -3, "confidence": "High"},
        "timeframes": {"15m": {"bias": "Bearish"}, "1h": {"bias": "Bearish"}},
    }


def test_analyze_and_store_signal_scores_and_persists_compact_signal(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: _tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: _mtf(),
    )

    assert result["stored"] is True
    assert result["symbol"] == "XAUUSD"
    assert result["exchange"] == "OANDA"
    assert result["timeframe"] == "15m"
    assert result["bias"] == "SELL"
    assert result["decision"] == "TRADE"
    assert result["score"] >= 70
    assert result["price"] == 4078.2
    assert result["plan"]["entry_zone"]
    assert result["plan"]["sl"] > 4078.2
    assert result["plan"]["tp"][0] < 4078.2
    assert "STORED_FROM_AUTOMATION_CONNECTOR" in result["reason_codes"]

    latest = TradeSignalRepository(db_path).get_latest_trade_signal("XAUUSD", timeframe="15m")
    assert latest is not None
    assert latest["bias"] == "SELL"
    assert latest["score"] == result["score"]
    assert latest["plan"] == result["plan"]


def test_analyze_and_store_signal_stores_error_free_wait_signal_when_score_is_not_trade(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    tech = _tech(price=4078.2)
    tech["market_structure"] = {"trend": "Neutral/Ranging", "trend_strength": "Weak", "momentum_aligned": False}
    tech["market_sentiment"] = {"volatility": "Low", "buy_sell_signal": "NEUTRAL"}
    mtf = {"alignment": {"status": "MIXED/RANGING", "net_score": 0, "confidence": "Low"}, "timeframes": {}}

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: tech,
        multi_timeframe_fn=lambda full_symbol, exchange: mtf,
    )

    assert result["stored"] is True
    assert result["bias"] == "WAIT"
    assert result["decision"] == "WAIT_CONFIRMATION"
    assert result["plan"]["entry_zone"] is None
    assert result["plan"]["tp"] == []
