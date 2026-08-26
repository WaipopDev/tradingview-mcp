#!/usr/bin/env python3
"""Track and evaluate XAUUSD trade-plan outcomes in the trading signals SQLite DB.

Creates a small sidecar table in the same DB. It can:
- add a manual Telegram trade plan (--add-plan)
- auto-track actionable rows from trade_signals when entry/sl/tp exist
- evaluate open plans against the latest collected price, marking TP/SL hits
- print a concise summary with --summary
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


SCHEMA = """
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


def ensure_management_columns(con: sqlite3.Connection) -> None:
    cols = {r[1] for r in con.execute("PRAGMA table_info(trade_plan_outcomes)")}
    additions = {
        "management_state": "TEXT",
        "managed_sl": "REAL",
        "protected_at": "TEXT",
        "partial_taken_at": "TEXT",
        "partial_price": "REAL",
        "partial_fraction": "REAL",
        "exit_reason": "TEXT",
        "order_score": "REAL",
        "setup_score": "REAL",
        "setup_type": "TEXT",
        "session_label": "TEXT",
        "order_metadata_json": "TEXT",
    }
    for name, ddl in additions.items():
        if name not in cols:
            con.execute(f"ALTER TABLE trade_plan_outcomes ADD COLUMN {name} {ddl}")


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    ensure_management_columns(con)
    return con


def latest_price(con: sqlite3.Connection, symbol: str, timeframe: str) -> tuple[float | None, str | None]:
    row = con.execute(
        """
        SELECT price, created_at FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()
    if row and row["price"] is not None:
        return float(row["price"]), row["created_at"]
    return None, None


def add_manual_plan(con: sqlite3.Connection, args: argparse.Namespace) -> int:
    created_at = args.created_at or utc_now()
    plan_key = args.plan_key or f"manual:{args.symbol.upper()}:{args.timeframe}:{args.direction.upper()}:{created_at}:{args.entry_low}-{args.entry_high}:{args.sl}:{args.tp1}:{args.tp2}:{args.tp3}"
    con.execute(
        """
        INSERT OR IGNORE INTO trade_plan_outcomes
        (source, plan_key, symbol, timeframe, direction, entry_low, entry_high, sl, tp1, tp2, tp3, note, created_at)
        VALUES ('telegram_manual', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            plan_key,
            args.symbol.upper(),
            args.timeframe,
            args.direction.upper(),
            min(args.entry_low, args.entry_high),
            max(args.entry_low, args.entry_high),
            args.sl,
            args.tp1,
            args.tp2,
            args.tp3,
            args.note,
            created_at,
        ),
    )
    row = con.execute("SELECT id FROM trade_plan_outcomes WHERE plan_key=?", (plan_key,)).fetchone()
    return int(row["id"])


def auto_track_trade_signals(con: sqlite3.Connection, symbol: str, timeframe: str) -> int:
    rows = con.execute(
        """
        SELECT id, symbol, timeframe, bias, entry_low, entry_high, sl, tp1, tp2, tp3, created_at
        FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND bias IN ('BUY','SELL')
          AND entry_low IS NOT NULL AND entry_high IS NOT NULL AND sl IS NOT NULL
        ORDER BY created_at DESC
        """,
        (symbol, timeframe),
    ).fetchall()
    added = 0
    for r in rows:
        plan_key = f"trade_signal:{r['id']}"
        cur = con.execute(
            """
            INSERT OR IGNORE INTO trade_plan_outcomes
            (source_signal_id, source, plan_key, symbol, timeframe, direction, entry_low, entry_high, sl, tp1, tp2, tp3, created_at)
            VALUES (?, 'trade_signal', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r["id"], plan_key, r["symbol"], r["timeframe"], r["bias"],
                min(float(r["entry_low"]), float(r["entry_high"])),
                max(float(r["entry_low"]), float(r["entry_high"])),
                r["sl"], r["tp1"], r["tp2"], r["tp3"], r["created_at"],
            ),
        )
        added += cur.rowcount
    return added


def favorable_points(direction: str, entry: float, price: float) -> float:
    return price - entry if direction == "BUY" else entry - price


def adverse_points(direction: str, entry: float, price: float) -> float:
    return entry - price if direction == "BUY" else price - entry


def evaluate_open(con: sqlite3.Connection, symbol: str, timeframe: str) -> list[dict]:
    price, price_time = latest_price(con, symbol, timeframe)
    if price is None:
        return []
    updates: list[dict] = []
    rows = con.execute(
        """
        SELECT * FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status IN ('pending','entered')
        ORDER BY created_at ASC, id ASC
        """,
        (symbol, timeframe),
    ).fetchall()
    now = utc_now()
    for r in rows:
        direction = str(r["direction"])
        entry_low = float(r["entry_low"])
        entry_high = float(r["entry_high"])
        status = str(r["status"])
        entry_price = r["entry_price"]
        entered_at = r["entered_at"]
        result = None
        closed_at = None

        if status == "pending":
            in_zone = entry_low <= price <= entry_high
            source = str(r["source"] or "") if "source" in r.keys() else ""
            is_trigger_order = "scalp_watch" in source
            crossed_trigger = is_trigger_order and (
                (direction == "BUY" and price > entry_high)
                or (direction == "SELL" and price < entry_low)
            )
            if is_trigger_order and (in_zone or crossed_trigger):
                status = "entered"
                entry_price = price if in_zone else (entry_high if direction == "BUY" else entry_low)
                entered_at = price_time or now

        if status == "entered" and entry_price is not None:
            entry = float(entry_price)
            tps = [r["tp1"], r["tp2"], r["tp3"]]
            hit_tp = None
            for idx, tp in enumerate(tps, start=1):
                if tp is None:
                    continue
                tp = float(tp)
                if (direction == "BUY" and price >= tp) or (direction == "SELL" and price <= tp):
                    hit_tp = idx
            managed_sl = r["managed_sl"] if "managed_sl" in r.keys() else None
            effective_sl = float(managed_sl) if managed_sl is not None else float(r["sl"])
            hit_sl = (direction == "BUY" and price <= effective_sl) or (direction == "SELL" and price >= effective_sl)
            if hit_sl:
                status = "closed"
                partial_taken = ("partial_taken_at" in r.keys()) and r["partial_taken_at"] is not None
                if managed_sl is not None and abs(effective_sl - entry) <= 0.05:
                    result = "PARTIAL_BE" if partial_taken else "BE"
                elif managed_sl is not None:
                    result = "TRAIL_SL"
                else:
                    result = "SL"
                closed_at = price_time or now
            elif hit_tp is not None:
                status = "closed"
                result = f"TP{hit_tp}"
                closed_at = price_time or now
            max_fav = max(float(r["max_favorable"] or 0), favorable_points(direction, entry, price))
            max_adv = max(float(r["max_adverse"] or 0), adverse_points(direction, entry, price))
        else:
            max_fav = float(r["max_favorable"] or 0)
            max_adv = float(r["max_adverse"] or 0)

        con.execute(
            """
            UPDATE trade_plan_outcomes
            SET status=?, result=COALESCE(?, result), entry_price=COALESCE(?, entry_price),
                entered_at=COALESCE(?, entered_at), closed_at=COALESCE(?, closed_at),
                current_price=?, max_favorable=?, max_adverse=?, last_checked_at=?
            WHERE id=?
            """,
            (status, result, entry_price, entered_at, closed_at, price, max_fav, max_adv, now, r["id"]),
        )
        updates.append({"id": r["id"], "direction": direction, "status": status, "result": result or r["result"], "price": price})
    return updates


def summary(con: sqlite3.Connection, symbol: str, timeframe: str, limit: int = 10) -> str:
    rows = con.execute(
        """
        SELECT * FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT ?
        """,
        (symbol, timeframe, limit),
    ).fetchall()
    closed = con.execute(
        """
        SELECT COUNT(*) total,
               SUM(CASE WHEN result LIKE 'TP%' OR result='PARTIAL_BE' THEN 1 ELSE 0 END) wins,
               SUM(CASE WHEN result IN ('SL','CUT') THEN 1 ELSE 0 END) losses
        FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status='closed'
          AND entry_price IS NOT NULL AND entered_at IS NOT NULL
        """,
        (symbol, timeframe),
    ).fetchone()
    total = int(closed["total"] or 0)
    wins = int(closed["wins"] or 0)
    losses = int(closed["losses"] or 0)
    wr = (wins / total * 100) if total else 0
    out = [f"closed={total} wins={wins} losses={losses} win_rate={wr:.1f}%"]
    for r in rows:
        out.append(
            f"#{r['id']} {r['direction']} {r['entry_low']:g}-{r['entry_high']:g} SL {r['sl']:g} "
            f"TP {r['tp1'] or '-'} / {r['tp2'] or '-'} / {r['tp3'] or '-'} | "
            f"status={r['status']} result={r['result'] or '-'} current={r['current_price'] or '-'} "
            f"MFE={float(r['max_favorable'] or 0):.2f} MAE={float(r['max_adverse'] or 0):.2f} note={r['note'] or ''}"
        )
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--auto-track", action="store_true")
    p.add_argument("--evaluate", action="store_true")
    p.add_argument("--summary", action="store_true")
    p.add_argument("--add-plan", action="store_true")
    p.add_argument("--direction", choices=["BUY", "SELL", "buy", "sell"])
    p.add_argument("--entry-low", type=float)
    p.add_argument("--entry-high", type=float)
    p.add_argument("--sl", type=float)
    p.add_argument("--tp1", type=float)
    p.add_argument("--tp2", type=float)
    p.add_argument("--tp3", type=float)
    p.add_argument("--note", default="")
    p.add_argument("--plan-key")
    p.add_argument("--created-at")
    args = p.parse_args(argv)

    db = Path(args.db_path).expanduser()
    with connect(db) as con:
        if args.add_plan:
            required = [args.direction, args.entry_low, args.entry_high, args.sl]
            if any(v is None for v in required):
                p.error("--add-plan requires --direction --entry-low --entry-high --sl")
            plan_id = add_manual_plan(con, args)
            print(f"added_plan_id={plan_id}")
        if args.auto_track:
            added = auto_track_trade_signals(con, args.symbol, args.timeframe)
            if args.summary:
                print(f"auto_tracked={added}")
        if args.evaluate:
            updates = evaluate_open(con, args.symbol, args.timeframe)
            if args.summary:
                print(f"evaluated={len(updates)}")
        if args.summary:
            print(summary(con, args.symbol, args.timeframe))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
