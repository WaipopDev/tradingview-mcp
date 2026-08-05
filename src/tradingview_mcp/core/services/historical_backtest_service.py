"""DB-backed historical candle backtesting for MGT/Analyst.

Phase 2B reads `historical_candles` collected from TradingView and stores
repeatable backtest runs/trades. It is intentionally deterministic and does not
modify live trading logic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from tradingview_mcp.core.services.indicators_calc import calc_atr, calc_bollinger, calc_ema, calc_rsi
from tradingview_mcp.core.storage.database import PathLike, connect_database, initialize_database

WIN_RESULTS = {"TP"}
LOSS_RESULTS = {"SL"}
_VALID_STRATEGIES = {"bollinger_rejection", "ema_trend", "live_logic_replay", "production_entry_replay"}


@dataclass(frozen=True)
class Candle:
    ts: int
    datetime_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def session_label(datetime_utc: str) -> str:
    try:
        dt = datetime.fromisoformat(datetime_utc.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hour_ict = (dt.astimezone(timezone.utc).hour + 7) % 24
    except Exception:
        return "unknown"
    if 6 <= hour_ict < 14:
        return "Asia"
    if 14 <= hour_ict < 19:
        return "London"
    if 19 <= hour_ict < 23:
        return "London/NY overlap"
    return "NY/late"


def ensure_backtest_schema(db_path: PathLike | None = None) -> None:
    db = initialize_database(db_path)
    with connect_database(db) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS backtest_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT NOT NULL,
              exchange TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              strategy TEXT NOT NULL,
              params_json TEXT,
              candle_count INTEGER NOT NULL,
              date_from TEXT,
              date_to TEXT,
              total_trades INTEGER NOT NULL,
              wins INTEGER NOT NULL,
              losses INTEGER NOT NULL,
              win_rate REAL NOT NULL,
              expectancy_r REAL NOT NULL,
              avg_mfe REAL NOT NULL,
              avg_mae REAL NOT NULL,
              max_loss_streak INTEGER NOT NULL,
              summary_json TEXT,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_backtest_runs_lookup
            ON backtest_runs(symbol, exchange, timeframe, strategy, created_at DESC);

            CREATE TABLE IF NOT EXISTS backtest_trades (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              run_id INTEGER NOT NULL,
              symbol TEXT NOT NULL,
              exchange TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              strategy TEXT NOT NULL,
              direction TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
              setup_type TEXT,
              session_label TEXT,
              entry_ts INTEGER NOT NULL,
              entry_time TEXT NOT NULL,
              entry_price REAL NOT NULL,
              sl REAL NOT NULL,
              tp REAL NOT NULL,
              exit_ts INTEGER,
              exit_time TEXT,
              exit_price REAL,
              result TEXT NOT NULL,
              r_multiple REAL NOT NULL,
              mfe REAL NOT NULL,
              mae REAL NOT NULL,
              hold_bars INTEGER NOT NULL,
              metadata_json TEXT,
              FOREIGN KEY(run_id) REFERENCES backtest_runs(id)
            );
            CREATE INDEX IF NOT EXISTS idx_backtest_trades_run
            ON backtest_trades(run_id, entry_ts);
            """
        )


def load_candles(symbol: str, exchange: str, timeframe: str, db_path: PathLike | None = None, limit: int | None = None) -> list[Candle]:
    initialize_database(db_path)
    sql = """
        SELECT ts, datetime_utc, open, high, low, close, volume
        FROM historical_candles
        WHERE UPPER(symbol)=UPPER(?) AND UPPER(exchange)=UPPER(?) AND timeframe=?
        ORDER BY ts ASC
    """
    params: list[Any] = [symbol, exchange, timeframe]
    if limit:
        sql = "SELECT * FROM (" + sql + " LIMIT ?) ORDER BY ts ASC"
        params.append(int(limit))
    with connect_database(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [Candle(ts=int(r["ts"]), datetime_utc=str(r["datetime_utc"]), open=float(r["open"]), high=float(r["high"]), low=float(r["low"]), close=float(r["close"]), volume=None if r["volume"] is None else float(r["volume"])) for r in rows]


def _csv_set(value: str | Iterable[str] | None) -> set[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
    else:
        parts = [str(p).strip() for p in value]
    out = {p for p in parts if p}
    return out or None


def _mtf_direction_map(candles: list[Candle], higher: list[Candle]) -> dict[int, str]:
    """Map each base candle timestamp to latest higher-timeframe EMA trend."""
    if len(higher) < 60:
        return {}
    closes = [c.close for c in higher]
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    higher_dirs: list[tuple[int, str]] = []
    for i, c in enumerate(higher):
        e20, e50 = ema20[i], ema50[i]
        if e20 is None or e50 is None:
            direction = "RANGE"
        elif e20 > e50:
            direction = "BUY"
        elif e20 < e50:
            direction = "SELL"
        else:
            direction = "RANGE"
        higher_dirs.append((c.ts, direction))
    mapping: dict[int, str] = {}
    j = 0
    current = "RANGE"
    for c in candles:
        while j < len(higher_dirs) and higher_dirs[j][0] <= c.ts:
            current = higher_dirs[j][1]
            j += 1
        mapping[c.ts] = current
    return mapping


def _risk(entry: float, sl: float) -> float:
    return max(0.01, abs(entry - sl))


def _score_trade(direction: str, rsi: float | None, ema20: float | None, ema50: float | None, bb_pos: str | None) -> int:
    score = 50
    if direction == "BUY":
        if rsi is not None and rsi <= 35:
            score += 15
        if ema20 is not None and ema50 is not None and ema20 >= ema50:
            score += 10
        if bb_pos == "below_lower":
            score += 15
    else:
        if rsi is not None and rsi >= 65:
            score += 15
        if ema20 is not None and ema50 is not None and ema20 <= ema50:
            score += 10
        if bb_pos == "above_upper":
            score += 15
    return max(0, min(100, score))


def _candidate_live_logic_replay(
    candles: list[Candle],
    score_gate: int,
    allowed_sessions: set[str] | None = None,
    allowed_directions: set[str] | None = None,
    allowed_setups: set[str] | None = None,
    mtf_direction_by_ts: Mapping[int, str] | None = None,
    mtf_filter: str = "off",
) -> list[dict[str, Any]]:
    """Approximate current Telegram entry gate over historical candles.

    Mirrors the important live guards rather than every integration detail:
    - derived setup score must clear score_gate
    - BUY avoids very hot RSI; SELL avoids very cold RSI
    - same-direction near-duplicate zone guard for 45 minutes
    - after 3 same-direction SL/CUT-like recent simulated losses is handled by
      the trade simulator/report layer in Phase 2C analysis, not during signal
      generation because future outcomes are unknown at entry time.
    """
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    rsi = calc_rsi(closes, 14)
    atr = calc_atr(highs, lows, closes, 14)
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    bb = calc_bollinger(closes, 20, 2.0)
    signals: list[dict[str, Any]] = []
    recent_zones: list[tuple[int, str, float, float]] = []
    for i, c in enumerate(candles):
        atr_i, rsi_i, ema20_i, ema50_i = atr[i], rsi[i], ema20[i], ema50[i]
        if atr_i is None or rsi_i is None or ema20_i is None or ema50_i is None:
            continue
        direction: str | None = None
        setup_type = "live_logic/continuation"
        score = 50
        # Trend-following pullback side of current entry derivation.
        if ema20_i > ema50_i and c.close > ema20_i and 42 <= rsi_i <= 66:
            direction = "BUY"
            score += 20
            setup_type = "live_logic/BUY_continuation"
        elif ema20_i < ema50_i and c.close < ema20_i and 34 <= rsi_i <= 58:
            direction = "SELL"
            score += 20
            setup_type = "live_logic/SELL_continuation"
        # Range rejection / scalp-watch style side.
        lower_i = bb["lower"][i]
        upper_i = bb["upper"][i]
        if lower_i is not None and c.low <= lower_i and c.close > c.open and rsi_i <= 48:
            direction = "BUY"
            score += 25
            setup_type = "live_logic/BUY_rejection"
        elif upper_i is not None and c.high >= upper_i and c.close < c.open and rsi_i >= 52:
            direction = "SELL"
            score += 25
            setup_type = "live_logic/SELL_rejection"
        if direction is None:
            continue
        candle_session = session_label(c.datetime_utc)
        if allowed_sessions and candle_session not in allowed_sessions:
            continue
        if allowed_directions and direction not in allowed_directions:
            continue
        if allowed_setups and setup_type not in allowed_setups:
            continue
        if mtf_filter != "off" and mtf_direction_by_ts:
            mtf_dir = mtf_direction_by_ts.get(c.ts, "RANGE")
            if mtf_filter == "with_trend" and mtf_dir in {"BUY", "SELL"} and mtf_dir != direction:
                continue
            if mtf_filter == "strict_with_trend" and mtf_dir != direction:
                continue
            if mtf_filter == "rejection_countertrend_only" and "rejection" in setup_type and mtf_dir == direction:
                continue
        if direction == "BUY" and rsi_i >= 70:
            continue
        if direction == "SELL" and rsi_i <= 30:
            continue
        # RR/ATR quality proxy.
        if atr_i <= 0:
            continue
        score += 10
        score = max(0, min(100, score))
        if score < score_gate:
            continue
        entry_proxy = c.close
        zone_low = entry_proxy - min(3.0, atr_i * 0.4)
        zone_high = entry_proxy + min(3.0, atr_i * 0.4)
        duplicate = False
        for prev_ts, prev_dir, prev_low, prev_high in reversed(recent_zones):
            if c.ts - prev_ts > 45 * 60:
                break
            if prev_dir != direction:
                continue
            center_distance = abs(((prev_low + prev_high) / 2) - ((zone_low + zone_high) / 2))
            overlap = max(0.0, min(prev_high, zone_high) - max(prev_low, zone_low))
            if center_distance <= 3.0 or overlap / max(0.01, zone_high - zone_low) >= 0.35:
                duplicate = True
                break
        if duplicate:
            continue
        recent_zones.append((c.ts, direction, zone_low, zone_high))
        signals.append({
            "index": i,
            "direction": direction,
            "score": score,
            "setup_type": setup_type,
            "rsi": rsi_i,
            "atr": atr_i,
            "ema20": ema20_i,
            "ema50": ema50_i,
            "zone_low": zone_low,
            "zone_high": zone_high,
            "mtf_direction": mtf_direction_by_ts.get(c.ts, "RANGE") if mtf_direction_by_ts else "off",
        })
    return signals


def _candidate_signals(
    candles: list[Candle],
    strategy: str,
    score_gate: int,
    allowed_sessions: set[str] | None = None,
    allowed_directions: set[str] | None = None,
    allowed_setups: set[str] | None = None,
    mtf_direction_by_ts: Mapping[int, str] | None = None,
    mtf_filter: str = "off",
) -> list[dict[str, Any]]:
    if strategy == "live_logic_replay":
        return _candidate_live_logic_replay(candles, score_gate, allowed_sessions, allowed_directions, allowed_setups, mtf_direction_by_ts, mtf_filter)
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    rsi = calc_rsi(closes, 14)
    atr = calc_atr(highs, lows, closes, 14)
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    bb = calc_bollinger(closes, 20, 2.0)
    signals: list[dict[str, Any]] = []
    for i, c in enumerate(candles):
        atr_i, rsi_i, ema20_i, ema50_i = atr[i], rsi[i], ema20[i], ema50[i]
        if atr_i is None or rsi_i is None or ema20_i is None or ema50_i is None:
            continue
        direction: str | None = None
        setup_type = strategy
        bb_pos = None
        if strategy == "bollinger_rejection":
            lower_i = bb["lower"][i]
            upper_i = bb["upper"][i]
            if lower_i is not None and c.low <= lower_i and c.close > c.open:
                direction, bb_pos, setup_type = "BUY", "below_lower", "rejection/mean-reversion"
            elif upper_i is not None and c.high >= upper_i and c.close < c.open:
                direction, bb_pos, setup_type = "SELL", "above_upper", "rejection/mean-reversion"
        elif strategy == "ema_trend":
            if ema20_i > ema50_i and c.low <= ema20_i and c.close > ema20_i and 40 <= rsi_i <= 68:
                direction, setup_type = "BUY", "continuation/trend"
            elif ema20_i < ema50_i and c.high >= ema20_i and c.close < ema20_i and 32 <= rsi_i <= 60:
                direction, setup_type = "SELL", "continuation/trend"
        if direction is None:
            continue
        score = _score_trade(direction, rsi_i, ema20_i, ema50_i, bb_pos)
        if score < score_gate:
            continue
        signals.append({"index": i, "direction": direction, "score": score, "setup_type": setup_type, "rsi": rsi_i, "atr": atr_i, "ema20": ema20_i, "ema50": ema50_i})
    return signals


def _simulate_trade(candles: list[Candle], signal: Mapping[str, Any], rr: float, sl_atr: float, max_hold_bars: int) -> dict[str, Any] | None:
    i = int(signal["index"])
    if i + 1 >= len(candles):
        return None
    entry_c = candles[i + 1]
    direction = str(signal["direction"])
    entry = entry_c.open
    atr = float(signal["atr"])
    if direction == "BUY":
        sl = entry - (atr * sl_atr)
        tp = entry + (entry - sl) * rr
    else:
        sl = entry + (atr * sl_atr)
        tp = entry - (sl - entry) * rr
    risk = _risk(entry, sl)
    mfe = 0.0
    mae = 0.0
    exit_price = candles[min(len(candles) - 1, i + max_hold_bars)].close
    exit_c = candles[min(len(candles) - 1, i + max_hold_bars)]
    result = "TIME_EXIT"
    hold = 0
    for j in range(i + 1, min(len(candles), i + 1 + max_hold_bars)):
        c = candles[j]
        hold = j - i
        if direction == "BUY":
            mfe = max(mfe, c.high - entry)
            mae = max(mae, entry - c.low)
            hit_sl = c.low <= sl
            hit_tp = c.high >= tp
        else:
            mfe = max(mfe, entry - c.low)
            mae = max(mae, c.high - entry)
            hit_sl = c.high >= sl
            hit_tp = c.low <= tp
        if hit_sl and hit_tp:
            # Conservative intrabar ordering: if both touched, count SL first.
            result = "SL"
            exit_price = sl
            exit_c = c
            break
        if hit_sl:
            result = "SL"
            exit_price = sl
            exit_c = c
            break
        if hit_tp:
            result = "TP"
            exit_price = tp
            exit_c = c
            break
    if result == "TP":
        r_multiple = rr
    elif result == "SL":
        r_multiple = -1.0
    else:
        if direction == "BUY":
            r_multiple = (exit_price - entry) / risk
        else:
            r_multiple = (entry - exit_price) / risk
    return {
        "direction": direction,
        "setup_type": signal.get("setup_type"),
        "session_label": session_label(entry_c.datetime_utc),
        "entry_ts": entry_c.ts,
        "entry_time": entry_c.datetime_utc,
        "entry_price": entry,
        "sl": sl,
        "tp": tp,
        "exit_ts": exit_c.ts,
        "exit_time": exit_c.datetime_utc,
        "exit_price": exit_price,
        "result": result,
        "r_multiple": r_multiple,
        "mfe": mfe,
        "mae": mae,
        "hold_bars": hold,
        "metadata": {k: signal.get(k) for k in ["score", "rsi", "atr", "ema20", "ema50", "mtf_direction", "zone_low", "zone_high"]},
    }


def summarize_trades(trades: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(trades)
    wins = sum(1 for t in trades if t["result"] in WIN_RESULTS)
    losses = sum(1 for t in trades if t["result"] in LOSS_RESULTS)
    r_values = [float(t["r_multiple"]) for t in trades]
    loss_streak = max_loss_streak = 0
    for t in trades:
        if t["result"] in LOSS_RESULTS:
            loss_streak += 1
            max_loss_streak = max(max_loss_streak, loss_streak)
        elif t["result"] in WIN_RESULTS:
            loss_streak = 0
    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / total * 100 if total else 0.0,
        "expectancy_r": sum(r_values) / total if total else 0.0,
        "avg_mfe": sum(float(t["mfe"]) for t in trades) / total if total else 0.0,
        "avg_mae": sum(float(t["mae"]) for t in trades) / total if total else 0.0,
        "max_loss_streak": max_loss_streak,
    }


MIN_ENTRY_SCORE = 70
MIN_SL_DISTANCE = 5.0
MAX_SL_DISTANCE = 8.0


def _prod_clamp_sl(direction: str, entry_low: float, entry_high: float, sl: float) -> float:
    if direction == "BUY":
        distance = max(MIN_SL_DISTANCE, min(MAX_SL_DISTANCE, entry_high - sl))
        return entry_high - distance
    distance = max(MIN_SL_DISTANCE, min(MAX_SL_DISTANCE, sl - entry_low))
    return entry_low + distance


def _production_order_from_candle(candles: list[Candle], i: int, rsi: list[float | None], atr: list[float | None], ema20: list[float | None], ema50: list[float | None]) -> dict[str, Any] | None:
    c = candles[i]
    rsi_i, atr_i, ema20_i, ema50_i = rsi[i], atr[i], ema20[i], ema50[i]
    if rsi_i is None or atr_i is None or ema20_i is None or ema50_i is None:
        return None
    price = c.close
    sd1_low, sd1_high = price - atr_i, price + atr_i
    sd2_low, sd2_high = price - (2 * atr_i), price + (2 * atr_i)
    pivot = (c.high + c.low + c.close) / 3
    bullish = price > ema20_i and ema20_i > ema50_i and 45 <= rsi_i <= 68
    bearish = price < ema20_i and ema20_i < ema50_i and 32 <= rsi_i <= 55
    if not (bullish or bearish):
        return None
    if bearish:
        direction = "SELL"
        entry_low = min(max(price + 1.0, pivot), max(ema20_i, pivot))
        entry_high = max(ema20_i, pivot, price + 2.5)
        sl = entry_high + 5.0
        tp1, tp2 = sd1_low, sd2_low
    else:
        direction = "BUY"
        entry_low = min(max(sd1_low, price - 3.0), price)
        entry_high = max(min(price + 0.8, sd1_high), entry_low)
        sl = entry_low - 5.0
        tp1, tp2 = sd1_high, sd2_high
    entry_low, entry_high = min(entry_low, entry_high), max(entry_low, entry_high)
    sl = _prod_clamp_sl(direction, entry_low, entry_high, sl)
    rr = abs(tp1 - entry_high) / max(0.01, abs(entry_low - sl))
    score = 70
    if direction == "BUY" and 45 <= rsi_i <= 66:
        score += 15
    elif direction == "SELL" and 34 <= rsi_i <= 55:
        score += 15
    elif (direction == "BUY" and rsi_i >= 70) or (direction == "SELL" and rsi_i <= 30):
        score -= 20
    if rr >= 1.5:
        score += 15
    elif rr < 1.0:
        score -= 15
    score = max(0, min(100, int(round(score))))
    if score < MIN_ENTRY_SCORE:
        return None
    return {"index": i, "direction": direction, "score": score, "setup_type": "production_entry/continuation_trend", "session_label": session_label(c.datetime_utc), "entry_low": entry_low, "entry_high": entry_high, "sl": sl, "tp": tp1, "tp2": tp2, "rr": rr, "rsi": rsi_i, "atr": atr_i, "ema20": ema20_i, "ema50": ema50_i}


def _simulate_production_order(candles: list[Candle], order: Mapping[str, Any], max_hold_bars: int) -> dict[str, Any] | None:
    i = int(order["index"])
    direction = str(order["direction"])
    entry_low, entry_high = float(order["entry_low"]), float(order["entry_high"])
    sl, tp = float(order["sl"]), float(order["tp"])
    entry_c: Candle | None = None
    entry_j = -1
    for j in range(i + 1, min(len(candles), i + 1 + max_hold_bars)):
        c = candles[j]
        if c.low <= entry_high and c.high >= entry_low:
            entry_c = c
            entry_j = j
            break
    if entry_c is None:
        return None
    entry = min(max(entry_c.open, entry_low), entry_high)
    risk = _risk(entry, sl)
    mfe = mae = 0.0
    result = "TIME_EXIT"
    exit_c = candles[min(len(candles) - 1, entry_j + max_hold_bars)]
    exit_price = exit_c.close
    hold = 0
    for j in range(entry_j, min(len(candles), entry_j + max_hold_bars)):
        c = candles[j]
        hold = j - entry_j + 1
        if direction == "BUY":
            mfe = max(mfe, c.high - entry)
            mae = max(mae, entry - c.low)
            hit_sl, hit_tp = c.low <= sl, c.high >= tp
        else:
            mfe = max(mfe, entry - c.low)
            mae = max(mae, c.high - entry)
            hit_sl, hit_tp = c.high >= sl, c.low <= tp
        if hit_sl and hit_tp:
            result, exit_price, exit_c = "SL", sl, c
            break
        if hit_sl:
            result, exit_price, exit_c = "SL", sl, c
            break
        if hit_tp:
            result, exit_price, exit_c = "TP", tp, c
            break
    if result == "TP":
        r_multiple = abs(tp - entry) / risk
    elif result == "SL":
        r_multiple = -1.0
    else:
        r_multiple = (exit_price - entry) / risk if direction == "BUY" else (entry - exit_price) / risk
    return {"direction": direction, "setup_type": order.get("setup_type"), "session_label": order.get("session_label"), "entry_ts": entry_c.ts, "entry_time": entry_c.datetime_utc, "entry_price": entry, "sl": sl, "tp": tp, "exit_ts": exit_c.ts, "exit_time": exit_c.datetime_utc, "exit_price": exit_price, "result": result, "r_multiple": r_multiple, "mfe": mfe, "mae": mae, "hold_bars": hold, "metadata": {k: order.get(k) for k in ["score", "rsi", "atr", "ema20", "ema50", "entry_low", "entry_high", "rr", "tp2"]}}


def _blocked_by_production_duplicate(order: Mapping[str, Any], open_trades: list[dict[str, Any]], recent_orders: list[Mapping[str, Any]], now_ts: int) -> bool:
    direction = str(order["direction"])
    low, high = float(order["entry_low"]), float(order["entry_high"])
    center = (low + high) / 2
    for t in open_trades:
        if t["direction"] != direction:
            continue
        old_low = float(t["metadata"].get("entry_low") or t["entry_price"])
        old_high = float(t["metadata"].get("entry_high") or t["entry_price"])
        overlap = max(0.0, min(old_high, high) - max(old_low, low))
        if overlap / max(0.01, high - low) >= 0.25 or abs(((old_low + old_high) / 2) - center) <= 10.0:
            return True
    if int(order.get("score") or 0) >= 85:
        return False
    for prev in reversed(recent_orders):
        if now_ts - int(prev["ts"]) > 45 * 60:
            break
        if prev["direction"] != direction:
            continue
        old_low, old_high = float(prev["entry_low"]), float(prev["entry_high"])
        overlap = max(0.0, min(old_high, high) - max(old_low, low))
        if abs(((old_low + old_high) / 2) - center) <= 3.0 or overlap / max(0.01, high - low) >= 0.35:
            return True
    return False


def _blocked_by_production_adaptive(order: Mapping[str, Any], closed_trades: list[dict[str, Any]], now_ts: int) -> bool:
    direction = str(order["direction"])
    rows = [t for t in reversed(closed_trades) if t["direction"] == direction][:8]
    if not rows:
        return False
    recent3_losses = len(rows) >= 3 and all(str(r["result"]) in {"SL", "CUT"} for r in rows[:3])
    if recent3_losses:
        last_closed_ts = int(rows[0]["exit_ts"] or now_ts)
        if now_ts - last_closed_ts < 90 * 60:
            return True
        if int(order.get("score") or 0) < 85:
            return True
    recent_90_losses = sum(1 for r in rows if now_ts - int(r["exit_ts"] or now_ts) <= 90 * 60 and str(r["result"]) in {"SL", "CUT"})
    if recent_90_losses >= 3 and int(order.get("score") or 0) < 85:
        return True
    rsi = order.get("rsi")
    if rsi is not None and direction == "BUY" and float(rsi) >= 68:
        return True
    if rsi is not None and direction == "SELL" and float(rsi) <= 32:
        return True
    return False


def _run_production_entry_replay(candles: list[Candle], max_hold_bars: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    rsi = calc_rsi(closes, 14)
    atr = calc_atr(highs, lows, closes, 14)
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    trades: list[dict[str, Any]] = []
    open_trades: list[dict[str, Any]] = []
    recent_orders: list[Mapping[str, Any]] = []
    blocked_duplicate = blocked_adaptive = candidates = 0
    for i, c in enumerate(candles[:-2]):
        open_trades = [t for t in open_trades if int(t.get("exit_ts") or 0) > c.ts]
        order = _production_order_from_candle(candles, i, rsi, atr, ema20, ema50)
        if not order:
            continue
        candidates += 1
        if _blocked_by_production_duplicate(order, open_trades, recent_orders, c.ts):
            blocked_duplicate += 1
            continue
        if _blocked_by_production_adaptive(order, trades, c.ts):
            blocked_adaptive += 1
            continue
        trade = _simulate_production_order(candles, order, max_hold_bars)
        recent_orders.append({"ts": c.ts, "direction": order["direction"], "entry_low": order["entry_low"], "entry_high": order["entry_high"]})
        if trade is None:
            continue
        trades.append(trade)
        if str(trade["result"]) == "TIME_EXIT":
            open_trades.append(trade)
    meta = {"production_candidates": candidates, "blocked_duplicate": blocked_duplicate, "blocked_adaptive": blocked_adaptive}
    return trades, meta


def run_db_backtest(
    symbol: str = "XAUUSD",
    exchange: str = "OANDA",
    timeframe: str = "15m",
    strategy: str = "bollinger_rejection",
    db_path: PathLike | None = None,
    score_gate: int = 60,
    rr: float = 1.5,
    sl_atr: float = 1.2,
    max_hold_bars: int = 12,
    limit: int | None = None,
    store: bool = True,
    allowed_sessions: str | Iterable[str] | None = None,
    allowed_directions: str | Iterable[str] | None = None,
    allowed_setups: str | Iterable[str] | None = None,
    mtf_filter: str = "off",
    mtf_timeframe: str = "1h",
) -> dict[str, Any]:
    strategy = strategy.lower().strip()
    if strategy not in _VALID_STRATEGIES:
        return {"error": f"Unknown strategy {strategy!r}; choose {sorted(_VALID_STRATEGIES)}"}
    ensure_backtest_schema(db_path)
    candles = load_candles(symbol, exchange, timeframe, db_path, limit)
    if len(candles) < 60:
        return {"error": f"Not enough candles ({len(candles)}); collect at least 60 bars first."}
    if strategy == "production_entry_replay":
        trades, production_meta = _run_production_entry_replay(candles, int(max_hold_bars))
        summary = summarize_trades(trades)
        params = {"score_gate": MIN_ENTRY_SCORE, "rr": "production_tp1", "sl_band": [MIN_SL_DISTANCE, MAX_SL_DISTANCE], "max_hold_bars": int(max_hold_bars), "limit": limit, **production_meta}
    else:
        session_filter = _csv_set(allowed_sessions)
        direction_filter = _csv_set(allowed_directions)
        setup_filter = _csv_set(allowed_setups)
        mtf_filter = (mtf_filter or "off").strip()
        if mtf_filter not in {"off", "with_trend", "strict_with_trend", "rejection_countertrend_only"}:
            return {"error": "Unknown mtf_filter; choose off, with_trend, strict_with_trend, rejection_countertrend_only"}
        mtf_map: dict[int, str] | None = None
        if mtf_filter != "off":
            higher = load_candles(symbol, exchange, mtf_timeframe, db_path, None)
            mtf_map = _mtf_direction_map(candles, higher)
            if not mtf_map:
                return {"error": f"Not enough {mtf_timeframe} candles for mtf_filter={mtf_filter}"}
        signals = _candidate_signals(candles, strategy, int(score_gate), session_filter, direction_filter, setup_filter, mtf_map, mtf_filter)
        trades = [t for s in signals if (t := _simulate_trade(candles, s, float(rr), float(sl_atr), int(max_hold_bars))) is not None]
        summary = summarize_trades(trades)
        params = {
            "score_gate": int(score_gate),
            "rr": float(rr),
            "sl_atr": float(sl_atr),
            "max_hold_bars": int(max_hold_bars),
            "limit": limit,
            "allowed_sessions": sorted(session_filter) if session_filter else None,
            "allowed_directions": sorted(direction_filter) if direction_filter else None,
            "allowed_setups": sorted(setup_filter) if setup_filter else None,
            "mtf_filter": mtf_filter,
            "mtf_timeframe": mtf_timeframe,
        }
    result = {
        "symbol": symbol.upper(),
        "exchange": exchange.upper(),
        "timeframe": timeframe,
        "strategy": strategy,
        "params": params,
        "candle_count": len(candles),
        "date_from": candles[0].datetime_utc,
        "date_to": candles[-1].datetime_utc,
        **summary,
        "recent_trades": trades[-5:],
        "data_source": "local historical_candles from TradingView",
        "created_at": utc_now_iso(),
    }
    if store:
        result["run_id"] = store_backtest_result(result, trades, db_path)
    return result


def store_backtest_result(result: Mapping[str, Any], trades: list[dict[str, Any]], db_path: PathLike | None = None) -> int:
    ensure_backtest_schema(db_path)
    with connect_database(db_path) as conn:
        cur = conn.execute(
            """
            INSERT INTO backtest_runs
            (symbol, exchange, timeframe, strategy, params_json, candle_count, date_from, date_to,
             total_trades, wins, losses, win_rate, expectancy_r, avg_mfe, avg_mae, max_loss_streak, summary_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result["symbol"], result["exchange"], result["timeframe"], result["strategy"],
                json.dumps(result.get("params") or {}, ensure_ascii=False, sort_keys=True),
                result["candle_count"], result.get("date_from"), result.get("date_to"),
                result["total_trades"], result["wins"], result["losses"], result["win_rate"],
                result["expectancy_r"], result["avg_mfe"], result["avg_mae"], result["max_loss_streak"],
                json.dumps({k: result.get(k) for k in ["recent_trades", "data_source"]}, ensure_ascii=False, sort_keys=True),
                result.get("created_at") or utc_now_iso(),
            ),
        )
        if cur.lastrowid is None:
            raise RuntimeError("SQLite did not return a backtest run id")
        run_id = int(cur.lastrowid)
        for t in trades:
            conn.execute(
                """
                INSERT INTO backtest_trades
                (run_id, symbol, exchange, timeframe, strategy, direction, setup_type, session_label,
                 entry_ts, entry_time, entry_price, sl, tp, exit_ts, exit_time, exit_price, result,
                 r_multiple, mfe, mae, hold_bars, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, result["symbol"], result["exchange"], result["timeframe"], result["strategy"],
                    t["direction"], t.get("setup_type"), t.get("session_label"), t["entry_ts"], t["entry_time"],
                    t["entry_price"], t["sl"], t["tp"], t.get("exit_ts"), t.get("exit_time"), t.get("exit_price"),
                    t["result"], t["r_multiple"], t["mfe"], t["mae"], t["hold_bars"],
                    json.dumps(t.get("metadata") or {}, ensure_ascii=False, sort_keys=True),
                ),
            )
    return run_id
