"""OI expected-range / magnet scoring for intraday proxy flow.

The service is pure and data-source agnostic: callers provide already-known
anchor price, expected move or IV proxy, basis, and OI magnet zone. The result
can be fed into ``strategy_regime_score`` as ``flow_context``.
"""
from __future__ import annotations

from typing import Any, Optional


def _round(value: Optional[float], decimals: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), decimals)


def _num(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _state(value: Any) -> str:
    return str(value or "").strip().lower()


def _confidence(high: bool = False, low: bool = False) -> str:
    if high:
        return "High"
    if low:
        return "Low"
    return "Medium"


def _range_state(current: float, low1: float, high1: float, low2: float, high2: float,
                 magnet: Optional[float], expected_move: float) -> str:
    near = max(expected_move * 0.20, 1e-9)
    if current < low2:
        return "outside_lower_sd2"
    if current > high2:
        return "outside_upper_sd2"
    if current < low1:
        return "outside_lower_sd1"
    if current > high1:
        return "outside_upper_sd1"
    if abs(current - low1) <= near:
        return "near_lower_sd1"
    if abs(current - high1) <= near:
        return "near_upper_sd1"
    if magnet is not None and abs(current - magnet) <= near:
        return "inside_sd1_near_magnet"
    return "inside_sd1"


def score_oi_expected_range(
    symbol: str,
    current_price: float,
    anchor_price: float,
    expected_move: Optional[float] = None,
    iv_daily_pct: Optional[float] = None,
    oi_magnet_zone: Optional[float] = None,
    basis: Optional[float] = None,
    proxy_underlying_price: Optional[float] = None,
    price_action_state: str = "",
    volatility_state: str = "",
    volume_state: str = "",
    expiry_context: bool = False,
) -> dict[str, Any]:
    """Score intraday OI/option expected-range proxy context.

    Args use point values for gold/XAUUSD-style instruments. ``iv_daily_pct`` is
    interpreted as percent of ``anchor_price`` (0.8 means 0.8%).
    """
    current = float(current_price)
    anchor = float(anchor_price)
    magnet = _num(oi_magnet_zone)
    basis_value = _num(basis)
    proxy_value = _num(proxy_underlying_price)
    iv_pct = _num(iv_daily_pct)
    move = _num(expected_move)

    notes: list[str] = []

    if move is None:
        if iv_pct is None:
            return {
                "error": "expected_move or iv_daily_pct is required",
                "symbol": symbol,
            }
        move = anchor * (iv_pct / 100.0)
        move_source = "iv_daily_pct"
    else:
        move_source = "expected_move"

    if move <= 0:
        return {"error": "expected_move must be positive", "symbol": symbol}

    basis_status = "not_applicable"
    adjusted_proxy = None
    basis_diff = None
    stale_basis = False
    if proxy_value is not None:
        if basis_value is None:
            basis_status = "missing_basis"
            notes.append("Basis missing for proxy-underlying input; OI proxy direction is neutral.")
        else:
            adjusted_proxy = proxy_value + basis_value
            basis_diff = current - adjusted_proxy
            basis_status = "ok"
            if abs(basis_diff) > max(move * 0.25, 3.0):
                stale_basis = True
                basis_status = "stale_or_misaligned"
                notes.append("Basis-adjusted proxy is far from current price; reduce proxy confidence.")

    sd1_low = anchor - move
    sd1_high = anchor + move
    sd2_low = anchor - (2 * move)
    sd2_high = anchor + (2 * move)
    range_state = _range_state(current, sd1_low, sd1_high, sd2_low, sd2_high, magnet, move)

    pa = _state(price_action_state)
    vol = _state(volatility_state)
    volu = _state(volume_state)
    expanding = vol in {"expanding", "high", "very high"} or volu in {"high", "very high", "above average"}
    low_vol = vol in {"low", "compressed", "squeeze"}

    direction = "WAIT"
    confidence = "Medium"
    regime_hint = "range_magnet" if range_state == "inside_sd1_near_magnet" else "neutral_expected_range"

    if basis_status == "missing_basis" or stale_basis:
        confidence = "Low"
        regime_hint = "neutral_expected_range"
    elif pa in {"rejected_lower_sd1", "sweep_lower_reject", "back_inside_from_lower"}:
        direction = "BUY"
        confidence = _confidence(high=True)
        regime_hint = "range_mean_reversion"
        notes.append("Lower SD1 sweep/rejection favors BUY mean reversion back toward range/magnet.")
    elif pa in {"rejected_upper_sd1", "sweep_upper_reject", "back_inside_from_upper"}:
        direction = "SELL"
        confidence = _confidence(high=True)
        regime_hint = "range_mean_reversion"
        notes.append("Upper SD1 sweep/rejection favors SELL mean reversion back toward range/magnet.")
    elif pa in {"breakout_up", "outside_upper_sd1_breakout"} or range_state == "outside_upper_sd1":
        if expanding:
            direction = "BUY"
            confidence = "High"
            regime_hint = "trend_momentum"
            notes.append("Upper SD1 breakout with volatility/volume expansion favors BUY breakout continuation.")
        else:
            confidence = "Low"
            notes.append("Upper SD1 break lacks expansion; wait for confirmation or rejection.")
    elif pa in {"breakout_down", "outside_lower_sd1_breakout"} or range_state == "outside_lower_sd1":
        if expanding:
            direction = "SELL"
            confidence = "High"
            regime_hint = "trend_momentum"
            notes.append("Lower SD1 breakout with volatility/volume expansion favors SELL breakout continuation.")
        else:
            confidence = "Low"
            notes.append("Lower SD1 break lacks expansion; wait for confirmation or rejection.")
    elif range_state == "inside_sd1_near_magnet" and low_vol:
        direction = "WAIT"
        confidence = "Medium"
        regime_hint = "range_magnet"
        notes.append("Price is inside SD1 near OI magnet with low volatility; expect range/magnet behavior.")
    elif range_state in {"outside_upper_sd2", "outside_lower_sd2"}:
        direction = "WAIT"
        confidence = "Low"
        regime_hint = "extreme_avoid_chasing"
        notes.append("Price is outside SD2; avoid chasing without strong confirmation.")

    if expiry_context:
        notes.append("Expiry/settlement context present; OI magnet receives higher attention but remains a proxy.")

    source = "OI expected range / magnet proxy"
    return {
        "symbol": symbol,
        "current_price": _round(current),
        "anchor_price": _round(anchor),
        "expected_move": {
            "points": _round(move),
            "source": move_source,
            "iv_daily_pct": _round(iv_pct) if iv_pct is not None else None,
        },
        "basis_adjustment": {
            "status": basis_status,
            "proxy_underlying_price": _round(proxy_value),
            "basis": _round(basis_value),
            "basis_adjusted_proxy": _round(adjusted_proxy),
            "current_minus_adjusted_proxy": _round(basis_diff),
        },
        "range_levels": {
            "sd1_low": _round(sd1_low),
            "sd1_high": _round(sd1_high),
            "sd2_low": _round(sd2_low),
            "sd2_high": _round(sd2_high),
        },
        "oi_magnet_zone": _round(magnet),
        "range_state": range_state,
        "regime_hint": regime_hint,
        "flow_context": {
            "direction": direction,
            "confidence": confidence,
            "source": source,
        },
        "notes": notes,
    }
