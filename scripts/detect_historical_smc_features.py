#!/usr/bin/env python3
"""Detect historical SMC-style features from stored candles.

This is an evidence/shadow tool: it writes derived feature rows to
`historical_smc_features` but does not modify production entry/order logic.
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


def ema(values: list[float], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    if len(values) < period:
        return out
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        out[i] = prev
    return out


def atr(candles: list[Candle], period: int = 14) -> list[float | None]:
    tr: list[float] = []
    for i, c in enumerate(candles):
        if i == 0:
            tr.append(c.high - c.low)
        else:
            prev_close = candles[i - 1].close
            tr.append(max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close)))
    out: list[float | None] = [None] * len(candles)
    if len(tr) < period:
        return out
    val = sum(tr[:period]) / period
    out[period - 1] = val
    for i in range(period, len(tr)):
        val = (val * (period - 1) + tr[i]) / period
        out[i] = val
    return out


def rolling_avg(values: list[float | None], period: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    window: list[float] = []
    for i, v in enumerate(values):
        if v is not None:
            window.append(float(v))
        if len(window) > period:
            window.pop(0)
        if len(window) >= max(3, period // 2):
            out[i] = sum(window) / len(window)
    return out


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


def load_candles(con: sqlite3.Connection, symbol: str, exchange: str, timeframe: str, limit: int | None) -> list[Candle]:
    sql = """
        SELECT ts, datetime_utc, open, high, low, close, volume
        FROM historical_candles
        WHERE UPPER(symbol)=UPPER(?) AND UPPER(exchange)=UPPER(?) AND timeframe=?
        ORDER BY ts ASC
    """
    params: list[Any] = [symbol, exchange, timeframe]
    if limit:
        sql = "SELECT * FROM (" + sql + " LIMIT ?) ORDER BY ts ASC"
        params.append(limit)
    rows = con.execute(sql, params).fetchall()
    return [Candle(int(r["ts"]), str(r["datetime_utc"]), float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]), None if r["volume"] is None else float(r["volume"])) for r in rows]


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_smc_features (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          exchange TEXT NOT NULL,
          timeframe TEXT NOT NULL,
          ts INTEGER NOT NULL,
          datetime_utc TEXT NOT NULL,
          session_label TEXT,
          ema_trend TEXT,
          liquidity_sweep TEXT,
          liquidity_level REAL,
          choch TEXT,
          bos TEXT,
          bos_level REAL,
          fvg TEXT,
          fvg_low REAL,
          fvg_high REAL,
          order_block TEXT,
          order_block_low REAL,
          order_block_high REAL,
          price_action_confirm TEXT,
          order_flow_proxy TEXT,
          volume_ratio REAL,
          feature_score_buy INTEGER NOT NULL DEFAULT 0,
          feature_score_sell INTEGER NOT NULL DEFAULT 0,
          features_json TEXT,
          created_at TEXT NOT NULL,
          UNIQUE(symbol, exchange, timeframe, ts)
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_historical_smc_features_lookup ON historical_smc_features(symbol, exchange, timeframe, ts)")


def detect_features(candles: list[Candle], symbol: str, exchange: str, timeframe: str) -> list[dict[str, Any]]:
    closes = [c.close for c in candles]
    vols = [c.volume for c in candles]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    atr14 = atr(candles, 14)
    avg_vol = rolling_avg(vols, 20)
    rows: list[dict[str, Any]] = []
    last_structure = "RANGE"
    lookback = 20
    for i, c in enumerate(candles):
        if i < max(50, lookback + 3):
            continue
        prev = candles[i - 1]
        prev2 = candles[i - 2]
        prior = candles[max(0, i - lookback):i]
        prior_high = max(x.high for x in prior)
        prior_low = min(x.low for x in prior)
        atr_i = atr14[i] or max(0.01, c.high - c.low)
        body = abs(c.close - c.open)
        rng = max(0.01, c.high - c.low)
        upper_wick = c.high - max(c.open, c.close)
        lower_wick = min(c.open, c.close) - c.low
        buy_score = 0
        sell_score = 0

        ema_trend = "RANGE"
        ema20_i = ema20[i]
        ema50_i = ema50[i]
        if ema20_i is not None and ema50_i is not None:
            if ema20_i > ema50_i:
                ema_trend = "BUY"
                buy_score += 1
            elif ema20_i < ema50_i:
                ema_trend = "SELL"
                sell_score += 1

        liquidity_sweep = None
        liquidity_level = None
        if c.low < prior_low and c.close > prior_low:
            liquidity_sweep = "BUY"
            liquidity_level = prior_low
            buy_score += 1
        elif c.high > prior_high and c.close < prior_high:
            liquidity_sweep = "SELL"
            liquidity_level = prior_high
            sell_score += 1

        bos = None
        bos_level = None
        if c.close > prior_high:
            bos = "BUY"
            bos_level = prior_high
            buy_score += 1
        elif c.close < prior_low:
            bos = "SELL"
            bos_level = prior_low
            sell_score += 1

        choch = None
        if bos == "BUY" and last_structure == "SELL":
            choch = "BUY"
            buy_score += 1
        elif bos == "SELL" and last_structure == "BUY":
            choch = "SELL"
            sell_score += 1
        if bos in {"BUY", "SELL"}:
            last_structure = bos

        fvg = None
        fvg_low = None
        fvg_high = None
        # 3-candle imbalance: bullish gap between candle i-2 high and current low; bearish inverse.
        if c.low > prev2.high and body >= 0.35 * atr_i:
            fvg = "BUY"
            fvg_low = prev2.high
            fvg_high = c.low
            buy_score += 1
        elif c.high < prev2.low and body >= 0.35 * atr_i:
            fvg = "SELL"
            fvg_low = c.high
            fvg_high = prev2.low
            sell_score += 1

        order_block = None
        order_block_low = None
        order_block_high = None
        impulse = body >= 0.65 * atr_i
        if impulse and c.close > c.open and prev.close < prev.open:
            order_block = "BUY"
            order_block_low = prev.low
            order_block_high = prev.high
            buy_score += 1
        elif impulse and c.close < c.open and prev.close > prev.open:
            order_block = "SELL"
            order_block_low = prev.low
            order_block_high = prev.high
            sell_score += 1

        price_action = None
        bullish_engulf = c.close > c.open and prev.close < prev.open and c.close >= prev.open and c.open <= prev.close
        bearish_engulf = c.close < c.open and prev.close > prev.open and c.close <= prev.open and c.open >= prev.close
        if bullish_engulf or (lower_wick / rng >= 0.45 and c.close > c.open):
            price_action = "BUY"
            buy_score += 1
        elif bearish_engulf or (upper_wick / rng >= 0.45 and c.close < c.open):
            price_action = "SELL"
            sell_score += 1

        vol_avg = avg_vol[i]
        volume_ratio = None
        if c.volume is not None and vol_avg:
            volume_ratio = c.volume / max(1e-9, vol_avg)
        order_flow = None
        close_location = (c.close - c.low) / rng
        if volume_ratio is not None and volume_ratio >= 1.2:
            if c.close > c.open and close_location >= 0.6:
                order_flow = "BUY"
                buy_score += 1
            elif c.close < c.open and close_location <= 0.4:
                order_flow = "SELL"
                sell_score += 1

        features = {
            "prior_high": prior_high,
            "prior_low": prior_low,
            "atr14": atr_i,
            "body_ratio": body / rng,
            "upper_wick_pct": upper_wick / rng * 100,
            "lower_wick_pct": lower_wick / rng * 100,
            "close_location": close_location,
            "ema20": ema20[i],
            "ema50": ema50[i],
        }
        rows.append(
            {
                "symbol": symbol.upper(),
                "exchange": exchange.upper(),
                "timeframe": timeframe,
                "ts": c.ts,
                "datetime_utc": c.datetime_utc,
                "session_label": session_label(c.datetime_utc),
                "ema_trend": ema_trend,
                "liquidity_sweep": liquidity_sweep,
                "liquidity_level": liquidity_level,
                "choch": choch,
                "bos": bos,
                "bos_level": bos_level,
                "fvg": fvg,
                "fvg_low": fvg_low,
                "fvg_high": fvg_high,
                "order_block": order_block,
                "order_block_low": order_block_low,
                "order_block_high": order_block_high,
                "price_action_confirm": price_action,
                "order_flow_proxy": order_flow,
                "volume_ratio": volume_ratio,
                "feature_score_buy": buy_score,
                "feature_score_sell": sell_score,
                "features_json": json.dumps(features, ensure_ascii=False, separators=(",", ":")),
                "created_at": utc_now(),
            }
        )
    return rows


def store_features(con: sqlite3.Connection, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    cols = list(rows[0].keys())
    placeholders = ",".join("?" for _ in cols)
    updates = ",".join(f"{c}=excluded.{c}" for c in cols if c not in {"symbol", "exchange", "timeframe", "ts"})
    sql = f"INSERT INTO historical_smc_features ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(symbol,exchange,timeframe,ts) DO UPDATE SET {updates}"
    con.executemany(sql, [[row[c] for c in cols] for row in rows])
    return len(rows)


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"rows": len(rows)}
    fields = ["liquidity_sweep", "choch", "bos", "fvg", "order_block", "price_action_confirm", "order_flow_proxy"]
    for f in fields:
        out[f] = {
            "BUY": sum(1 for r in rows if r[f] == "BUY"),
            "SELL": sum(1 for r in rows if r[f] == "SELL"),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    db_path = Path(args.db_path).expanduser()
    with sqlite3.connect(db_path) as con:
        con.row_factory = sqlite3.Row
        ensure_schema(con)
        candles = load_candles(con, args.symbol, args.exchange, args.timeframe, args.limit)
        rows = detect_features(candles, args.symbol, args.exchange, args.timeframe)
        stored = store_features(con, rows)
        con.commit()
    result = {"db_path": str(db_path), "symbol": args.symbol.upper(), "exchange": args.exchange.upper(), "timeframe": args.timeframe, "candles": len(candles), "features_stored": stored, "summary": summarize(rows)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"SMC features stored={stored} candles={len(candles)} {args.exchange.upper()}:{args.symbol.upper()} {args.timeframe}")
        print(json.dumps(result["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
