#!/usr/bin/env python3
"""Script-only MGT material-event detector for Waipop's trad system.

Runs without an LLM. Prints nothing for routine/no-risk states. Any non-empty
stdout is delivered by Hermes cron, so keep output concise Thai.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"
DEFAULT_STATE = Path.home() / ".hermes" / "cron" / "state" / "trad_mgt_material_detector.json"
URGENT_STATES = {"CUT_NOW", "MOVE_SL_BE", "TAKE_PARTIAL", "PROTECT"}
LOSS_RESULTS = {"SL", "CUT"}
WIN_RESULTS = {"TP1", "TP2", "TP3", "PARTIAL_BE", "TRAIL_SL"}


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def age_seconds(value: Any) -> int | None:
    dt = parse_dt(value)
    if not dt:
        return None
    return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))


def load_state(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def rowdict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return None if row is None else {k: row[k] for k in row.keys()}


def fmt_price(v: Any) -> str:
    try:
        return f"{float(v):.2f}"
    except Exception:
        return "-"


def latest_signal(con: sqlite3.Connection, symbol: str, timeframe: str) -> dict[str, Any] | None:
    if not table_exists(con, "trade_signals"):
        return None
    return rowdict(con.execute(
        """
        select id,symbol,timeframe,price,bias,decision,total_score,created_at
        from trade_signals
        where upper(symbol)=upper(?) and timeframe=?
        order by id desc limit 1
        """,
        (symbol, timeframe),
    ).fetchone())


def open_orders(con: sqlite3.Connection, symbol: str, timeframe: str) -> list[dict[str, Any]]:
    if not table_exists(con, "trade_plan_outcomes"):
        return []
    return [rowdict(r) for r in con.execute(
        """
        select * from trade_plan_outcomes
        where upper(symbol)=upper(?) and timeframe=? and status in ('pending','entered')
        order by id asc
        """,
        (symbol, timeframe),
    ).fetchall()]


def recent_closed(con: sqlite3.Connection, symbol: str, timeframe: str, after_id: int) -> list[dict[str, Any]]:
    if not table_exists(con, "trade_plan_outcomes"):
        return []
    return [rowdict(r) for r in con.execute(
        """
        select * from trade_plan_outcomes
        where upper(symbol)=upper(?) and timeframe=? and status='closed' and id>?
        order by id asc
        """,
        (symbol, timeframe, after_id),
    ).fetchall()]


def last_closed_id(con: sqlite3.Connection, symbol: str, timeframe: str) -> int:
    if not table_exists(con, "trade_plan_outcomes"):
        return 0
    row = con.execute(
        "select coalesce(max(id),0) from trade_plan_outcomes where upper(symbol)=upper(?) and timeframe=? and status='closed'",
        (symbol, timeframe),
    ).fetchone()
    return int(row[0] or 0)


def recent_loss_streak(con: sqlite3.Connection, symbol: str, timeframe: str, limit: int = 5) -> tuple[int, list[dict[str, Any]]]:
    if not table_exists(con, "trade_plan_outcomes"):
        return 0, []
    rows = [rowdict(r) for r in con.execute(
        """
        select id,direction,result,closed_at,max_favorable,max_adverse,note
        from trade_plan_outcomes
        where upper(symbol)=upper(?) and timeframe=? and status='closed'
        order by id desc limit ?
        """,
        (symbol, timeframe, limit),
    ).fetchall()]
    streak = 0
    for r in rows:
        if str(r.get("result") or "").upper() in LOSS_RESULTS:
            streak += 1
        else:
            break
    return streak, rows


def build_report(args: argparse.Namespace, con: sqlite3.Connection, state: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    signal = latest_signal(con, args.symbol, args.timeframe)
    opens = open_orders(con, args.symbol, args.timeframe)
    prev_closed_id = int(state.get("last_closed_id", 0) or 0)
    closed = recent_closed(con, args.symbol, args.timeframe, prev_closed_id)
    latest_closed_id = last_closed_id(con, args.symbol, args.timeframe)

    events: list[str] = []
    lines: list[str] = []

    if signal:
        sig_age = age_seconds(signal.get("created_at"))
        if sig_age is not None and sig_age > args.max_age_seconds and opens:
            events.append("STALE_DATA_WITH_OPEN_ORDERS")
            lines.append(f"- ⚠️ Data stale: signal ล่าสุดเก่า {sig_age//60} นาที แต่มี open orders {len(opens)} ไม้")
    elif opens:
        events.append("NO_SIGNAL_WITH_OPEN_ORDERS")
        lines.append(f"- ⚠️ ไม่มี trade_signal ล่าสุด แต่มี open orders {len(opens)} ไม้")

    urgent = [o for o in opens if str(o.get("management_state") or "").upper() in URGENT_STATES]
    if urgent:
        events.append("URGENT_OPEN_ORDER_MANAGEMENT")
        for o in urgent[:5]:
            lines.append(
                f"- 🚨 {'Scalp' if 'scalp' in str(o.get('source') or '').lower() else 'Order'} #{o.get('id')} {o.get('direction')} state={o.get('management_state')} "
                f"price={fmt_price(o.get('current_price'))} entry={fmt_price(o.get('entry_low'))}-{fmt_price(o.get('entry_high'))} "
                f"SL={fmt_price(o.get('sl'))} TP1={fmt_price(o.get('tp1'))}"
            )

    if closed:
        events.append("NEW_CLOSED_ORDERS")
        wins = sum(1 for r in closed if str(r.get("result") or "").upper() in WIN_RESULTS)
        losses = sum(1 for r in closed if str(r.get("result") or "").upper() in LOSS_RESULTS)
        lines.append(f"- ปิด order ใหม่ {len(closed)} ไม้: win={wins}, loss={losses}")
        for r in closed[-5:]:
            lines.append(
                f"  • {'Scalp' if 'scalp' in str(r.get('source') or '').lower() else 'Order'} #{r.get('id')} {r.get('direction')} result={r.get('result')} "
                f"MFE={fmt_price(r.get('max_favorable'))} MAE={fmt_price(r.get('max_adverse'))}"
            )

    streak, recent = recent_loss_streak(con, args.symbol, args.timeframe)
    last_reported_streak = int(state.get("last_loss_streak_reported", 0) or 0)
    if streak >= args.loss_streak_threshold and streak != last_reported_streak:
        events.append("REPEATED_LOSS_STREAK")
        ids = ",".join(str(r.get("id")) for r in recent[:streak])
        lines.append(f"- ⚠️ แพ้ต่อเนื่อง {streak} ไม้ล่าสุด (orders {ids}) ควรลด/หยุดฝั่งเดิมจนมี confirmation score สูง")

    # Routine state: no material event -> silent stdout.
    new_state = dict(state)
    new_state["last_checked_at"] = datetime.now(timezone.utc).isoformat()
    new_state["last_closed_id"] = latest_closed_id
    if streak >= args.loss_streak_threshold:
        new_state["last_loss_streak_reported"] = streak
    elif streak == 0:
        new_state["last_loss_streak_reported"] = 0

    if not events:
        return "", new_state

    sig_line = "- สถานะระบบ: "
    if signal:
        sig_line += f"{signal.get('bias')}/{signal.get('decision')} score={signal.get('total_score')} price={fmt_price(signal.get('price'))}"
    else:
        sig_line += "ไม่มี latest signal"

    report = "\n".join([
        "## MGT",
        sig_line,
        f"- Events: {', '.join(events)}",
        *lines,
        "- ต้องให้ Waipop อนุมัติไหม: ใช่ ถ้าจะปรับ logic/cron/code; ไม่ใช่ถ้าเป็นแค่แจ้งเตือน order",
    ])
    return report, new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Script-only MGT material event detector")
    parser.add_argument("--db-path", default=os.getenv("TRADINGVIEW_MCP_DB_PATH") or str(DEFAULT_DB))
    parser.add_argument("--state-path", default=str(DEFAULT_STATE))
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--max-age-seconds", type=int, default=300)
    parser.add_argument("--loss-streak-threshold", type=int, default=3)
    parser.add_argument("--no-state", action="store_true", help="Do not read/write detector state (for smoke tests)")
    args = parser.parse_args(argv)

    db = Path(args.db_path).expanduser()
    if not db.exists():
        print(f"## MGT\n- ⚠️ DB ไม่พบ: {db}\n- ต้องให้ Waipop อนุมัติไหม: ไม่ใช่")
        return 0

    state_path = Path(args.state_path).expanduser()
    state = {} if args.no_state else load_state(state_path)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    report, new_state = build_report(args, con, state)
    if not args.no_state:
        save_state(state_path, new_state)
    if report:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
