#!/usr/bin/env python3
"""Read-only shadow/paper validation for XAUUSD outcome classification.

This script intentionally does not mutate production code or the SQLite DB.
It checks whether stored trade_plan_outcomes match the current paper
classification rules and flags missed management/protection cases.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

WIN_RESULTS = {"TP1", "TP2", "TP3", "PARTIAL_BE", "TRAIL_SL"}
NEUTRAL_RESULTS = {"BE"}
LOSS_RESULTS = {"SL", "CUT"}


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def to_float(value):
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def risk(row: sqlite3.Row) -> float | None:
    entry = to_float(row["entry_price"])
    if entry is None:
        entry = to_float(row["entry_high"] if row["direction"] == "BUY" else row["entry_low"])
    sl = to_float(row["sl"])
    if entry is None or sl is None:
        return None
    return abs(entry - sl)


def proposed_shadow_result(row: sqlite3.Row) -> tuple[str | None, str]:
    result = row["result"]
    source = str(row["source"] or "").lower()
    mfe = to_float(row["max_favorable"]) or 0.0
    mae = to_float(row["max_adverse"]) or 0.0
    rr = risk(row) or 0.01

    if "scalp" in source and result == "CUT" and mfe >= 5.0 and mae <= max(1.5, 0.6 * rr):
        return "PARTIAL_BE", "late-scalp-MFE>=5 snapped back; should be managed BE/PARTIAL_BE"
    if row["partial_taken_at"] and result in {"SL", "CUT", "BE"}:
        return "PARTIAL_BE", "partial_taken_at exists; terminal should be PARTIAL_BE if returned to BE/zone"
    if row["management_state"] == "BE_PROTECTED" and result in {"SL", "CUT"}:
        return "BE", "BE_PROTECTED exists; terminal loss should not remain full SL/CUT"
    return result, ""


def stats(rows, result_key: str) -> tuple[int, int, int, int, float]:
    total = len(rows)
    wins = sum(1 for row in rows if row[result_key] in WIN_RESULTS)
    losses = sum(1 for row in rows if row[result_key] in LOSS_RESULTS)
    be = sum(1 for row in rows if row[result_key] in NEUTRAL_RESULTS)
    win_rate = (wins / total * 100.0) if total else 0.0
    return total, wins, losses, be, win_rate


def build_report(db_path: Path, symbol: str, timeframe: str) -> str:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        rows = con.execute(
            """
            SELECT * FROM trade_plan_outcomes
            WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status='closed'
            ORDER BY id ASC
            """,
            (symbol, timeframe),
        ).fetchall()
    finally:
        con.close()

    enriched = []
    changes = []
    missed = []
    for row in rows:
        item = dict(row)
        shadow, reason = proposed_shadow_result(row)
        item["shadow_result"] = shadow
        item["shadow_reason"] = reason
        item["risk"] = risk(row)
        enriched.append(item)
        if shadow != row["result"]:
            changes.append(item)
        if (
            row["result"] in LOSS_RESULTS
            and (to_float(row["max_favorable"]) or 0.0) >= 5.0
            and not row["partial_taken_at"]
            and not row["management_state"]
        ):
            missed.append(item)

    current = stats(enriched, "result")
    shadow = stats(enriched, "shadow_result")

    lines: list[str] = []
    lines.append("# Shadow/Paper Validation — XAUUSD outcome classification")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()} UTC")
    lines.append(f"DB: {db_path}")
    lines.append("Mode: READ-ONLY; no DB/code mutation.")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Closed outcomes checked: {current[0]}")
    lines.append(f"- Current stats: Win {current[1]}/{current[0]} = {current[4]:.1f}% | Loss {current[2]} | BE {current[3]}")
    lines.append(f"- Shadow stats:  Win {shadow[1]}/{shadow[0]} = {shadow[4]:.1f}% | Loss {shadow[2]} | BE {shadow[3]}")
    lines.append(f"- Classification diffs: {len(changes)}")
    lines.append(f"- Missed-protection warnings: {len(missed)}")
    lines.append("")
    lines.append("## Classification diffs")
    if not changes:
        lines.append("- None. Current stored results match shadow rules.")
    else:
        for item in changes:
            lines.append(
                f"- #{item['id']} {item['source']} {item['direction']} "
                f"{item['result']} -> {item['shadow_result']} | "
                f"MFE={to_float(item['max_favorable']) or 0:.2f} MAE={to_float(item['max_adverse']) or 0:.2f} | "
                f"{item['shadow_reason']}"
            )
    lines.append("")
    lines.append("## Missed-protection warnings")
    if not missed:
        lines.append("- None.")
    else:
        for item in missed:
            lines.append(
                f"- #{item['id']} {item['source']} {item['direction']} result={item['result']} "
                f"MFE={to_float(item['max_favorable']) or 0:.2f} MAE={to_float(item['max_adverse']) or 0:.2f} "
                f"risk≈{item['risk'] or 0:.2f} created={item['created_at']}"
            )
    lines.append("")
    if changes:
        lines.append("Verdict: NOT READY — review classification diffs before production expansion.")
    elif missed:
        lines.append("Verdict: CLASSIFICATION PASS, but management timing needs paper tuning before production expansion.")
    else:
        lines.append("Verdict: PASS — no classification diffs or missed-protection warnings.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", default=str(db_path_from_env()))
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(Path(args.db_path).expanduser(), args.symbol, args.timeframe)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
