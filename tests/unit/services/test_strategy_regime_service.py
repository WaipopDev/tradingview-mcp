from tradingview_mcp.core.services.strategy_regime_service import score_strategy_regime


def test_score_strategy_regime_prefers_buy_for_aligned_trend_breakout():
    technical = {
        "price_data": {"current_price": 2500, "change_percent": 1.4},
        "market_structure": {"trend": "Bullish", "trend_strength": "Strong", "momentum_aligned": True},
        "market_sentiment": {"volatility": "Medium", "buy_sell_signal": "BUY"},
        "rsi": {"value": 58, "signal": "Bullish"},
        "macd": {"crossover": "Bullish"},
        "bollinger_bands": {"width": 0.035, "squeeze": False, "position": "Upper Half"},
        "volume_analysis": {"signal": "High", "ratio": 2.2},
        "atr": {"volatility": "Medium", "percent_of_price": 1.2},
    }
    mtf = {
        "alignment": {"status": "MOSTLY BULLISH", "net_score": 3, "confidence": "High"},
        "timeframes": {
            "1D": {"bias": "Bullish"},
            "4h": {"bias": "Bullish"},
            "1h": {"bias": "Bullish"},
            "15m": {"bias": "Bullish"},
        },
    }

    result = score_strategy_regime("XAUUSD", "OANDA", technical, mtf)

    assert result["bias"] == "BUY"
    assert result["decision"] == "TRADE"
    assert result["total_score"] >= 70
    assert result["regime"]["primary"] == "trend_momentum"
    assert "trend_following" in result["strategy_family"]["primary"]


def test_score_strategy_regime_waits_for_mixed_range_even_when_oversold():
    technical = {
        "price_data": {"current_price": 2500, "change_percent": -0.2},
        "market_structure": {"trend": "Neutral/Ranging", "trend_strength": "Weak", "momentum_aligned": False},
        "market_sentiment": {"volatility": "Low", "buy_sell_signal": "NEUTRAL"},
        "rsi": {"value": 27, "signal": "Oversold"},
        "macd": {"crossover": "Neutral"},
        "bollinger_bands": {"width": 0.018, "squeeze": True, "position": "Below Lower Band"},
        "volume_analysis": {"signal": "Normal", "ratio": 1.0},
        "atr": {"volatility": "Low", "percent_of_price": 0.7},
    }
    mtf = {"alignment": {"status": "MIXED/RANGING", "net_score": 0, "confidence": "Low"}, "timeframes": {}}

    result = score_strategy_regime("XAUUSD", "OANDA", technical, mtf)

    assert result["bias"] == "WAIT"
    assert result["decision"] == "WAIT_CONFIRMATION"
    assert result["regime"]["primary"] in {"range_mean_reversion", "low_vol_squeeze"}
    assert result["score_breakdown"]["mtf_alignment"] < 15


def test_score_strategy_regime_marks_conflicting_flow_as_wait_confirmation():
    technical = {
        "price_data": {"current_price": 2500, "change_percent": 0.8},
        "market_structure": {"trend": "Bullish", "trend_strength": "Strong", "momentum_aligned": True},
        "market_sentiment": {"volatility": "Medium", "buy_sell_signal": "BUY"},
        "rsi": {"value": 61, "signal": "Bullish"},
        "macd": {"crossover": "Bullish"},
        "bollinger_bands": {"width": 0.03, "squeeze": False, "position": "Upper Half"},
        "volume_analysis": {"signal": "High", "ratio": 2.0},
        "atr": {"volatility": "Medium", "percent_of_price": 1.1},
    }
    mtf = {"alignment": {"status": "MOSTLY BULLISH", "net_score": 3, "confidence": "High"}, "timeframes": {}}
    flow = {"direction": "SELL", "confidence": "High", "source": "GLD unusual options activity"}

    result = score_strategy_regime("XAUUSD", "OANDA", technical, mtf, flow_context=flow)

    assert result["bias"] == "BUY"
    assert result["decision"] == "WAIT_CONFIRMATION"
    assert result["score_breakdown"]["options_futures_sentiment_proxy"] <= 3
    assert any("conflicts" in note.lower() for note in result["notes"])


def test_score_strategy_regime_accepts_oi_proxy_limitation_without_changing_contract():
    technical = {
        "price_data": {"current_price": 2500, "change_percent": 1.0},
        "market_structure": {"trend": "Bullish", "trend_strength": "Strong", "momentum_aligned": True},
        "market_sentiment": {"volatility": "Medium", "buy_sell_signal": "BUY"},
        "rsi": {"value": 57, "signal": "Bullish"},
        "macd": {"crossover": "Bullish"},
        "bollinger_bands": {"width": 0.03, "squeeze": False, "position": "Upper Half"},
        "volume_analysis": {"signal": "High", "ratio": 2.0},
        "atr": {"volatility": "Medium", "percent_of_price": 1.0},
    }
    mtf = {"alignment": {"status": "MOSTLY BULLISH", "net_score": 3, "confidence": "High"}, "timeframes": {}}
    flow = {
        "direction": "BUY",
        "confidence": "High",
        "source": "OANDA:XAUUSD intraday ATR + support/resistance OI proxy",
        "real_open_interest_available": False,
        "limitation": "OANDA:XAUUSD spot/CFD has no centralised open interest; proxy only.",
    }

    result = score_strategy_regime("XAUUSD", "OANDA", technical, mtf, flow_context=flow)

    assert {"bias", "decision", "total_score", "score_breakdown", "regime", "strategy_family", "thresholds", "notes"}.issubset(result)
    assert result["bias"] == "BUY"
    assert result["decision"] == "TRADE"
    assert result["score_breakdown"]["options_futures_sentiment_proxy"] == 15
    assert any("proxy only" in note.lower() for note in result["notes"])
    assert any("real_open_interest_available=false" in note for note in result["notes"])
