from __future__ import annotations

from tradingview_mcp.core.jobs.analyze_and_store_signal import analyze_and_store_signal
from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import TradeSignalRepository


def _tech(price: float = 4078.2) -> dict:
    return {
        "symbol": "OANDA:XAUUSD",
        "price_data": {"current_price": price, "change_percent": -0.3},
        "timeframe_context": {"timeframe": "15m", "trend": "Bearish"},
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
        "timeframes": {
            "15m": {"bias": "Bearish"},
            "1h": {"bias": "Bearish"},
            "4h": {"bias": "Bearish"},
            "1D": {"bias": "Bearish"},
        },
    }


def test_analyze_and_store_signal_scores_and_persists_compact_signal(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    calls = {}

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="KUCOIN",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: calls.setdefault(
            "technical", (symbol, exchange, timeframe)
        ) and _tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: calls.setdefault("mtf", (full_symbol, exchange)) and _mtf(),
    )

    assert result["stored"] is True
    assert result["symbol"] == "XAUUSD"
    assert result["exchange"] == "OANDA"
    assert result["instrument"] == "OANDA:XAUUSD"
    assert result["timeframe"] == "15m"
    assert calls["technical"] == ("XAUUSD", "OANDA", "15m")
    assert calls["mtf"] == ("OANDA:XAUUSD", "OANDA")
    assert result["bias"] == "SELL"
    assert result["decision"] == "TRADE"
    assert result["score"] >= 70
    assert result["price"] == 4078.2
    assert result["plan"]["entry_zone"]
    assert result["plan"]["sl"] > 4078.2
    assert result["plan"]["tp"][0] < 4078.2
    assert result["sd_range"]["sd1_low"] == 4070.2
    assert result["sd_range"]["sd1_high"] == 4086.2
    assert result["oi_proxy"]["magnet_zone"] == 4075
    assert result["oi_proxy"]["real_open_interest_available"] is False
    assert result["technical"]["source_symbol"] == "OANDA:XAUUSD"
    assert result["technical"]["reported_symbol"] == "OANDA:XAUUSD"
    assert result["technical"]["price_data"]["current_price"] == 4078.2
    assert result["technical"]["support_resistance"]["support_levels"] == [4075, 4062]
    assert "mtf_alignment" in result["score_breakdown"]
    assert "SD_OI_PROXY_ATTACHED" in result["reason_codes"]
    assert "STORED_FROM_AUTOMATION_CONNECTOR" in result["reason_codes"]

    latest = TradeSignalRepository(db_path).get_latest_trade_signal("XAUUSD", timeframe="15m")
    assert latest is not None
    assert latest["bias"] == "SELL"
    assert latest["score"] == result["score"]
    assert latest["plan"] == result["plan"]
    assert latest["instrument"] == "OANDA:XAUUSD"
    assert latest["technical"]["source_symbol"] == "OANDA:XAUUSD"
    assert "mtf_alignment" in latest["score_breakdown"]


def test_analyze_and_store_signal_stores_error_free_wait_signal_when_score_is_not_trade(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    tech = _tech(price=4078.2)
    tech["market_structure"] = {"trend": "Neutral/Ranging", "trend_strength": "Weak", "momentum_aligned": False}
    tech["market_sentiment"] = {"volatility": "Low", "buy_sell_signal": "NEUTRAL"}
    mtf = {
        "alignment": {"status": "MIXED/RANGING", "net_score": 0, "confidence": "Low"},
        "timeframes": {"15m": {}, "1h": {}, "4h": {}, "1D": {}},
    }

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


def test_analyze_and_store_signal_rejects_incomplete_mtf_payload(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: _tech(),
        multi_timeframe_fn=lambda full_symbol, exchange: {
            "alignment": {"status": "MOSTLY BEARISH", "net_score": -3, "confidence": "High"},
            "timeframes": {"15m": {}, "1h": {}},
        },
    )

    assert result["stored"] is False
    assert result["symbol"] == "XAUUSD"
    assert result["exchange"] == "OANDA"
    assert result["instrument"] == "OANDA:XAUUSD"
    assert result["error"]["code"] == "INCOMPLETE_MTF_PAYLOAD"
    assert result["error"]["missing_timeframes"] == ["4h", "1D"]


def test_analyze_and_store_signal_wraps_retryable_technical_upstream_error(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: {"error": "Analysis failed: upstream timeout"},
        multi_timeframe_fn=lambda full_symbol, exchange: _mtf(),
    )

    assert result["stored"] is False
    assert result["instrument"] == "OANDA:XAUUSD"
    assert result["error"]["code"] == "UPSTREAM_ERROR"
    assert result["error"]["retryable"] is True


def test_analyze_and_store_signal_marks_legacy_configuration_errors_non_retryable(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)

    result = analyze_and_store_signal(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="15m",
        db_path=db_path,
        analyze_coin_fn=lambda symbol, exchange, timeframe: {"error": "tradingview_ta is missing; run `uv sync`."},
        multi_timeframe_fn=lambda full_symbol, exchange: _mtf(),
    )

    assert result["stored"] is False
    assert result["error"]["code"] == "INTERNAL_ERROR"
    assert result["error"]["retryable"] is False
