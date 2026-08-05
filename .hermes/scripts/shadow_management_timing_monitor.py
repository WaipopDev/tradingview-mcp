#!/usr/bin/env python3
"""Read-only shadow monitor for XAUUSD management timing.

Purpose: detect cases where MOVE_SL_BE / TAKE_PARTIAL should probably have
happened before a reversal, without mutating the live SQLite DB or production
scripts. This is paper/shadow validation only.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WIN_RESULTS = {"TP1", "TP2", "TP3", "PARTIAL_BE", "TRAIL_SL"}
LOSS_RESULTS = {"SL", "CUT"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def to_float(v: Any) -> float | None:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def parse_json(v: Any, default: Any) -> Any:
    if not v:
        return default
    try:
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return default


def entry_ref(row: sqlite3.Row | dict[str, Any]) -> float | None:
    entry = to_float(row["entry_price"] if "entry_price" in row.keys() else None)
    if entry is not None:
        return entry
    direction = str(row["direction"])
    return to_float(row["entry_high"] if direction == "BUY" else row["entry_low"])


def risk(row: sqlite3.Row | dict[str, Any]) -> float | None:
    entry = entry_ref(row)
    sl = to_float(row["sl"])
    if entry is None or sl is None:
        return None
    return abs(entry - sl)


def tp1_progress(row: sqlite3.Row | dict[str, Any]) -> float | None:
    mfe = to_float(row["max_favorable"]) or 0.0
    entry = entry_ref(row)
    tp1 = to_float(row["tp1"])
    if entry is None or tp1 is None:
        return None
    dist = abs(tp1 - entry)
    if dist <= 0:
        return None
    return mfe / dist


def favorable(direction: str, entry: float, price: float) -> float:
    return price - entry if direction == "BUY" else entry - price


def adverse(direction: str, entry: float, price: float) -> float:
    return entry - price if direction == "BUY" else price - entry


def protection_trigger_reason(row: sqlite3.Row | dict[str, Any]) -> str | None:
    mfe = to_float(row["max_favorable"]) or 0.0
    progress = tp1_progress(row)
    if mfe >= 5.0:
        return f"MFE>=5 ({mfe:.2f})"
    if progress is not None and progress >= 0.65:
        return f"TP1 progress>=65% ({progress*100:.1f}%)"
    return None


def closed_missed_cases(con: sqlite3.Connection, symbol: str, timeframe: str, limit: int) -> list[dict[str, Any]]:
    rows = con.execute(
        """
        SELECT * FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status='closed'
        ORDER BY id DESC
        LIMIT ?
        """,
        (symbol, timeframe, limit),
    ).fetchall()
    cases: list[dict[str, Any]] = []
    for row in rows:
        reason = protection_trigger_reason(row)
        if not reason:
            continue
        if row["result"] not in LOSS_RESULTS:
            continue
        if row["management_state"] or row["partial_taken_at"]:
            continue
        item = dict(row)
        item["paper_reason"] = reason
        item["risk"] = risk(row)
        item["tp1_progress"] = tp1_progress(row)
        item["paper_recommendation"] = "Shadow flag: would have needed earlier MOVE_SL_BE or TAKE_PARTIAL before reversal."
        cases.append(item)
    return list(reversed(cases))


def latest_signal(con: sqlite3.Connection, symbol: str, timeframe: str) -> sqlite3.Row | None:
    return con.execute(
        """
        SELECT * FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()


def open_shadow_actions(con: sqlite3.Connection, symbol: str, timeframe: str) -> list[dict[str, Any]]:
    sig = latest_signal(con, symbol, timeframe)
    if sig is None or sig["price"] is None:
        return []
    price = float(sig["price"])
    tech = parse_json(sig["technical_json"], {})
    rsi = tech.get("rsi") if isinstance(tech.get("rsi"), dict) else {}
    macd = tech.get("macd") if isinstance(tech.get("macd"), dict) else {}
    ema = tech.get("ema") if isinstance(tech.get("ema"), dict) else {}
    sentiment = tech.get("market_sentiment") if isinstance(tech.get("market_sentiment"), dict) else {}
    structure = tech.get("market_structure") if isinstance(tech.get("market_structure"), dict) else {}
    ema20 = to_float(ema.get("ema20"))
    rsi_val = to_float(rsi.get("value"))
    rsi_dir = str(rsi.get("direction") or "")
    macd_cross = str(macd.get("crossover") or "")
    momentum = str(sentiment.get("momentum") or "")
    trend = str(structure.get("trend") or "")

    rows = con.execute(
        """
        SELECT * FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status IN ('pending','entered')
        ORDER BY id ASC
        """,
        (symbol, timeframe),
    ).fetchall()
    actions: list[dict[str, Any]] = []
    for row in rows:
        direction = str(row["direction"])
        entry = entry_ref(row)
        rr = risk(row) or 0.01
        if entry is None:
            continue
        live_profit = favorable(direction, entry, price)
        live_adverse = adverse(direction, entry, price)
        mfe = max(to_float(row["max_favorable"]) or 0.0, live_profit)
        mae = max(to_float(row["max_adverse"]) or 0.0, live_adverse)
        tp1 = to_float(row["tp1"])
        progress = None if tp1 is None else mfe / max(0.01, abs(tp1 - entry))
        if direction == "BUY":
            reversal = (rsi_val is not None and rsi_val >= 66 and "Fall" in rsi_dir) or "Bear" in macd_cross or (ema20 is not None and price < ema20)
            aligned = (ema20 is None or price >= ema20) and "Bear" not in momentum and "Bear" not in trend
        else:
            reversal = (rsi_val is not None and rsi_val <= 34 and "Ris" in rsi_dir) or "Bull" in macd_cross or (ema20 is not None and price > ema20)
            aligned = (ema20 is None or price <= ema20) and "Bull" not in momentum and "Bull" not in trend

        action = "HOLD"
        reason = "no shadow management trigger"
        suggested_sl = None
        if not row["partial_taken_at"] and (mfe >= 5.0 or (progress is not None and progress >= 0.65)) and reversal:
            action = "TAKE_PARTIAL"
            suggested_sl = entry
            reason = f"paper trigger: MFE={mfe:.2f}, TP1 progress={(progress or 0)*100:.1f}%, reversal=True"
        elif row["management_state"] != "BE_PROTECTED" and live_profit >= 0.5 * rr:
            action = "MOVE_SL_BE"
            suggested_sl = entry
            reason = f"paper trigger: live profit {live_profit:.2f} >= 0.5R ({0.5*rr:.2f})"
        elif not aligned and live_profit <= 0:
            action = "PROTECT"
            reason = "paper trigger: not aligned and not profitable"
        if action != "HOLD":
            actions.append(
                {
                    "id": row["id"],
                    "source": row["source"],
                    "direction": direction,
                    "status": row["status"],
                    "price": price,
                    "entry": entry,
                    "sl": row["sl"],
                    "tp1": row["tp1"],
                    "mfe": mfe,
                    "mae": mae,
                    "profit": live_profit,
                    "risk": rr,
                    "tp1_progress": progress,
                    "action": action,
                    "suggested_sl": suggested_sl,
                    "reason": reason,
                    "latest_signal_at": sig["created_at"],
                }
            )
    return actions


def build_report(db_path: Path, symbol: str, timeframe: str, limit: int) -> str:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        open_actions = open_shadow_actions(con, symbol, timeframe)
        missed = closed_missed_cases(con, symbol, timeframe, limit)
        open_count = con.execute(
            "SELECT COUNT(*) FROM trade_plan_outcomes WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status IN ('pending','entered')",
            (symbol, timeframe),
        ).fetchone()[0]
    finally:
        con.close()

    lines: list[str] = []
    lines.append("# Shadow Management Timing Monitor — XAUUSD")
    lines.append("")
    lines.append(f"Generated: {utc_now()} UTC")
    lines.append(f"DB: {db_path}")
    lines.append("Mode: READ-ONLY paper monitor; no production DB/code mutation.")
    lines.append("")
    lines.append("## Current open-order shadow actions")
    lines.append(f"- Open orders: {open_count}")
    if not open_actions:
        lines.append("- No paper MOVE_SL_BE / TAKE_PARTIAL / PROTECT trigger on currently open orders.")
    else:
        for a in open_actions:
            lines.append(
                f"- #{a['id']} {a['source']} {a['direction']} action={a['action']} "
                f"price={a['price']:.2f} entry={a['entry']:.2f} profit={a['profit']:.2f} "
                f"MFE={a['mfe']:.2f} MAE={a['mae']:.2f} R≈{a['risk']:.2f} | {a['reason']}"
            )
    lines.append("")
    lines.append(f"## Closed-order missed-protection scan, last {limit} closed outcomes")
    lines.append(f"- Missed-protection cases: {len(missed)}")
    if not missed:
        lines.append("- None.")
    else:
        for item in missed:
            progress = item["tp1_progress"]
            lines.append(
                f"- #{item['id']} {item['source']} {item['direction']} result={item['result']} "
                f"MFE={to_float(item['max_favorable']) or 0:.2f} MAE={to_float(item['max_adverse']) or 0:.2f} "
                f"risk≈{item['risk'] or 0:.2f} TP1_progress={(progress or 0)*100:.1f}% | {item['paper_reason']}"
            )
    lines.append("")
    lines.append("## Paper recommendation")
    if open_actions:
        lines.append("- Watch current open orders closely; paper trigger exists but was not applied because this monitor is read-only.")
    elif missed:
        lines.append("- Keep production unchanged. Next shadow test should tune management timing thresholds on the missed-protection cluster before any live logic patch.")
    else:
        lines.append("- No immediate management-timing issue detected in the current sample.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=str(db_path_from_env()))
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(Path(args.db_path).expanduser(), args.symbol, args.timeframe, args.limit)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
