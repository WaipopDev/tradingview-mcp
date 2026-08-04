"""Deterministic SD range + intraday OI proxy builder for XAUUSD.

OANDA:XAUUSD is spot/CFD and does not expose centralised exchange open
interest. This module therefore derives an intraday *proxy* context from
already-fetched technical data: current price, ATR, volume state, and nearest
support/resistance levels. The output is compact and safe for dashboard/LLM use.
"""
from __future__ import annotations

from typing import Any

from tradingview_mcp.core.services.oi_expected_range_service import score_oi_expected_range

OANDA_XAUUSD_OI_LIMITATION = (
    "OANDA:XAUUSD spot/CFD has no centralised open interest; this is an "
    "intraday ATR + support/resistance proxy, not real exchange OI."
)
OANDA_XAUUSD_PROXY_SOURCE = "OANDA:XAUUSD intraday ATR + support/resistance OI proxy"


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value: float | None, decimals: int = 4) -> float | None:
    return None if value is None else round(float(value), decimals)


def _price(technical: dict[str, Any]) -> float | None:
    price_data = technical.get("price_data") or {}
    for key in ("current_price", "price", "close"):
        value = _num(price_data.get(key))
        if value is not None and value > 0:
            return value
    return None


def _atr_expected_move(technical: dict[str, Any], price: float) -> tuple[float, str]:
    atr = technical.get("atr") or {}
    value = _num(atr.get("value"))
    if value is not None and value > 0:
        return value, "atr_value"
    pct = _num(atr.get("percent_of_price"))
    if pct is not None and pct > 0:
        return max(price * pct / 100.0, price * 0.001), "atr_percent_of_price"
    return max(price * 0.0015, 1.0), "fallback_price_pct"


def _levels(technical: dict[str, Any]) -> dict[str, list[float]]:
    sr = technical.get("support_resistance") or technical.get("levels") or {}
    support = sr.get("support_levels") or sr.get("support") or []
    resistance = sr.get("resistance_levels") or sr.get("resistance") or []
    return {
        "support": [float(x) for x in (_num(item) for item in support) if x is not None and x > 0][:5],
        "resistance": [float(x) for x in (_num(item) for item in resistance) if x is not None and x > 0][:5],
    }


def _nearest_magnet(price: float, levels: dict[str, list[float]]) -> float | None:
    candidates = levels.get("support", []) + levels.get("resistance", [])
    if not candidates:
        return None
    return min(candidates, key=lambda level: abs(level - price))


def _price_action_state(price: float, anchor: float, expected_move: float) -> str:
    sd1_low = anchor - expected_move
    sd1_high = anchor + expected_move
    if price > sd1_high:
        return "outside_upper_sd1_breakout"
    if price < sd1_low:
        return "outside_lower_sd1_breakout"
    return "inside_sd1"


def _safe_proxy_flow(flow: dict[str, Any] | None) -> dict[str, Any]:
    """Return flow_context safe to feed into Strategy Regime Scoring.

    Strategy scoring only consumes direction/confidence/source today, but the
    explicit false OI flag and limitation travel with the proxy context so logs
    and score notes cannot imply OANDA:XAUUSD has real centralised OI.
    """
    flow = flow or {}
    direction = str(flow.get("direction") or "WAIT").upper()
    if direction not in {"BUY", "SELL", "WAIT"}:
        direction = "WAIT"
    return {
        "direction": direction,
        "confidence": flow.get("confidence") or "Medium",
        "source": OANDA_XAUUSD_PROXY_SOURCE,
        "real_open_interest_available": False,
        "limitation": OANDA_XAUUSD_OI_LIMITATION,
    }


def build_sd_oi_proxy(symbol: str, technical: dict[str, Any], timeframe: str = "15m") -> dict[str, Any]:
    """Build compact SD range and OI/intraday proxy payload from technical data."""
    price = _price(technical)
    if price is None:
        return {
            "sd_range": {},
            "oi_proxy": {
                "real_open_interest_available": False,
                "source": OANDA_XAUUSD_PROXY_SOURCE,
                "limitation": OANDA_XAUUSD_OI_LIMITATION + " Proxy unavailable without price.",
            },
            "flow_context": _safe_proxy_flow({"direction": "WAIT", "confidence": "Low"}),
        }

    expected_move, move_source = _atr_expected_move(technical, price)
    anchor = price
    levels = _levels(technical)
    magnet = _nearest_magnet(price, levels)
    volume = technical.get("volume_analysis") or {}
    atr = technical.get("atr") or {}

    scored = score_oi_expected_range(
        symbol=symbol.upper(),
        current_price=price,
        anchor_price=anchor,
        expected_move=expected_move,
        oi_magnet_zone=magnet,
        price_action_state=_price_action_state(price, anchor, expected_move),
        volatility_state=str(atr.get("volatility") or ""),
        volume_state=str(volume.get("signal") or ""),
    )
    range_levels = scored.get("range_levels") or {}
    flow = _safe_proxy_flow(scored.get("flow_context"))

    return {
        "sd_range": {
            "anchor_price": _round(anchor),
            "expected_move_points": _round(expected_move),
            "expected_move_source": move_source,
            "timeframe": timeframe,
            "sd1_low": range_levels.get("sd1_low"),
            "sd1_high": range_levels.get("sd1_high"),
            "sd2_low": range_levels.get("sd2_low"),
            "sd2_high": range_levels.get("sd2_high"),
            "range_state": scored.get("range_state"),
        },
        "oi_proxy": {
            "real_open_interest_available": False,
            "source": OANDA_XAUUSD_PROXY_SOURCE,
            "limitation": OANDA_XAUUSD_OI_LIMITATION,
            "magnet_zone": _round(magnet),
            "support_levels": [_round(x) for x in levels.get("support", [])],
            "resistance_levels": [_round(x) for x in levels.get("resistance", [])],
            "flow_direction": flow.get("direction"),
            "flow_confidence": flow.get("confidence"),
            "regime_hint": scored.get("regime_hint"),
            "notes": scored.get("notes") or [],
        },
        "flow_context": flow,
    }
