#!/usr/bin/env python3
"""Send deterministic XAUUSD entry-zone orders to Telegram from latest DB signal.

Each sent BUY/SELL setup is inserted into trade_plan_outcomes first, so it has
an Order # and can later be evaluated/announced when TP or SL is hit.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


ENTRY_SCHEMA = """
CREATE TABLE IF NOT EXISTS telegram_entry_alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  target TEXT NOT NULL,
  source_signal_id INTEGER,
  outcome_id INTEGER,
  delivered_at TEXT NOT NULL,
  UNIQUE(symbol, timeframe, fingerprint, target)
);
"""

OUTCOME_SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_plan_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_signal_id INTEGER,
  source TEXT NOT NULL DEFAULT 'manual',
  plan_key TEXT UNIQUE,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL DEFAULT '15m',
  direction TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
  entry_low REAL NOT NULL,
  entry_high REAL NOT NULL,
  sl REAL NOT NULL,
  tp1 REAL,
  tp2 REAL,
  tp3 REAL,
  status TEXT NOT NULL DEFAULT 'pending',
  result TEXT,
  entry_price REAL,
  entered_at TEXT,
  closed_at TEXT,
  current_price REAL,
  max_favorable REAL DEFAULT 0,
  max_adverse REAL DEFAULT 0,
  note TEXT,
  created_at TEXT NOT NULL,
  last_checked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_trade_plan_outcomes_status ON trade_plan_outcomes(symbol, status, created_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(ENTRY_SCHEMA)
    con.executescript(OUTCOME_SCHEMA)
    # Add columns for older DBs.
    cols = {r[1] for r in con.execute("PRAGMA table_info(telegram_entry_alerts)").fetchall()}
    if "outcome_id" not in cols:
        con.execute("ALTER TABLE telegram_entry_alerts ADD COLUMN outcome_id INTEGER")
    return con


def parse_json(v: Any, default: Any) -> Any:
    if not v:
        return default
    try:
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return default


def latest_signal(con: sqlite3.Connection, symbol: str, timeframe: str) -> sqlite3.Row | None:
    return con.execute(
        """
        SELECT * FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()


def fmt(n: float | None) -> str:
    return "-" if n is None else f"{float(n):.1f}".rstrip("0").rstrip(".")


# XAUUSD point convention here: 100 points = 1.00 price unit.
# User wants SL not beyond 500–800 points, so cap SL distance at 8.00.
MIN_SL_POINTS = 500
MAX_SL_POINTS = 800
POINTS_PER_PRICE_UNIT = 100
MIN_SL_DISTANCE = MIN_SL_POINTS / POINTS_PER_PRICE_UNIT
MAX_SL_DISTANCE = MAX_SL_POINTS / POINTS_PER_PRICE_UNIT


def clamp_sl(direction: str, entry_low: float, entry_high: float, sl: float) -> float:
    """Keep SL distance in the requested 500–800 point band from worst-case fill."""
    if direction == "BUY":
        # Worst BUY fill is the top of the entry zone.
        distance = entry_high - sl
        distance = max(MIN_SL_DISTANCE, min(MAX_SL_DISTANCE, distance))
        return entry_high - distance
    # Worst SELL fill is the bottom of the entry zone.
    distance = sl - entry_low
    distance = max(MIN_SL_DISTANCE, min(MAX_SL_DISTANCE, distance))
    return entry_low + distance


def derive_order(row: sqlite3.Row) -> tuple[dict[str, Any], str]:
    price = float(row["price"])
    sd = parse_json(row["sd_range_json"], {})
    tech = parse_json(row["technical_json"], {})
    sr = tech.get("support_resistance") or {}
    ema = tech.get("ema") if isinstance(tech.get("ema"), dict) else {}
    market_structure = tech.get("market_structure") or {}
    sentiment = tech.get("market_sentiment") or {}
    rsi = tech.get("rsi") or {}
    macd = tech.get("macd") or {}

    sd1_low = float(sd.get("sd1_low") or price - 5)
    sd1_high = float(sd.get("sd1_high") or price + 5)
    sd2_low = float(sd.get("sd2_low") or price - 10)
    sd2_high = float(sd.get("sd2_high") or price + 10)
    pivot = float(sr.get("pivot") or price)
    ema20 = float(ema.get("ema20") or pivot)
    rsi_val = rsi.get("value")

    trend = str(market_structure.get("trend") or "Neutral")
    momentum = str(sentiment.get("momentum") or "Neutral")
    macd_cross = str(macd.get("crossover") or "")
    bearish = price < ema20 and ("Bear" in trend or "Bear" in momentum or "Bear" in macd_cross)
    bullish = price > ema20 and ("Bull" in trend or "Bull" in momentum or "Bull" in macd_cross)

    if bearish:
        direction = "SELL"
        bias = "SELL มากกว่า / BUY เป็นเด้งสั้น"
        entry_low = min(max(price + 1.0, pivot), max(ema20, pivot))
        entry_high = max(ema20, pivot, price + 2.5)
        sl = entry_high + 5.0
        tp1, tp2, tp3 = sd1_low, sd2_low, None
        invalidation = f"ถ้ายืนเหนือ {fmt(entry_high)} ได้ ลด/งด SELL"
    elif bullish:
        direction = "BUY"
        bias = "BUY มากกว่า"
        entry_low = min(max(sd1_low, price - 3.0), price)
        entry_high = max(min(price + 0.8, sd1_high), entry_low)
        sl = entry_low - 5.0
        tp1, tp2, tp3 = sd1_high, sd2_high, None
        invalidation = f"ถ้าหลุด {fmt(entry_low)} ระวังกลับลง {fmt(sd1_low)} / {fmt(sd2_low)}"
    else:
        # If unclear, still produce a conservative range-reversion order in the nearer direction.
        if price >= pivot:
            direction = "SELL"
            bias = "WAIT / กลางกรอบ แต่ใกล้โซนขาย"
            entry_low, entry_high = pivot, sd1_high
            sl = sd2_high
            tp1, tp2, tp3 = sd1_low, sd2_low, None
            invalidation = f"ถ้ายืนเหนือ {fmt(sd1_high)} ได้ งด SELL"
        else:
            direction = "BUY"
            bias = "WAIT / กลางกรอบ แต่ใกล้โซนรับ"
            entry_low, entry_high = sd1_low, pivot
            sl = sd2_low - 4.0
            tp1, tp2, tp3 = price, sd1_high, None
            invalidation = f"ถ้าหลุด {fmt(sd1_low)} งด BUY"

    entry_low = min(entry_low, entry_high)
    entry_high = max(entry_low, entry_high)
    sl = clamp_sl(direction, entry_low, entry_high, sl)

    # Simple setup score: trend alignment + RSI quality + risk/reward.
    rr = abs((tp1 or price) - entry_high) / max(0.01, abs(entry_low - sl))
    score = 50
    if bullish and direction == "BUY" or bearish and direction == "SELL":
        score += 20
    if rsi_val is not None:
        rv = float(rsi_val)
        if direction == "BUY" and 45 <= rv <= 66:
            score += 15
        elif direction == "SELL" and 34 <= rv <= 55:
            score += 15
        elif (direction == "BUY" and rv >= 70) or (direction == "SELL" and rv <= 30):
            score -= 20
    if rr >= 1.5:
        score += 15
    elif rr < 1.0:
        score -= 15
    score = max(0, min(100, int(round(score))))

    order = {
        "symbol": row["symbol"],
        "timeframe": row["timeframe"],
        "source_signal_id": row["id"],
        "price": price,
        "raw_bias": row["bias"],
        "decision": row["decision"],
        "bias": bias,
        "direction": direction,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "rsi": rsi_val,
        "ema20": ema20,
        "score": score,
        "rr": rr,
        "invalidation": invalidation,
    }
    fp = (
        f"{row['symbol']}:{row['timeframe']}:{round(price)}:{direction}:"
        f"{round(order['entry_low'])}:{round(order['entry_high'])}:"
        f"{round(sl)}:{round(tp1 or 0)}:{round(tp2 or 0)}"
    )
    return order, fp


def already_sent(con: sqlite3.Connection, symbol: str, timeframe: str, fp: str, target: str) -> bool:
    return con.execute(
        "SELECT 1 FROM telegram_entry_alerts WHERE symbol=? AND timeframe=? AND fingerprint=? AND target=? LIMIT 1",
        (symbol, timeframe, fp, target),
    ).fetchone() is not None


def confirmation_skip_reason(order: dict[str, Any]) -> str | None:
    """Do not trade WAIT_CONFIRMATION unless price has confirmed beyond the zone."""
    raw_bias = str(order.get("raw_bias") or "")
    decision = str(order.get("decision") or "")
    if raw_bias != "WAIT" and decision == "TRADE":
        return None
    price = float(order["price"])
    if order["direction"] == "BUY":
        confirmed = price > float(order["entry_high"])
        level = order["entry_high"]
        side = "เหนือ"
    else:
        confirmed = price < float(order["entry_low"])
        level = order["entry_low"]
        side = "ต่ำกว่า"
    if confirmed and int(order.get("score") or 0) >= 85:
        return None
    return (
        f"งดส่ง {order['direction']}: signal ยังเป็น {decision or raw_bias}; "
        f"รอราคา confirm {side} {fmt(level)} และ score >=85"
    )


def recent_similar_zone_reason(con: sqlite3.Connection, order: dict[str, Any]) -> str | None:
    """Avoid repeated same-direction zones for 45 minutes unless a strong confirmed trade appears."""
    rows = con.execute(
        """
        SELECT id, direction, entry_low, entry_high, status, result, created_at, closed_at
        FROM trade_plan_outcomes
        WHERE symbol=? AND timeframe=? AND direction=?
        ORDER BY id DESC LIMIT 16
        """,
        (order["symbol"], order["timeframe"], order["direction"]),
    ).fetchall()
    now = datetime.now(timezone.utc)
    new_low = float(order["entry_low"])
    new_high = float(order["entry_high"])
    new_center = (new_low + new_high) / 2
    new_band = int(new_center // 5)
    strong_fresh_confirmation = (
        str(order.get("decision") or "") == "TRADE"
        and int(order.get("score") or 0) >= 85
        and str(order.get("raw_bias") or "") != "WAIT"
    )
    if strong_fresh_confirmation:
        return None
    for row in rows:
        raw_time = row["closed_at"] or row["created_at"]
        try:
            t = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if (now - t).total_seconds() > 45 * 60:
            continue
        old_low = float(row["entry_low"])
        old_high = float(row["entry_high"])
        old_center = (old_low + old_high) / 2
        old_band = int(old_center // 5)
        center_distance = abs(old_center - new_center)
        overlap = max(0.0, min(old_high, new_high) - max(old_low, new_low))
        width = max(0.01, new_high - new_low)
        same_5usd_band = old_band == new_band or abs(old_center - new_center) <= 5.0
        if center_distance <= 3.0 or overlap / width >= 0.35 or same_5usd_band:
            return f"งดส่งซ้ำ: โซนใกล้ Order #{row['id']} ใน 45 นาทีล่าสุด ({fmt(old_low)}–{fmt(old_high)})"
    return None


def open_duplicate_reason(con: sqlite3.Connection, order: dict[str, Any]) -> str | None:
    """Do not stack repeated orders in the same direction while one is active."""
    row = con.execute(
        """
        SELECT id, direction, entry_low, entry_high, sl, tp1, tp2, status, result, created_at
        FROM trade_plan_outcomes
        WHERE symbol=? AND timeframe=? AND direction=? AND status IN ('pending','entered')
        ORDER BY id DESC LIMIT 1
        """,
        (order["symbol"], order["timeframe"], order["direction"]),
    ).fetchone()
    if row is None:
        return None

    existing_low = float(row["entry_low"])
    existing_high = float(row["entry_high"])
    new_low = float(order["entry_low"])
    new_high = float(order["entry_high"])
    overlap = max(0.0, min(existing_high, new_high) - max(existing_low, new_low))
    new_width = max(0.01, new_high - new_low)
    center_distance = abs(((existing_low + existing_high) / 2) - ((new_low + new_high) / 2))
    similar_zone = overlap / new_width >= 0.25 or center_distance <= 10.0
    if similar_zone:
        return (
            f"งดส่งซ้ำ: ยังมี Order #{row['id']} {row['direction']} เปิดอยู่ "
            f"โซน {fmt(existing_low)}–{fmt(existing_high)}; รอ TP/SL ก่อน"
        )
    return None


def adaptive_skip_reason(con: sqlite3.Connection, order: dict[str, Any]) -> str | None:
    """Use recent closed order performance to avoid repeating losing logic."""
    rows = con.execute(
        """
        SELECT result, max_favorable, max_adverse, current_price, created_at, closed_at
        FROM trade_plan_outcomes
        WHERE symbol=? AND timeframe=? AND direction=? AND status='closed'
        ORDER BY closed_at DESC, id DESC LIMIT 8
        """,
        (order["symbol"], order["timeframe"], order["direction"]),
    ).fetchall()
    if not rows:
        return None
    losses = sum(1 for r in rows if str(r["result"]) in {"SL", "CUT"})
    wins = sum(1 for r in rows if str(r["result"] or "").startswith("TP"))
    recent3_losses = len(rows) >= 3 and all(str(r["result"]) in {"SL", "CUT"} for r in rows[:3])
    win_rate = wins / len(rows) * 100
    rsi = order.get("rsi")
    rsi_hot = rsi is not None and float(rsi) >= 68 and order["direction"] == "BUY"
    rsi_cold = rsi is not None and float(rsi) <= 32 and order["direction"] == "SELL"

    if recent3_losses:
        last_closed_raw = rows[0]["closed_at"]
        try:
            last_closed = datetime.fromisoformat(str(last_closed_raw).replace("Z", "+00:00"))
            if last_closed.tzinfo is None:
                last_closed = last_closed.replace(tzinfo=timezone.utc)
            minutes_since = (datetime.now(timezone.utc) - last_closed).total_seconds() / 60
        except Exception:
            minutes_since = 0
        if minutes_since < 90:
            return f"งดส่ง {order['direction']} ชั่วคราว: 3 order ล่าสุดแพ้ต่อเนื่อง รอ cooldown อีก {max(1, int(90-minutes_since))} นาที"
        if str(order.get("decision") or "") != "TRADE" or int(order.get("score") or 0) < 85:
            return f"งดส่ง {order['direction']}: หลังแพ้ 3 ไม้ ต้องรอ TRADE confirmation และ score >=85 ตอนนี้ {int(order.get('score') or 0)}/100"
    recent_90_losses = 0
    for r in rows:
        try:
            closed = datetime.fromisoformat(str(r["closed_at"]).replace("Z", "+00:00"))
            if closed.tzinfo is None:
                closed = closed.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if (datetime.now(timezone.utc) - closed).total_seconds() <= 90 * 60 and str(r["result"]) in {"SL", "CUT"}:
            recent_90_losses += 1
    if recent_90_losses >= 3 and (str(order.get("decision") or "") != "TRADE" or int(order.get("score") or 0) < 85):
        return f"งดส่ง {order['direction']}: มี SL/CUT ฝั่งเดียวกัน {recent_90_losses} ไม้ใน 90 นาที ต้องรอ TRADE confirmation และ score >=85"
    if len(rows) >= 5 and losses >= 3 and win_rate < 45 and int(order.get("score") or 0) < 70:
        return f"งดส่ง {order['direction']} ชั่วคราว: ผลย้อนหลัง {wins}/{len(rows)} win ({win_rate:.1f}%) ต่ำกว่าเกณฑ์ และ score ยังไม่ถึง 70"
    if rsi_hot:
        return f"งดส่ง BUY: RSI {fmt(rsi)} สูงเกินไป เสี่ยงไล่ซื้อปลายรอบ"
    if rsi_cold:
        return f"งดส่ง SELL: RSI {fmt(rsi)} ต่ำเกินไป เสี่ยงขายปลายรอบ"
    return None


def ensure_outcome(con: sqlite3.Connection, order: dict[str, Any], fp: str) -> int:
    plan_key = f"entry_alert:{fp}"
    con.execute(
        """
        INSERT OR IGNORE INTO trade_plan_outcomes
        (source_signal_id, source, plan_key, symbol, timeframe, direction, entry_low, entry_high, sl, tp1, tp2, tp3, note, created_at)
        VALUES (?, 'telegram_entry_alert', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order["source_signal_id"],
            plan_key,
            order["symbol"],
            order["timeframe"],
            order["direction"],
            order["entry_low"],
            order["entry_high"],
            order["sl"],
            order["tp1"],
            order["tp2"],
            order["tp3"],
            f"Auto Telegram entry alert at price {fmt(order['price'])}",
            utc_now(),
        ),
    )
    row = con.execute("SELECT id FROM trade_plan_outcomes WHERE plan_key=?", (plan_key,)).fetchone()
    return int(row["id"])


def message_for_order(order: dict[str, Any], outcome_id: int) -> str:
    tps = " / ".join(fmt(x) for x in [order.get("tp1"), order.get("tp2"), order.get("tp3")] if x is not None)
    return "\n".join([
        f"Order #{outcome_id} | XAUUSD {fmt(order['price'])}",
        f"Bias: {order['bias']}",
        f"Score: {int(order.get('score') or 0)}/100 | RR≈{float(order.get('rr') or 0):.2f}",
        "",
        f"{order['direction']} zone: {fmt(order['entry_low'])}–{fmt(order['entry_high'])}",
        f"SL: {fmt(order['sl'])}",
        f"TP: {tps}",
        "",
        str(order["invalidation"]),
        "",
        f"RSI: {fmt(order.get('rsi'))} | EMA20: {fmt(order.get('ema20'))}",
    ])


def mark_sent(con: sqlite3.Connection, order: dict[str, Any], fp: str, target: str, outcome_id: int) -> None:
    con.execute(
        """
        INSERT OR IGNORE INTO telegram_entry_alerts
        (symbol, timeframe, fingerprint, target, source_signal_id, outcome_id, delivered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (order["symbol"], order["timeframe"], fp, target, order["source_signal_id"], outcome_id, utc_now()),
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET") or "telegram:8237892676")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    with connect(Path(args.db_path).expanduser()) as con:
        row = latest_signal(con, args.symbol, args.timeframe)
        if row is None or row["price"] is None:
            return 0
        order, fp = derive_order(row)
        skip_reason = (
            open_duplicate_reason(con, order)
            or recent_similar_zone_reason(con, order)
            or confirmation_skip_reason(order)
            or adaptive_skip_reason(con, order)
        )
        if skip_reason:
            if args.dry_run:
                print(skip_reason)
            return 0
        if not args.force and already_sent(con, order["symbol"], order["timeframe"], fp, args.target):
            return 0
        if args.dry_run:
            preview_id = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM trade_plan_outcomes").fetchone()[0]
            print(message_for_order(order, int(preview_id)))
            return 0
        outcome_id = ensure_outcome(con, order, fp)
        message = message_for_order(order, outcome_id)
        sent = subprocess.run(
            ["hermes", "send", "--quiet", "--to", args.target, "--subject", f"XAUUSD Order #{outcome_id}", message],
            text=True,
            capture_output=True,
            check=False,
        )
        if sent.returncode != 0:
            print(sent.stderr.strip() or sent.stdout.strip(), flush=True)
            return sent.returncode
        mark_sent(con, order, fp, args.target, outcome_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
