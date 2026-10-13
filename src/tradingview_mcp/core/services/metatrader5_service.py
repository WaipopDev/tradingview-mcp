"""MetaTrader 5 local-market-data provider.

The provider reads bars from the MetaTrader 5 terminal installed on the same
Windows machine. It does not place orders and never calls trading functions.
"""
from __future__ import annotations

import os
from typing import Any

from tradingview_mcp.core.services.indicators_calc import (
    calc_atr,
    calc_bollinger,
    calc_ema,
    calc_macd,
    calc_rsi,
    calc_sma,
)

try:  # Optional dependency: the package is Windows/MT5-terminal specific.
    import MetaTrader5 as _mt5  # type: ignore
except ImportError:  # pragma: no cover - exercised on non-Windows CI
    _mt5 = None


class MetaTrader5DataError(RuntimeError):
    """Raised when MT5 cannot provide the requested market data."""


def _timeframe_value(timeframe: str) -> Any:
    if _mt5 is None:
        raise MetaTrader5DataError(
            "MetaTrader5 package is not installed; install the optional MT5 dependency"
        )
    values = {
        "5m": getattr(_mt5, "TIMEFRAME_M5", None),
        "15m": getattr(_mt5, "TIMEFRAME_M15", None),
        "1h": getattr(_mt5, "TIMEFRAME_H1", None),
        "4h": getattr(_mt5, "TIMEFRAME_H4", None),
        "1D": getattr(_mt5, "TIMEFRAME_D1", None),
        "1W": getattr(_mt5, "TIMEFRAME_W1", None),
        "1M": getattr(_mt5, "TIMEFRAME_MN1", None),
    }
    if timeframe not in values or values[timeframe] is None:
        raise ValueError(f"Unsupported MT5 timeframe: {timeframe}")
    return values[timeframe]


def _number(row: Any, key: str) -> float:
    value = row[key]
    return float(value)


def _initialize() -> None:
    if _mt5 is None:
        raise MetaTrader5DataError(
            "MetaTrader5 package is not installed; install the optional MT5 dependency"
        )
    path = os.getenv("MT5_TERMINAL_PATH")
    ok = _mt5.initialize(path=path) if path else _mt5.initialize()
    if not ok:
        raise MetaTrader5DataError(
            f"MetaTrader5 initialize failed: {_mt5.last_error()}"
        )


def _latest(values: list[float | None]) -> float | None:
    return values[-1] if values else None


def _select_symbol(symbol: str) -> str:
    """Select the broker's symbol, allowing common MT5 commodity aliases."""
    aliases = {"XAUUSD": "GOLD", "XAGUSD": "SILVER"}
    candidates = [symbol, aliases.get(symbol.upper(), "")]
    candidates.extend(
        item.strip() for item in os.getenv("MT5_SYMBOL_ALIASES", "").split(",") if item.strip()
    )
    for candidate in dict.fromkeys(c for c in candidates if c):
        if _mt5.symbol_select(candidate, True):
            return candidate
    raise MetaTrader5DataError(
        f"MetaTrader5 cannot select symbol {symbol!r}: {_mt5.last_error()}"
    )


def fetch_indicator_payload(symbol: str, timeframe: str, bars: int = 260) -> dict[str, Any]:
    """Fetch OHLCV bars and return a TradingView-compatible indicator mapping."""
    tf = _timeframe_value(timeframe)
    if bars < 30:
        raise ValueError("bars must be at least 30")

    _initialize()
    selected_symbol = _select_symbol(symbol)

    rates = _mt5.copy_rates_from_pos(selected_symbol, tf, 0, bars)
    if rates is None or len(rates) < 30:
        raise MetaTrader5DataError(
            f"MetaTrader5 returned insufficient bars for {symbol!r}/{timeframe}: "
            f"{_mt5.last_error()}"
        )

    opens = [_number(row, "open") for row in rates]
    highs = [_number(row, "high") for row in rates]
    lows = [_number(row, "low") for row in rates]
    closes = [_number(row, "close") for row in rates]
    volumes = [_number(row, "tick_volume") for row in rates]

    bb = calc_bollinger(closes, 20)
    macd = calc_macd(closes)
    payload: dict[str, Any] = {
        "symbol": selected_symbol,
        "source": "MetaTrader5",
        "timeframe": timeframe,
        "open": opens[-1],
        "high": highs[-1],
        "low": lows[-1],
        "close": closes[-1],
        "volume": volumes[-1],
        "volume.SMA20": _latest(calc_sma(volumes, 20)),
        "RSI": _latest(calc_rsi(closes, 14)),
        "BB.upper": _latest(bb["upper"]),
        "BB.lower": _latest(bb["lower"]),
        "SMA20": _latest(calc_sma(closes, 20)),
        "ATR": _latest(calc_atr(highs, lows, closes, 14)),
        "MACD.macd": _latest(macd["macd"]),
        "MACD.signal": _latest(macd["signal"]),
    }
    for period in (10, 20, 30, 50, 100, 200):
        payload[f"SMA{period}"] = _latest(calc_sma(closes, period))
        payload[f"EMA{period}"] = _latest(calc_ema(closes, period))
    return payload


def terminal_snapshot() -> dict[str, Any]:
    """Return non-secret MT5 terminal connectivity information."""
    _initialize()
    info = _mt5.terminal_info()
    if info is None:
        raise MetaTrader5DataError(f"MetaTrader5 terminal_info failed: {_mt5.last_error()}")
    return {
        "source": "MetaTrader5",
        "name": getattr(info, "name", None),
        "connected": bool(getattr(info, "connected", False)),
        "trade_allowed": bool(getattr(info, "trade_allowed", False)),
        "version": _mt5.version(),
    }


def analyze_symbol(symbol: str, exchange: str, timeframe: str) -> dict[str, Any]:
    """Return the public technical-analysis shape using MT5 bars."""
    from tradingview_mcp.core.services.indicators import (
        analyze_timeframe_context,
        compute_metrics,
        extract_extended_indicators,
    )

    indicators = fetch_indicator_payload(symbol, timeframe)
    metrics = compute_metrics(indicators)
    if not metrics:
        return {"error": f"Could not compute metrics for {symbol}", "symbol": symbol,
                "exchange": exchange, "timeframe": timeframe, "source": "MetaTrader5"}

    extended = extract_extended_indicators(indicators)
    return {
        "symbol": symbol, "exchange": exchange, "timeframe": timeframe,
        "timestamp": "real-time", "source": "MetaTrader5",
        "price_data": {
            "current_price": metrics["price"], "open": round(indicators["open"], 6),
            "high": round(indicators["high"], 6), "low": round(indicators["low"], 6),
            "close": round(indicators["close"], 6), "change_percent": metrics["change"],
            "volume": indicators["volume"],
        },
        "timeframe_context": analyze_timeframe_context(indicators, timeframe),
        "rsi": extended["rsi"], "macd": extended["macd"], "sma": extended["sma"],
        "ema": extended["ema"], "bollinger_bands": extended["bollinger_bands"],
        "atr": extended["atr"], "volume_analysis": extended["volume"],
        "obv": extended["obv"], "support_resistance": extended["support_resistance"],
        "stochastic": extended["stochastic"], "adx": extended["adx"],
        "market_structure": extended["market_structure"],
        **({"vwap": extended["vwap"]} if "vwap" in extended else {}),
        "market_sentiment": {
            "overall_rating": metrics["rating"], "buy_sell_signal": metrics["signal"],
            "volatility": (
                "High" if metrics["bbw"] and metrics["bbw"] > 0.05
                else "Medium" if metrics["bbw"] and metrics["bbw"] > 0.02 else "Low"
            ),
            "momentum": "Bullish" if metrics["change"] > 0 else "Bearish",
        },
    }
