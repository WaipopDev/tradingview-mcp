"""Read broker-native market data exported by the MT5MarketDataBridge EA.

The bridge is deliberately file based because the official MetaTrader5 Python
wheel is Windows-only and is not available to the macOS Python process that
runs Hermes.  All reads fail closed on malformed, incomplete, or stale data.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

REQUIRED_TIMEFRAMES = ("15m", "1h", "4h", "1D")
SYMBOL_ALIASES = {"XAUUSD", "GOLD", "XAU"}
DEFAULT_MAX_AGE_SECONDS = 5.0


class Mt5SnapshotError(RuntimeError):
    """The MT5 bridge snapshot cannot be trusted for trading decisions."""


def default_snapshot_path() -> Path:
    configured = os.getenv("TRAD_MT5_SNAPSHOT_PATH")
    if configured:
        return Path(configured).expanduser()
    return (
        Path.home()
        / "Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5"
        / "MQL5/Files/MT5MarketDataBridge/GOLD.json"
    )


def _number(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise Mt5SnapshotError(f"MT5 snapshot field {name} is not numeric") from exc
    if result != result or result in {float("inf"), float("-inf")}:
        raise Mt5SnapshotError(f"MT5 snapshot field {name} is not finite")
    return result


def load_mt5_snapshot(
    path: str | Path | None = None,
    *,
    symbol: str = "XAUUSD",
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    now_msc: int | None = None,
) -> dict[str, Any]:
    snapshot_path = Path(path).expanduser() if path else default_snapshot_path()
    try:
        payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Mt5SnapshotError(f"MT5 snapshot not found: {snapshot_path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise Mt5SnapshotError(f"MT5 snapshot is unreadable: {snapshot_path}: {exc}") from exc

    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise Mt5SnapshotError("MT5 snapshot schema_version must be 1")
    if str(payload.get("source", "")).upper() != "MT5":
        raise Mt5SnapshotError("MT5 snapshot source is invalid")

    requested = symbol.strip().upper()
    actual = str(payload.get("symbol", "")).strip().upper()
    canonical = str(payload.get("canonical_symbol", "")).strip().upper()
    if requested in SYMBOL_ALIASES:
        if actual not in SYMBOL_ALIASES or canonical != "XAUUSD":
            raise Mt5SnapshotError(f"MT5 snapshot symbol mismatch: requested={requested} actual={actual} canonical={canonical}")
    elif requested not in {actual, canonical}:
        raise Mt5SnapshotError(f"MT5 snapshot symbol mismatch: requested={requested} actual={actual}")

    tick = payload.get("tick")
    if not isinstance(tick, dict):
        raise Mt5SnapshotError("MT5 snapshot tick payload is missing")
    tick_msc = int(_number(tick.get("time_msc"), "tick.time_msc"))
    now = int(time.time() * 1000) if now_msc is None else int(now_msc)
    age_seconds = (now - tick_msc) / 1000
    if age_seconds < -5:
        raise Mt5SnapshotError(f"MT5 snapshot tick is from the future by {-age_seconds:.1f}s")
    if age_seconds > max_age_seconds:
        raise Mt5SnapshotError(f"MT5 snapshot is stale: age={age_seconds:.1f}s max={max_age_seconds:.1f}s")

    bid = _number(tick.get("bid"), "tick.bid")
    ask = _number(tick.get("ask"), "tick.ask")
    if bid <= 0 or ask <= 0 or ask < bid:
        raise Mt5SnapshotError(f"MT5 snapshot quote geometry is invalid: bid={bid} ask={ask}")

    frames = payload.get("timeframes")
    if not isinstance(frames, dict):
        raise Mt5SnapshotError("MT5 snapshot timeframes payload is missing")
    missing = [name for name in REQUIRED_TIMEFRAMES if not isinstance(frames.get(name), dict)]
    if missing:
        raise Mt5SnapshotError(f"MT5 snapshot missing timeframes: {', '.join(missing)}")
    return payload


def _rsi_signal(value: float) -> str:
    if value <= 30:
        return "Oversold"
    if value >= 70:
        return "Overbought"
    return "Neutral"


def _volatility(atr_pct: float) -> str:
    if atr_pct >= 0.5:
        return "High"
    if atr_pct >= 0.2:
        return "Medium"
    return "Low"


def _frame(snapshot: dict[str, Any], timeframe: str) -> dict[str, Any]:
    try:
        frame = snapshot["timeframes"][timeframe]
        bar = frame["bar"]
        previous = frame["previous_bar"]
    except (KeyError, TypeError) as exc:
        raise Mt5SnapshotError(f"MT5 snapshot has incomplete {timeframe} frame") from exc
    for key in ("open", "high", "low", "close", "tick_volume"):
        _number(bar.get(key), f"{timeframe}.bar.{key}")
    if _number(bar["high"], f"{timeframe}.bar.high") < _number(bar["low"], f"{timeframe}.bar.low"):
        raise Mt5SnapshotError(f"MT5 snapshot {timeframe} OHLC geometry is invalid")
    _number(previous.get("close"), f"{timeframe}.previous_bar.close")
    return frame


def analyze_mt5_coin(
    symbol: str,
    exchange: str,
    timeframe: str,
    *,
    snapshot_path: str | Path | None = None,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    snapshot = load_mt5_snapshot(snapshot_path, symbol=symbol, max_age_seconds=max_age_seconds)
    frame = _frame(snapshot, timeframe)
    bar = frame["bar"]
    previous = frame["previous_bar"]
    tick = snapshot["tick"]

    bid = _number(tick["bid"], "tick.bid")
    ask = _number(tick["ask"], "tick.ask")
    price = (bid + ask) / 2
    close = _number(bar["close"], f"{timeframe}.bar.close")
    previous_close = _number(previous["close"], f"{timeframe}.previous_bar.close")
    rsi = _number(frame.get("rsi"), f"{timeframe}.rsi")
    rsi_previous = _number(frame.get("rsi_previous"), f"{timeframe}.rsi_previous")
    atr = _number(frame.get("atr"), f"{timeframe}.atr")
    atr_pct = atr / price * 100 if price else 0
    macd = _number(frame.get("macd"), f"{timeframe}.macd")
    macd_signal = _number(frame.get("macd_signal"), f"{timeframe}.macd_signal")
    macd_hist = _number(frame.get("macd_histogram"), f"{timeframe}.macd_histogram")
    bb_upper = _number(frame.get("bb_upper"), f"{timeframe}.bb_upper")
    bb_middle = _number(frame.get("bb_middle"), f"{timeframe}.bb_middle")
    bb_lower = _number(frame.get("bb_lower"), f"{timeframe}.bb_lower")
    bb_width = (bb_upper - bb_lower) / bb_middle if bb_middle else 0
    volume = _number(bar.get("tick_volume"), f"{timeframe}.bar.tick_volume")
    avg_volume = _number(frame.get("avg_tick_volume"), f"{timeframe}.avg_tick_volume")
    volume_ratio = volume / avg_volume if avg_volume > 0 else 0
    volume_signal = "High" if volume_ratio >= 1.5 else "Above Average" if volume_ratio >= 1.1 else "Below Average" if volume_ratio < 0.7 else "Normal"
    trend = str(frame.get("trend") or "Neutral/Ranging")
    adx = _number(frame.get("adx"), f"{timeframe}.adx")
    support = [float(value) for value in frame.get("support", []) if float(value) > 0]
    resistance = [float(value) for value in frame.get("resistance", []) if float(value) > 0]
    pivot = (_number(previous.get("high"), "previous.high") + _number(previous.get("low"), "previous.low") + previous_close) / 3
    change_percent = (close - previous_close) / previous_close * 100 if previous_close else 0
    signal = "BUY" if "bullish" in trend.lower() else "SELL" if "bearish" in trend.lower() else "NEUTRAL"

    return {
        "symbol": f"MT5:{snapshot['symbol']}",
        "exchange": "MT5",
        "source": "MT5",
        "broker": snapshot.get("broker"),
        "timeframe": timeframe,
        "timestamp": tick["time_msc"],
        "price_data": {
            "current_price": price,
            "bid": bid,
            "ask": ask,
            "open": _number(bar["open"], "bar.open"),
            "high": _number(bar["high"], "bar.high"),
            "low": _number(bar["low"], "bar.low"),
            "close": close,
            "change_percent": change_percent,
            "volume": int(volume),
            "spread_points": tick.get("spread_points"),
        },
        "timeframe_context": {"timeframe": timeframe, "bias": trend, "bias_reasons": ["Broker-native MT5 EMA structure"]},
        "rsi": {"value": rsi, "signal": _rsi_signal(rsi), "direction": "Rising" if rsi > rsi_previous else "Falling", "previous": rsi_previous},
        "macd": {"macd_line": macd, "signal_line": macd_signal, "histogram": macd_hist, "crossover": "Bullish" if macd > macd_signal else "Bearish"},
        "ema": {"ema20": frame.get("ema20"), "ema50": frame.get("ema50"), "ema200": frame.get("ema200")},
        "bollinger_bands": {"upper": bb_upper, "middle": bb_middle, "lower": bb_lower, "width": bb_width, "squeeze": bb_width < 0.02, "position": "Above Upper" if price > bb_upper else "Below Lower" if price < bb_lower else "Inside Bands"},
        "atr": {"value": atr, "percent_of_price": atr_pct, "volatility": _volatility(atr_pct)},
        "volume_analysis": {"signal": volume_signal, "ratio": volume_ratio, "current": volume, "average": avg_volume},
        "support_resistance": {"pivot": pivot, "support_levels": support, "resistance_levels": resistance, "support": support, "resistance": resistance},
        "market_structure": {"trend": trend, "trend_strength": "Strong" if adx >= 25 else "Weak", "momentum_aligned": (signal == "BUY" and macd > macd_signal) or (signal == "SELL" and macd < macd_signal), "trend_signals": [f"ADX={adx:.1f}"]},
        "market_sentiment": {"overall_rating": 1 if signal == "BUY" else -1 if signal == "SELL" else 0, "buy_sell_signal": signal, "volatility": _volatility(atr_pct), "momentum": "Bullish" if macd_hist > 0 else "Bearish"},
    }


def run_mt5_multi_timeframe_analysis(
    full_symbol: str,
    exchange: str,
    *,
    snapshot_path: str | Path | None = None,
    max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    symbol = full_symbol.split(":")[-1]
    snapshot = load_mt5_snapshot(snapshot_path, symbol=symbol, max_age_seconds=max_age_seconds)
    timeframes: dict[str, Any] = {}
    net_score = 0
    for name in REQUIRED_TIMEFRAMES:
        frame = _frame(snapshot, name)
        trend = str(frame.get("trend") or "Neutral/Ranging")
        direction = "BUY" if "bullish" in trend.lower() else "SELL" if "bearish" in trend.lower() else "WAIT"
        net_score += 1 if direction == "BUY" else -1 if direction == "SELL" else 0
        timeframes[name] = {"trend": trend, "recommendation": direction, "close": frame["bar"]["close"], "rsi": frame.get("rsi")}

    if net_score == len(REQUIRED_TIMEFRAMES):
        status = "FULLY ALIGNED BULLISH"
    elif net_score == -len(REQUIRED_TIMEFRAMES):
        status = "FULLY ALIGNED BEARISH"
    elif net_score > 0:
        status = "MOSTLY BULLISH"
    elif net_score < 0:
        status = "MOSTLY BEARISH"
    else:
        status = "MIXED/RANGING"
    confidence = "High" if abs(net_score) == len(REQUIRED_TIMEFRAMES) else "Medium" if abs(net_score) >= 2 else "Low"
    return {
        "symbol": f"MT5:{snapshot['symbol']}",
        "exchange": "MT5",
        "source": "MT5",
        "broker": snapshot.get("broker"),
        "timeframes": timeframes,
        "alignment": {"status": status, "net_score": net_score, "confidence": confidence},
    }
