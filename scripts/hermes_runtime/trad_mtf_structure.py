#!/usr/bin/env python3
"""Multi-timeframe structure analysis for XAUUSD entry logic.

Replaces static RSI guards (e.g. 'RSI >= 68 blocks BUY') with a dynamic
read of chart structure across M15 / H1 / H4. The goal: judge trend and
exhaustion from price action and indicator structure, not a fixed RSI number,
so a strong bullish trend that keeps climbing past RSI 80 still allows BUY
pullbacks when structure supports it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(os.getenv("TRAD_REPO_ROOT") or "/Users/waipop/MainWTN/Hermes/trad")
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from tradingview_mcp.core.services.screener_service import analyze_coin  # type: ignore
except Exception:  # pragma: no cover
    analyze_coin = None  # type: ignore[assignment]


def _to_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def fetch_tf(symbol: str, exchange: str, tf: str) -> dict[str, Any] | None:
    """Fetch a fresh technical readout for a timeframe, or None on failure."""
    if analyze_coin is None:
        return None
    try:
        result = analyze_coin(symbol, exchange, tf)
    except Exception:
        return None
    if not isinstance(result, dict) or result.get("error"):
        return None
    return result


def tf_structure(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract a compact structure summary from one timeframe's analysis."""
    tech = payload.get("technical") if isinstance(payload.get("technical"), dict) else {}
    ms = tech.get("market_structure") or {}
    sent = tech.get("market_sentiment") or {}
    rsi = tech.get("rsi") or {}
    ema = tech.get("ema") if isinstance(tech.get("ema"), dict) else {}
    bb = tech.get("bollinger_bands") or {}
    sr = tech.get("support_resistance") or {}
    pd = tech.get("price_data") or {}

    trend = str(ms.get("trend") or "Neutral")
    trend_score = _to_float(ms.get("trend_score")) or 0.0
    momentum = str(sent.get("momentum") or "")
    rsi_val = _to_float(rsi.get("value"))
    rsi_dir = str(rsi.get("direction") or "")
    ema20 = _to_float(ema.get("ema20"))
    ema50 = _to_float(ema.get("ema50"))
    ema200 = _to_float(ema.get("ema200"))
    price = _to_float(pd.get("close") or pd.get("current_price"))

    bull = trend in ("Bullish", "Neutral/Ranging") and "Bull" in momentum
    bear = trend in ("Bearish", "Neutral/Ranging") and "Bear" in momentum

    # EMA alignment (higher-timeframe bias).
    ema_bull = bool(ema20 is not None and ema50 is not None and ema200 is not None
                    and ema20 >= ema50 >= ema200)
    ema_bear = bool(ema20 is not None and ema50 is not None and ema200 is not None
                    and ema20 <= ema50 <= ema200)

    # Position within Bollinger Bands (exhaustion clues, not a hard block).
    bb_upper = _to_float(bb.get("upper"))
    bb_lower = _to_float(bb.get("lower"))
    bb_pos = None
    if bb_upper is not None and bb_lower is not None and price is not None and bb_upper > bb_lower:
        bb_pos = (price - bb_lower) / (bb_upper - bb_lower)

    near_resistance = None
    near_support = None
    try:
        res = _to_float(sr.get("nearest_resistance"))
        sup = _to_float(sr.get("nearest_support"))
        if res is not None and price is not None:
            near_resistance = abs(res - price) / max(0.01, price)
        if sup is not None and price is not None:
            near_support = abs(sup - price) / max(0.01, price)
    except Exception:
        pass

    return {
        "timeframe": payload.get("timeframe"),
        "price": price,
        "trend": trend,
        "trend_score": trend_score,
        "momentum": momentum,
        "rsi": rsi_val,
        "rsi_dir": rsi_dir,
        "ema20": ema20,
        "ema50": ema50,
        "ema200": ema200,
        "ema_bull": ema_bull,
        "ema_bear": ema_bear,
        "bull": bull,
        "bear": bear,
        "bb_pos": bb_pos,
        "near_resistance": near_resistance,
        "near_support": near_support,
    }


def analyze(symbol: str, exchange: str) -> dict[str, Any]:
    """Build a dynamic MTF structure view for entry filtering."""
    tfs: dict[str, dict[str, Any] | None] = {}
    for tf in ("15m", "1h", "4h"):
        tfs[tf] = tf_structure(fetch_tf(symbol, exchange, tf) or {})

    # Higher-timeframe bias from H1/H4 EMA alignment + trend.
    htf = [tfs["1h"], tfs["4h"]]
    htf = [x for x in htf if x]
    bull_votes = sum(1 for x in htf if x.get("ema_bull") or x.get("bull"))
    bear_votes = sum(1 for x in htf if x.get("ema_bear") or x.get("bear"))
    if bull_votes > bear_votes:
        htf_bias = "BULL"
    elif bear_votes > bull_votes:
        htf_bias = "BEAR"
    else:
        htf_bias = "NEUTRAL"

    # M15 immediate structure.
    m15 = tfs["15m"] or {}
    m15_bull = bool(m15.get("ema_bull") or m15.get("bull"))
    m15_bear = bool(m15.get("ema_bear") or m15.get("bear"))

    # RSI exhaustion is dynamic: compare against the timeframe's own band, and
    # only treat it as exhaustion if the higher-timeframe trend is NOT with us.
    def exhaustion(direction: str) -> float:
        """Return 0..1 exhaustion score for a planned direction (BUY/SELL)."""
        score = 0.0
        # M15 RSI extreme.
        rsi = m15.get("rsi")
        if rsi is not None:
            if direction == "BUY" and rsi >= 78:
                score += 0.5
            if direction == "SELL" and rsi <= 22:
                score += 0.5
        # BB position extreme on M15.
        bb = m15.get("bb_pos")
        if bb is not None:
            if direction == "BUY" and bb >= 0.95:
                score += 0.3
            if direction == "SELL" and bb <= 0.05:
                score += 0.3
        # Against higher-timeframe bias => real exhaustion risk.
        if direction == "BUY" and htf_bias == "BEAR":
            score += 0.4
        if direction == "SELL" and htf_bias == "BULL":
            score += 0.4
        # With the trend => not exhaustion, discount the RSI noise.
        if direction == "BUY" and htf_bias == "BULL":
            score -= 0.4
        if direction == "SELL" and htf_bias == "BEAR":
            score -= 0.4
        return max(0.0, min(1.0, score))

    return {
        "tfs": tfs,
        "htf_bias": htf_bias,
        "m15_bull": m15_bull,
        "m15_bear": m15_bear,
        "buy_exhaustion": exhaustion("BUY"),
        "sell_exhaustion": exhaustion("SELL"),
    }


def allow_direction(struct: dict[str, Any], direction: str, max_exhaustion: float = 0.55) -> tuple[bool, str]:
    """Dynamic gate: allow a direction unless exhaustion is high AND against trend.

    Returns (allowed, reason).
    """
    ex = struct.get("buy_exhaustion" if direction == "BUY" else "sell_exhaustion", 0.0)
    htf = struct.get("htf_bias", "NEUTRAL")
    # With the higher-timeframe trend, allow even if short-term RSI is hot.
    if direction == "BUY" and htf == "BULL" and ex < 0.8:
        return True, f"BUY ตามเทรน HTF ({htf}); RSI ร้อนแต่โครงสร้างหนุน"
    if direction == "SELL" and htf == "BEAR" and ex < 0.8:
        return True, f"SELL ตามเทรน HTF ({htf}); RSI เย็นแต่โครงสร้างหนุน"
    if ex >= max_exhaustion:
        return False, (
            f"งด {direction}: exhaustion {ex:.2f} สูง และเป็นสวนเทรน HTF ({htf}); "
            f"รอโครงสร้างกลับตัวก่อน"
        )
    return True, f"{direction} อนุญาต (exhaustion {ex:.2f}, HTF {htf})"


if __name__ == "__main__":
    import json

    s = analyze("XAUUSD", "OANDA")
    print(json.dumps(s, ensure_ascii=False, indent=2, default=str))
