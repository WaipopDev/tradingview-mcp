from tradingview_mcp.core.services.oi_expected_range_service import score_oi_expected_range


def test_score_oi_expected_range_rejects_lower_sd1_as_buy_proxy():
    result = score_oi_expected_range(
        symbol="XAUUSD",
        current_price=4076,
        anchor_price=4100,
        expected_move=25,
        oi_magnet_zone=4100,
        basis=25,
        proxy_underlying_price=4051,
        price_action_state="rejected_lower_sd1",
        volatility_state="low",
        expiry_context=True,
    )

    assert result["range_levels"]["sd1_low"] == 4075
    assert result["range_levels"]["sd1_high"] == 4125
    assert result["basis_adjustment"]["basis"] == 25
    assert result["range_state"] == "near_lower_sd1"
    assert result["flow_context"] == {
        "direction": "BUY",
        "confidence": "High",
        "source": "OI expected range / magnet proxy",
    }
    assert result["regime_hint"] == "range_mean_reversion"


def test_score_oi_expected_range_breakout_above_sd1_with_expansion_is_buy_breakout():
    result = score_oi_expected_range(
        symbol="XAUUSD",
        current_price=4130,
        anchor_price=4100,
        expected_move=25,
        oi_magnet_zone=4100,
        price_action_state="breakout_up",
        volatility_state="expanding",
        volume_state="high",
    )

    assert result["range_state"] == "outside_upper_sd1"
    assert result["flow_context"]["direction"] == "BUY"
    assert result["flow_context"]["confidence"] == "High"
    assert result["regime_hint"] == "trend_momentum"


def test_score_oi_expected_range_inside_sd1_near_magnet_waits():
    result = score_oi_expected_range(
        symbol="XAUUSD",
        current_price=4103,
        anchor_price=4100,
        expected_move=25,
        oi_magnet_zone=4100,
        price_action_state="inside_range",
        volatility_state="low",
    )

    assert result["range_state"] == "inside_sd1_near_magnet"
    assert result["flow_context"]["direction"] == "WAIT"
    assert result["flow_context"]["confidence"] == "Medium"
    assert result["regime_hint"] == "range_magnet"


def test_score_oi_expected_range_treats_missing_basis_as_neutral_for_proxy_underlying():
    result = score_oi_expected_range(
        symbol="XAUUSD",
        current_price=4100,
        anchor_price=4100,
        expected_move=25,
        proxy_underlying_price=4075,
        oi_magnet_zone=4100,
    )

    assert result["basis_adjustment"]["status"] == "missing_basis"
    assert result["flow_context"]["direction"] == "WAIT"
    assert result["flow_context"]["confidence"] == "Low"
    assert any("Basis missing" in note for note in result["notes"])


def test_score_oi_expected_range_can_derive_expected_move_from_iv_pct():
    result = score_oi_expected_range(
        symbol="XAUUSD",
        current_price=4100,
        anchor_price=4100,
        expected_move=None,
        iv_daily_pct=0.8,
        oi_magnet_zone=4100,
    )

    assert result["expected_move"]["points"] == 32.8
    assert result["range_levels"]["sd1_low"] == 4067.2
    assert result["range_levels"]["sd1_high"] == 4132.8
