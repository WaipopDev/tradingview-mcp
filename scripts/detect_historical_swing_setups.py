#!/usr/bin/env python3
"""Detect full historical swing structure and swing trade setups.

Read-only/feature phase for XAUUSD swing logic. It derives pivot swings from
`historical_candles`, labels HH/HL/LH/LL, writes `historical_swing_points`,
then creates `historical_swing_setups` using swing trend + SMC features.
It does not modify production entry/order logic.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Candle:
    ts: int
    datetime_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def timeframe_seconds(timeframe: str) -> int:
    tf = timeframe.lower().strip()
    if tf.endswith("m"):
        return int(tf[:-1]) * 60
    if tf.endswith("h"):
        return int(tf[:-1]) * 3600
    if tf in {"1d", "d"}:
        return 86400
    return 0


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


def load_candles(con: sqlite3.Connection, symbol: str, exchange: str, timeframe: str, limit: int | None = None) -> list[Candle]:
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
    rows = con.execute(sql, params).fetchall()
    return [Candle(int(r["ts"]), str(r["datetime_utc"]), float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), None if r["volume"] is None else float(r["volume"])) for r in rows]


def ensure_schema(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS historical_swing_points (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          exchange TEXT NOT NULL,
          timeframe TEXT NOT NULL,
          ts INTEGER NOT NULL,
          datetime_utc TEXT NOT NULL,
          pivot_type TEXT NOT NULL CHECK(pivot_type IN ('HIGH','LOW')),
          price REAL NOT NULL,
          label TEXT,
          swing_direction TEXT,
          strength REAL,
          leg_bars INTEGER,
          confirmed_at_ts INTEGER,
          confirmed_at_time TEXT,
          created_at TEXT NOT NULL,
          UNIQUE(symbol, exchange, timeframe, ts, pivot_type)
        );
        CREATE INDEX IF NOT EXISTS idx_historical_swing_points_lookup
        ON historical_swing_points(symbol, exchange, timeframe, ts);

        CREATE TABLE IF NOT EXISTS historical_swing_setups (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          exchange TEXT NOT NULL,
          timeframe TEXT NOT NULL,
          ts INTEGER NOT NULL,
          datetime_utc TEXT NOT NULL,
          direction TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
          setup_type TEXT NOT NULL,
          trend_state TEXT,
          trigger_price REAL NOT NULL,
          entry_low REAL NOT NULL,
          entry_high REAL NOT NULL,
          sl REAL NOT NULL,
          tp1 REAL NOT NULL,
          tp2 REAL,
          rr REAL NOT NULL,
          score INTEGER NOT NULL,
          components_json TEXT,
          created_at TEXT NOT NULL,
          UNIQUE(symbol, exchange, timeframe, ts, direction, setup_type)
        );
        CREATE INDEX IF NOT EXISTS idx_historical_swing_setups_lookup
        ON historical_swing_setups(symbol, exchange, timeframe, ts, direction);
        """
    )


def detect_pivots(candles: list[Candle], left: int, right: int, min_move: float) -> list[dict[str, Any]]:
    raw: list[dict[str, Any]] = []
    for i in range(left, len(candles) - right):
        c = candles[i]
        prev_window = candles[i - left:i]
        next_window = candles[i + 1:i + 1 + right]
        is_high = all(c.high > x.high for x in prev_window) and all(c.high >= x.high for x in next_window)
        is_low = all(c.low < x.low for x in prev_window) and all(c.low <= x.low for x in next_window)
        if is_high:
            raw.append({"index": i, "ts": c.ts, "datetime_utc": c.datetime_utc, "pivot_type": "HIGH", "price": c.high, "confirmed_index": i + right})
        if is_low:
            raw.append({"index": i, "ts": c.ts, "datetime_utc": c.datetime_utc, "pivot_type": "LOW", "price": c.low, "confirmed_index": i + right})
    raw.sort(key=lambda r: (r["index"], 0 if r["pivot_type"] == "LOW" else 1))

    # Zig-zag compression: alternate HIGH/LOW; keep more extreme same-type pivot.
    pivots: list[dict[str, Any]] = []
    for r in raw:
        if not pivots:
            pivots.append(r)
            continue
        last = pivots[-1]
        if r["pivot_type"] == last["pivot_type"]:
            if (r["pivot_type"] == "HIGH" and r["price"] > last["price"]) or (r["pivot_type"] == "LOW" and r["price"] < last["price"]):
                pivots[-1] = r
            continue
        if abs(float(r["price"]) - float(last["price"])) < min_move:
            continue
        pivots.append(r)

    last_high: float | None = None
    last_low: float | None = None
    prev: dict[str, Any] | None = None
    out: list[dict[str, Any]] = []
    for p in pivots:
        label = None
        if p["pivot_type"] == "HIGH":
            label = "HH" if last_high is not None and p["price"] > last_high else "LH" if last_high is not None else "H"
            last_high = float(p["price"])
        else:
            label = "HL" if last_low is not None and p["price"] > last_low else "LL" if last_low is not None else "L"
            last_low = float(p["price"])
        swing_direction = None
        strength = None
        leg_bars = None
        if prev:
            swing_direction = "UP" if p["price"] > prev["price"] else "DOWN"
            leg_bars = int(p["index"]) - int(prev["index"])
            strength = abs(float(p["price"]) - float(prev["price"]))
        conf_i = min(len(candles) - 1, int(p["confirmed_index"]))
        out.append({**p, "label": label, "swing_direction": swing_direction, "strength": strength, "leg_bars": leg_bars, "confirmed_at_ts": candles[conf_i].ts, "confirmed_at_time": candles[conf_i].datetime_utc})
        prev = p
    return out


def store_pivots(con: sqlite3.Connection, rows: list[dict[str, Any]], symbol: str, exchange: str, timeframe: str) -> int:
    now = utc_now()
    payload = []
    for r in rows:
        payload.append((symbol.upper(), exchange.upper(), timeframe, r["ts"], r["datetime_utc"], r["pivot_type"], r["price"], r.get("label"), r.get("swing_direction"), r.get("strength"), r.get("leg_bars"), r.get("confirmed_at_ts"), r.get("confirmed_at_time"), now))
    con.executemany(
        """
        INSERT INTO historical_swing_points
        (symbol, exchange, timeframe, ts, datetime_utc, pivot_type, price, label, swing_direction, strength, leg_bars, confirmed_at_ts, confirmed_at_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, exchange, timeframe, ts, pivot_type) DO UPDATE SET
          price=excluded.price, label=excluded.label, swing_direction=excluded.swing_direction,
          strength=excluded.strength, leg_bars=excluded.leg_bars, confirmed_at_ts=excluded.confirmed_at_ts,
          confirmed_at_time=excluded.confirmed_at_time, created_at=excluded.created_at
        """,
        payload,
    )
    return len(payload)


def load_smc_by_ts(con: sqlite3.Connection, symbol: str, exchange: str, timeframe: str) -> dict[int, sqlite3.Row]:
    try:
        rows = con.execute(
            "SELECT * FROM historical_smc_features WHERE UPPER(symbol)=UPPER(?) AND UPPER(exchange)=UPPER(?) AND timeframe=?",
            (symbol, exchange, timeframe),
        ).fetchall()
    except sqlite3.OperationalError:
        return {}
    return {int(r["ts"]): r for r in rows}


def latest_confirmed_pivots(pivots: list[dict[str, Any]], ts: int) -> list[dict[str, Any]]:
    return [p for p in pivots if int(p["confirmed_at_ts"]) <= ts]


def structure_state(recent: list[dict[str, Any]]) -> str:
    labels = [p.get("label") for p in recent[-6:]]
    if "HH" in labels and "HL" in labels and labels[-1] in {"HH", "HL"}:
        return "BULLISH"
    if "LL" in labels and "LH" in labels and labels[-1] in {"LL", "LH"}:
        return "BEARISH"
    return "RANGE"


def build_setups(candles: list[Candle], pivots: list[dict[str, Any]], smc_by_ts: dict[int, sqlite3.Row], symbol: str, exchange: str, timeframe: str, min_rr: float) -> list[dict[str, Any]]:
    setups: list[dict[str, Any]] = []
    sec = timeframe_seconds(timeframe)
    for c in candles:
        recent = latest_confirmed_pivots(pivots, c.ts)
        if len(recent) < 4:
            continue
        state = structure_state(recent)
        lows = [p for p in recent if p["pivot_type"] == "LOW"]
        highs = [p for p in recent if p["pivot_type"] == "HIGH"]
        last_low = lows[-1] if lows else None
        last_high = highs[-1] if highs else None
        smc = smc_by_ts.get(c.ts - sec) or smc_by_ts.get(c.ts)  # prior closed candle preferred
        if smc is None:
            continue
        for direction in ("BUY", "SELL"):
            if direction == "BUY" and state not in {"BULLISH", "RANGE"}:
                continue
            if direction == "SELL" and state not in {"BEARISH", "RANGE"}:
                continue
            score = 0
            components: dict[str, Any] = {"trend_state": state}
            if direction == "BUY" and last_low and last_low.get("label") == "HL":
                score += 25; components["swing_anchor"] = "HL"
            if direction == "SELL" and last_high and last_high.get("label") == "LH":
                score += 25; components["swing_anchor"] = "LH"
            for field, pts in [("order_block", 20), ("order_flow_proxy", 15), ("price_action_confirm", 10), ("bos", 10), ("fvg", 5), ("choch", 5)]:
                if smc[field] == direction:
                    score += pts
                    components[field] = direction
            if smc["ema_trend"] == direction:
                score += 10; components["ema_trend"] = direction
            if score < 45:
                continue
            if direction == "BUY":
                anchor = float(last_low["price"] if last_low else c.low)
                entry_low = min(c.close, c.low)
                entry_high = max(c.close, c.open)
                sl = min(anchor, c.low) - 0.5
                risk = max(0.01, entry_high - sl)
                tp1 = entry_high + risk * 1.5
                tp2 = entry_high + risk * 2.2
                rr = abs(tp1 - entry_high) / risk
            else:
                anchor = float(last_high["price"] if last_high else c.high)
                entry_low = min(c.close, c.open)
                entry_high = max(c.close, c.high)
                sl = max(anchor, c.high) + 0.5
                risk = max(0.01, sl - entry_low)
                tp1 = entry_low - risk * 1.5
                tp2 = entry_low - risk * 2.2
                rr = abs(entry_low - tp1) / risk
            if rr < min_rr:
                continue
            setups.append({
                "symbol": symbol.upper(), "exchange": exchange.upper(), "timeframe": timeframe,
                "ts": c.ts, "datetime_utc": c.datetime_utc, "direction": direction,
                "setup_type": "swing/HL_OB_FLOW" if direction == "BUY" else "swing/LH_OB_FLOW",
                "trend_state": state, "trigger_price": c.close, "entry_low": min(entry_low, entry_high),
                "entry_high": max(entry_low, entry_high), "sl": sl, "tp1": tp1, "tp2": tp2,
                "rr": rr, "score": min(100, score), "components_json": json.dumps(components, ensure_ascii=False, sort_keys=True), "created_at": utc_now(),
            })
    return setups


def store_setups(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    cols = list(rows[0].keys())
    sql = f"INSERT INTO historical_swing_setups ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)}) ON CONFLICT(symbol,exchange,timeframe,ts,direction,setup_type) DO UPDATE SET " + ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"symbol","exchange","timeframe","ts","direction","setup_type"})
    con.executemany(sql, [[r[c] for c in cols] for r in rows])
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--left", type=int, default=3)
    p.add_argument("--right", type=int, default=3)
    p.add_argument("--min-move", type=float, default=4.0)
    p.add_argument("--min-rr", type=float, default=1.2)
    p.add_argument("--limit", type=int)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)
    with sqlite3.connect(Path(args.db_path).expanduser()) as con:
        con.row_factory = sqlite3.Row
        ensure_schema(con)
        candles = load_candles(con, args.symbol, args.exchange, args.timeframe, args.limit)
        pivots = detect_pivots(candles, args.left, args.right, args.min_move)
        stored_pivots = store_pivots(con, pivots, args.symbol, args.exchange, args.timeframe)
        smc_by_ts = load_smc_by_ts(con, args.symbol, args.exchange, args.timeframe)
        setups = build_setups(candles, pivots, smc_by_ts, args.symbol, args.exchange, args.timeframe, args.min_rr)
        stored_setups = store_setups(con, setups)
        con.commit()
    summary = {
        "symbol": args.symbol.upper(), "exchange": args.exchange.upper(), "timeframe": args.timeframe,
        "candles": len(candles), "pivots": len(pivots), "setups": len(setups),
        "pivots_stored": stored_pivots, "setups_stored": stored_setups,
        "setup_by_direction": {"BUY": sum(1 for s in setups if s["direction"] == "BUY"), "SELL": sum(1 for s in setups if s["direction"] == "SELL")},
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Swing pivots={len(pivots)} setups={len(setups)} stored={stored_pivots}/{stored_setups}")
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
