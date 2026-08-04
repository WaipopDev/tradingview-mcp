"""Automation connector: analyze market data, score it, and store dashboard signal."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from tradingview_mcp.core.errors import ErrorCode, make_error
from tradingview_mcp.core.jobs.score_latest_signal import store_compact_trade_signal
from tradingview_mcp.core.services.screener_service import analyze_coin, run_multi_timeframe_analysis
from tradingview_mcp.core.services.sd_oi_proxy_service import build_sd_oi_proxy
from tradingview_mcp.core.services.strategy_regime_service import score_strategy_regime
from tradingview_mcp.core.storage.database import PathLike
from tradingview_mcp.core.storage.repositories import SignalAiResponseRepository

AnalyzeCoinFn = Callable[[str, str, str], dict[str, Any]]
MultiTimeframeFn = Callable[[str, str], dict[str, Any]]

XAUUSD_SYMBOLS = {"XAUUSD", "GOLD", "XAU"}
REQUIRED_MTF_TIMEFRAMES = ("15m", "1h", "4h", "1D")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _retryable_legacy_error(error: Any) -> bool:
    text = str(error).lower()
    retryable_markers = (
        "analysis failed",
        "upstream",
        "timeout",
        "timed out",
        "rate limit",
        "temporarily",
        "connection",
        "remote end closed",
        "empty-body",
        "empty response",
    )
    return any(marker in text for marker in retryable_markers)


def _error_result(
    raw_error: Any,
    *,
    fallback_message: str,
    symbol: str,
    exchange: str,
    timeframe: str,
    instrument: str | None = None,
) -> dict[str, Any]:
    if isinstance(raw_error, dict):
        error = dict(raw_error)
        error.setdefault("retryable", False)
    else:
        retryable = _retryable_legacy_error(raw_error)
        code = ErrorCode.UPSTREAM_ERROR if retryable else ErrorCode.INTERNAL_ERROR
        error = make_error(code, str(raw_error or fallback_message), retryable=retryable)["error"]
    result: dict[str, Any] = {
        "stored": False,
        "error": error,
        "symbol": symbol,
        "exchange": exchange,
        "timeframe": timeframe,
    }
    if instrument:
        result["instrument"] = instrument
    return result


def _price(technical: dict[str, Any]) -> float | None:
    price_data = technical.get("price_data") or {}
    for key in ("current_price", "price", "close"):
        if price_data.get(key) is not None:
            return _num(price_data.get(key))
    return None


def _atr_points(technical: dict[str, Any], price: float) -> float:
    atr = technical.get("atr") or {}
    value = _num(atr.get("value"), 0)
    if value > 0:
        return value
    pct = _num(atr.get("percent_of_price"), 0)
    if pct > 0:
        return max(price * pct / 100, price * 0.001)
    return max(price * 0.0015, 1.0)


def _levels(technical: dict[str, Any]) -> dict[str, list[float]]:
    sr = technical.get("support_resistance") or technical.get("levels") or {}
    support = sr.get("support_levels") or sr.get("support") or []
    resistance = sr.get("resistance_levels") or sr.get("resistance") or []
    return {
        "support": [_num(item) for item in support if _num(item) > 0][:5],
        "resistance": [_num(item) for item in resistance if _num(item) > 0][:5],
    }


def _volume_summary(technical: dict[str, Any]) -> dict[str, Any]:
    vol = technical.get("volume_analysis") or {}
    atr = technical.get("atr") or {}
    return {
        "state": vol.get("signal") or "unknown",
        "ratio": vol.get("ratio"),
        "atr_volatility": atr.get("volatility"),
    }


def _mtf_missing_timeframes(mtf: dict[str, Any]) -> list[str]:
    timeframes = mtf.get("timeframes") or {}
    if not isinstance(timeframes, dict):
        return list(REQUIRED_MTF_TIMEFRAMES)
    return [tf for tf in REQUIRED_MTF_TIMEFRAMES if tf not in timeframes]


def _technical_payload(full_symbol: str, technical: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, compact subset of technical analysis for AI prompts."""
    return {
        "source_symbol": full_symbol,
        "reported_symbol": technical.get("symbol"),
        "price_data": technical.get("price_data") or {},
        "timeframe_context": technical.get("timeframe_context") or {},
        "market_structure": technical.get("market_structure") or {},
        "market_sentiment": technical.get("market_sentiment") or {},
        "rsi": technical.get("rsi") or {},
        "macd": technical.get("macd") or {},
        "atr": technical.get("atr") or {},
        "support_resistance": technical.get("support_resistance") or technical.get("levels") or {},
    }


def _entry_zone(low: float, high: float) -> str:
    return f"{low:g}-{high:g}" if low != high else f"{low:g}"


def _derive_plan(price: float | None, bias: str, technical: dict[str, Any]) -> dict[str, Any]:
    if price is None or bias not in {"BUY", "SELL"}:
        return {"entry_zone": None, "sl": None, "tp": []}

    atr = _atr_points(technical, price)
    levels = _levels(technical)
    supports = sorted([level for level in levels["support"] if level < price], reverse=True)
    resistances = sorted([level for level in levels["resistance"] if level > price])

    if bias == "SELL":
        entry_low = resistances[0] if resistances else price + atr * 0.5
        entry_high = resistances[1] if len(resistances) > 1 else entry_low + atr * 0.5
        sl = entry_high + atr * 0.25
        tps = supports[:3] or [price - atr, price - atr * 2, price - atr * 3]
        return {
            "entry_zone": _entry_zone(round(entry_low, 4), round(entry_high, 4)),
            "sl": round(sl, 4),
            "tp": [round(tp, 4) for tp in tps],
        }

    entry_high = supports[0] if supports else price - atr * 0.5
    entry_low = supports[1] if len(supports) > 1 else entry_high - atr * 0.5
    sl = entry_low - atr * 0.25
    tps = resistances[:3] or [price + atr, price + atr * 2, price + atr * 3]
    return {
        "entry_zone": _entry_zone(round(entry_low, 4), round(entry_high, 4)),
        "sl": round(sl, 4),
        "tp": [round(tp, 4) for tp in tps],
    }


def _compact_summary(
    symbol: str,
    exchange: str,
    timeframe: str,
    full_symbol: str,
    technical: dict[str, Any],
    score: dict[str, Any],
    sd_oi_proxy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    current_price = _price(technical)
    bias = str(score.get("bias") or "WAIT").upper()
    reason_codes = [
        "STORED_FROM_AUTOMATION_CONNECTOR",
        f"DECISION_{score.get('decision', 'UNKNOWN')}",
        f"REGIME_{(score.get('regime') or {}).get('primary', 'unknown')}",
    ]
    if sd_oi_proxy:
        reason_codes.append("SD_OI_PROXY_ATTACHED")
    return {
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "instrument": full_symbol,
        "timeframe": timeframe,
        "price": current_price,
        "bias": bias,
        "decision": score.get("decision") or "WAIT_CONFIRMATION",
        "score": score.get("total_score"),
        "confidence": (score.get("regime") or {}).get("description"),
        "regime": (score.get("regime") or {}).get("primary"),
        "sd_range": (sd_oi_proxy or {}).get("sd_range") or {},
        "oi_proxy": (sd_oi_proxy or {}).get("oi_proxy") or {},
        "volume": _volume_summary(technical),
        "technical": _technical_payload(full_symbol, technical),
        "levels": _levels(technical),
        "plan": _derive_plan(current_price, bias, technical),
        "reason_codes": reason_codes,
        "score_breakdown": score.get("score_breakdown") or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def analyze_and_store_signal(
    symbol: str = "XAUUSD",
    exchange: str = "OANDA",
    timeframe: str = "15m",
    db_path: PathLike | None = None,
    analyze_coin_fn: AnalyzeCoinFn = analyze_coin,
    multi_timeframe_fn: MultiTimeframeFn = run_multi_timeframe_analysis,
) -> dict[str, Any]:
    """Fetch analysis, score it deterministically, store compact signal, and return it.

    This is the production connector used by Telegram/Hermes prompts: one call
    performs data collection + regime scoring + SQLite persistence so the
    dashboard updates immediately and the LLM receives only compact JSON.
    """
    symbol_clean = symbol.strip().upper() or "XAUUSD"
    exchange_clean = exchange.strip().upper() or "OANDA"
    timeframe_clean = timeframe.strip() or "15m"
    if symbol_clean in XAUUSD_SYMBOLS:
        symbol_clean = "XAUUSD"
        exchange_clean = "OANDA"
    full_symbol = f"{exchange_clean}:{symbol_clean}"

    # Pass the bare symbol into analyze_coin so provider aliases/fallbacks remain
    # available (some TradingView libraries resolve XAUUSD via TVC:GOLD even when
    # the requested instrument is OANDA:XAUUSD). The compact contract still
    # preserves the requested instrument and reported source separately.
    technical = analyze_coin_fn(symbol_clean, exchange_clean, timeframe_clean)
    if not isinstance(technical, dict) or "error" in technical:
        return _error_result(
            technical.get("error") if isinstance(technical, dict) else None,
            fallback_message="technical analysis failed",
            symbol=symbol_clean,
            exchange=exchange_clean,
            timeframe=timeframe_clean,
            instrument=full_symbol,
        )

    mtf = multi_timeframe_fn(full_symbol, exchange_clean)
    if not isinstance(mtf, dict) or "error" in mtf:
        return _error_result(
            mtf.get("error") if isinstance(mtf, dict) else None,
            fallback_message="multi-timeframe analysis failed",
            symbol=symbol_clean,
            exchange=exchange_clean,
            timeframe=timeframe_clean,
            instrument=full_symbol,
        )
    missing_mtf = _mtf_missing_timeframes(mtf)
    if missing_mtf:
        return {
            "stored": False,
            "error": {
                "code": "INCOMPLETE_MTF_PAYLOAD",
                "message": "Multi-timeframe analysis is missing required execution/context timeframes.",
                "missing_timeframes": missing_mtf,
                "required_timeframes": list(REQUIRED_MTF_TIMEFRAMES),
                "retryable": True,
            },
            "symbol": symbol_clean,
            "exchange": exchange_clean,
            "instrument": full_symbol,
            "timeframe": timeframe_clean,
        }

    sd_oi_proxy = build_sd_oi_proxy(symbol_clean, technical, timeframe_clean)
    score = score_strategy_regime(full_symbol, exchange_clean, technical, mtf, flow_context=sd_oi_proxy.get("flow_context"))
    if "error" in score:
        return {"stored": False, **score}

    summary = _compact_summary(symbol_clean, exchange_clean, timeframe_clean, full_symbol, technical, score, sd_oi_proxy=sd_oi_proxy)
    summary["ai_gate"] = SignalAiResponseRepository(db_path).build_ai_gate(summary)
    stored = store_compact_trade_signal(summary, db_path=db_path)
    latest = stored["latest"] or summary
    latest["stored"] = True
    latest["source"] = "analyze_and_store_signal"
    latest["instrument"] = summary["instrument"]
    latest["technical"] = summary["technical"]
    latest["score_breakdown"] = score.get("score_breakdown") or {}
    latest["ai_gate"] = summary["ai_gate"]
    return latest
