"""Strategy-regime scoring inspired by the local 151 Trading Strategies playbook.

This module is deliberately pure: it consumes already-fetched technical,
multi-timeframe, and optional flow/proxy dictionaries and returns a deterministic
BUY/SELL/WAIT score. Network calls live in the MCP server wrapper.
"""
from __future__ import annotations

from typing import Any, Optional


_BULLISH = {"bullish", "buy", "strong buy", "mostly bullish", "fully aligned bullish"}
_BEARISH = {"bearish", "sell", "strong sell", "mostly bearish", "fully aligned bearish"}


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _direction_from_mtf(mtf_analysis: dict[str, Any]) -> str:
    alignment = mtf_analysis.get("alignment", {}) if isinstance(mtf_analysis, dict) else {}
    score = _num(alignment.get("net_score"), 0)
    status = _lower(alignment.get("status"))
    if score > 0 or "bullish" in status:
        return "BUY"
    if score < 0 or "bearish" in status:
        return "SELL"
    return "WAIT"


def _opposite(direction: str) -> str:
    return "SELL" if direction == "BUY" else "BUY" if direction == "SELL" else "WAIT"


def _classify_regime(technical: dict[str, Any], mtf: dict[str, Any]) -> dict[str, Any]:
    bb = technical.get("bollinger_bands", {}) or {}
    ms = technical.get("market_structure", {}) or {}
    rsi = technical.get("rsi", {}) or {}
    sentiment = technical.get("market_sentiment", {}) or {}
    alignment = (mtf or {}).get("alignment", {}) or {}

    trend = _lower(ms.get("trend"))
    trend_strength = _lower(ms.get("trend_strength"))
    volatility = _lower(sentiment.get("volatility"))
    rsi_signal = _lower(rsi.get("signal"))
    status = _lower(alignment.get("status"))
    squeeze = bool(bb.get("squeeze")) or (_num(bb.get("width"), 9) < 0.02)

    reasons: list[str] = []

    if squeeze or volatility == "low":
        # A squeeze can coexist with range. Prefer range when an extreme exists;
        # otherwise call it a squeeze and wait for breakout direction.
        if rsi_signal in {"oversold", "overbought"} or "lower" in _lower(bb.get("position")) or "upper" in _lower(bb.get("position")):
            reasons.append("Low volatility with oscillator/band extreme suggests range mean-reversion, not blind breakout.")
            return {
                "primary": "range_mean_reversion",
                "description": "Range / mean reversion",
                "reasons": reasons,
            }
        reasons.append("Low Bollinger width / low volatility suggests squeeze conditions.")
        return {"primary": "low_vol_squeeze", "description": "Low-volatility squeeze", "reasons": reasons}

    if "bullish" in trend or "bearish" in trend or "strong" in trend_strength or "bullish" in status or "bearish" in status:
        reasons.append("Trend structure or multi-timeframe alignment favors momentum/trend-following strategies.")
        return {"primary": "trend_momentum", "description": "Trend / momentum", "reasons": reasons}

    if "ranging" in trend or rsi_signal in {"oversold", "overbought"}:
        reasons.append("Neutral/ranging structure or RSI extreme favors contrarian mean-reversion setups.")
        return {"primary": "range_mean_reversion", "description": "Range / mean reversion", "reasons": reasons}

    reasons.append("No clean regime; use event/high-volatility guard and wait for confirmation.")
    return {"primary": "event_guard", "description": "High-vol/event or mixed regime", "reasons": reasons}


def _strategy_family(regime: str) -> dict[str, Any]:
    mapping = {
        "trend_momentum": {
            "primary": ["trend_following", "price_momentum", "moving_average_alignment", "channel_breakout"],
            "source_concepts": ["Price-momentum", "Trend following (momentum)", "Single/Two/Three moving averages", "Channel"],
        },
        "range_mean_reversion": {
            "primary": ["mean_reversion", "bollinger_reversion", "support_resistance", "contrarian"],
            "source_concepts": ["Mean-reversion", "Contrarian trading", "Support and resistance"],
        },
        "low_vol_squeeze": {
            "primary": ["bollinger_squeeze", "volume_breakout", "keltner_or_donchian_breakout"],
            "source_concepts": ["Channel", "Trend following (momentum)", "Volatility carry/context"],
        },
        "event_guard": {
            "primary": ["event_filter", "sentiment_filter", "reduced_size_confirmation"],
            "source_concepts": ["Trading on economic announcements", "Sentiment analysis", "Global macro"],
        },
    }
    return mapping.get(regime, mapping["event_guard"])


def _score_mtf(mtf: dict[str, Any], direction: str) -> tuple[int, list[str]]:
    alignment = (mtf or {}).get("alignment", {}) or {}
    net = _num(alignment.get("net_score"), 0)
    status = _lower(alignment.get("status"))
    abs_net = abs(net)
    notes = [f"MTF status={alignment.get('status', 'unknown')} net_score={net:g}"]
    if direction == "WAIT":
        return (8 if abs_net == 0 else 12), notes
    if (direction == "BUY" and (net >= 3 or "fully aligned bullish" in status)) or (direction == "SELL" and (net <= -3 or "fully aligned bearish" in status)):
        return 25, notes
    if (direction == "BUY" and net > 0) or (direction == "SELL" and net < 0):
        return 18, notes
    return 5, notes + ["MTF conflicts with selected bias."]


def _score_structure(technical: dict[str, Any], direction: str) -> tuple[int, list[str]]:
    ms = technical.get("market_structure", {}) or {}
    trend = _lower(ms.get("trend"))
    strength = _lower(ms.get("trend_strength"))
    aligned = bool(ms.get("momentum_aligned"))
    notes = [f"Structure trend={ms.get('trend', 'unknown')} strength={ms.get('trend_strength', 'unknown')}"]
    if direction == "WAIT":
        return 10, notes
    wanted = "bullish" if direction == "BUY" else "bearish"
    if wanted in trend and aligned:
        return 25 if "strong" in strength else 22, notes
    if wanted in trend:
        return 18, notes + ["Trend matches but momentum alignment is incomplete."]
    if "neutral" in trend or "ranging" in trend:
        return 12, notes + ["Ranging structure weakens directional trade confidence."]
    return 4, notes + ["Market structure conflicts with selected bias."]


def _score_strategy_fit(regime: str, technical: dict[str, Any], direction: str) -> tuple[int, list[str]]:
    rsi_signal = _lower((technical.get("rsi") or {}).get("signal"))
    bb_position = _lower((technical.get("bollinger_bands") or {}).get("position"))
    macd = _lower((technical.get("macd") or {}).get("crossover"))
    notes = [f"Regime={regime}"]
    if regime == "trend_momentum":
        if direction == "BUY" and macd == "bullish":
            return 20, notes + ["Momentum strategy fits bullish MACD/trend context."]
        if direction == "SELL" and macd == "bearish":
            return 20, notes + ["Momentum strategy fits bearish MACD/trend context."]
        return 14, notes + ["Trend regime present but trigger confirmation is partial."]
    if regime == "range_mean_reversion":
        if rsi_signal == "oversold" or "below lower" in bb_position:
            return (16 if direction in {"BUY", "WAIT"} else 8), notes + ["Oversold/lower-band condition favors BUY mean reversion only after confirmation."]
        if rsi_signal == "overbought" or "above upper" in bb_position:
            return (16 if direction in {"SELL", "WAIT"} else 8), notes + ["Overbought/upper-band condition favors SELL mean reversion only after confirmation."]
        return 12, notes
    if regime == "low_vol_squeeze":
        return 12, notes + ["Squeeze needs directional breakout and volume confirmation first."]
    return 8, notes + ["Event/mixed regime reduces strategy fit score."]


def _score_volume_atr(technical: dict[str, Any], direction: str) -> tuple[int, list[str]]:
    vol = technical.get("volume_analysis", {}) or {}
    atr = technical.get("atr", {}) or {}
    vol_signal = _lower(vol.get("signal"))
    atr_vol = _lower(atr.get("volatility"))
    notes = [f"Volume={vol.get('signal', 'unknown')} ATR_volatility={atr.get('volatility', 'unknown')}"]
    score = 6
    if vol_signal in {"very high", "high"}:
        score += 6
    elif vol_signal == "above average":
        score += 4
    elif vol_signal in {"very low", "below average"}:
        score -= 2
    if atr_vol == "medium":
        score += 3
    elif atr_vol == "high":
        score += 1
        notes.append("High ATR: trade smaller / require wider stop.")
    elif atr_vol == "low":
        score += 1
    return max(0, min(15, score)), notes


def _score_flow(flow_context: Optional[dict[str, Any]], direction: str) -> tuple[int, list[str]]:
    if not flow_context:
        return 8, ["No options/futures/sentiment proxy provided; neutral proxy score."]
    flow_dir = str(flow_context.get("direction", "WAIT")).upper()
    conf = _lower(flow_context.get("confidence"))
    source = flow_context.get("source", "flow proxy")
    if direction == "WAIT" or flow_dir == "WAIT":
        return 7, [f"{source}: neutral/wait flow proxy."]
    if flow_dir == direction:
        return (15 if conf == "high" else 12), [f"{source}: proxy confirms {direction}."]
    return (2 if conf == "high" else 4), [f"{source}: proxy conflicts with {direction} bias."]


def score_strategy_regime(
    symbol: str,
    exchange: str,
    technical_analysis: dict[str, Any],
    multi_timeframe_analysis: dict[str, Any],
    flow_context: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Return strategy-family fit and BUY/SELL/WAIT confidence score.

    Scores mirror docs/151-trading-strategies-adaptation-th.md:
    MTF 25, structure 25, strategy fit 20, volume/ATR 15, proxy flow 15.
    """
    if not isinstance(technical_analysis, dict) or "error" in technical_analysis:
        return {"error": "technical_analysis is missing or contains an error", "symbol": symbol, "exchange": exchange}
    if not isinstance(multi_timeframe_analysis, dict) or "error" in multi_timeframe_analysis:
        return {"error": "multi_timeframe_analysis is missing or contains an error", "symbol": symbol, "exchange": exchange}

    raw_direction = _direction_from_mtf(multi_timeframe_analysis)
    regime = _classify_regime(technical_analysis, multi_timeframe_analysis)
    # Range/squeeze setups should not be converted into an immediate trade from MTF alone.
    bias = raw_direction
    if regime["primary"] in {"range_mean_reversion", "low_vol_squeeze", "event_guard"}:
        if abs(_num((multi_timeframe_analysis.get("alignment") or {}).get("net_score"), 0)) < 3:
            bias = "WAIT"

    mtf_score, mtf_notes = _score_mtf(multi_timeframe_analysis, bias)
    structure_score, structure_notes = _score_structure(technical_analysis, bias)
    strategy_score, strategy_notes = _score_strategy_fit(regime["primary"], technical_analysis, bias)
    volume_score, volume_notes = _score_volume_atr(technical_analysis, bias)
    flow_score, flow_notes = _score_flow(flow_context, bias)

    total = mtf_score + structure_score + strategy_score + volume_score + flow_score

    decision = "NO_TRADE"
    if total >= 70 and bias in {"BUY", "SELL"}:
        decision = "TRADE"
    elif total >= 55 or bias == "WAIT":
        decision = "WAIT_CONFIRMATION"

    notes = regime["reasons"] + mtf_notes + structure_notes + strategy_notes + volume_notes + flow_notes
    if flow_context and flow_score <= 4:
        decision = "WAIT_CONFIRMATION"
        notes.append("Flow/proxy context conflicts with directional technical setup; wait for confirmation.")

    return {
        "symbol": symbol,
        "exchange": exchange,
        "bias": bias,
        "decision": decision,
        "total_score": int(round(total)),
        "score_breakdown": {
            "mtf_alignment": mtf_score,
            "structure_smc_liquidity": structure_score,
            "strategy_fit": strategy_score,
            "volume_atr_volatility": volume_score,
            "options_futures_sentiment_proxy": flow_score,
        },
        "regime": regime,
        "strategy_family": _strategy_family(regime["primary"]),
        "thresholds": {
            "trade": ">=70 and directional bias",
            "wait_confirmation": "55-69 or WAIT bias",
            "no_trade": "<55",
        },
        "notes": notes,
    }
