from __future__ import annotations

from tradingview_mcp.core.services.sd_oi_proxy_service import build_sd_oi_proxy


def _technical(price: float = 4078.2) -> dict:
    return {
        "price_data": {"current_price": price},
        "atr": {"value": 8.0, "volatility": "Medium", "percent_of_price": 0.2},
        "volume_analysis": {"signal": "High", "ratio": 2.1},
        "support_resistance": {
            "support_levels": [4075, 4062],
            "resistance_levels": [4090, 4100],
        },
    }


def test_build_sd_oi_proxy_derives_expected_range_from_atr_and_nearest_magnet():
    result = build_sd_oi_proxy("XAUUSD", _technical(), "15m")

    assert result["sd_range"]["anchor_price"] == 4078.2
    assert result["sd_range"]["expected_move_points"] == 8.0
    assert result["sd_range"]["sd1_low"] == 4070.2
    assert result["sd_range"]["sd1_high"] == 4086.2
    assert result["sd_range"]["sd2_low"] == 4062.2
    assert result["sd_range"]["sd2_high"] == 4094.2
    assert result["oi_proxy"]["magnet_zone"] == 4075
    assert result["oi_proxy"]["source"] == "OANDA:XAUUSD intraday ATR + support/resistance OI proxy"
    assert result["flow_context"]["direction"] in {"BUY", "SELL", "WAIT"}
    assert result["flow_context"]["source"] == "OANDA:XAUUSD intraday ATR + support/resistance OI proxy"
    assert result["flow_context"]["real_open_interest_available"] is False
    assert "not real exchange OI" in result["flow_context"]["limitation"]


def test_build_sd_oi_proxy_marks_spot_oi_as_proxy_not_real_open_interest():
    result = build_sd_oi_proxy("XAUUSD", _technical(), "15m")

    assert result["oi_proxy"]["real_open_interest_available"] is False
    assert "OANDA:XAUUSD" in result["oi_proxy"]["limitation"]
    assert "no centralised open interest" in result["oi_proxy"]["limitation"]
    assert "proxy" in result["oi_proxy"]["limitation"].lower()


def test_build_sd_oi_proxy_missing_price_keeps_safe_proxy_limitation():
    result = build_sd_oi_proxy("XAUUSD", {"price_data": {}}, "15m")

    assert result["sd_range"] == {}
    assert result["oi_proxy"]["real_open_interest_available"] is False
    assert result["flow_context"]["direction"] == "WAIT"
    assert result["flow_context"]["real_open_interest_available"] is False
    assert "not real exchange OI" in result["flow_context"]["limitation"]
