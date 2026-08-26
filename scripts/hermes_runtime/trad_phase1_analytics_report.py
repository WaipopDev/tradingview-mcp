#!/usr/bin/env python3
"""Phase 1 evidence analytics report for Waipop's XAUUSD MGT/Analyst workflow.

Reads the local trading SQLite DB and prints a concise evidence report. It does
not modify DB, orders, cron, or trading logic.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB = Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"
WIN_RESULTS = {"TP1", "TP2", "TP3", "PARTIAL_BE", "TRAIL_SL"}
LOSS_RESULTS = {"SL", "CUT"}
NEUTRAL_RESULTS = {"BE"}


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def local_hour_ict(value: Any) -> int | None:
    dt = parse_dt(value)
    if not dt:
        return None
    return (dt.hour + 7) % 24


def session_name(value: Any) -> str:
    """Approximate trading session from ICT hour."""
    h = local_hour_ict(value)
    if h is None:
        return "unknown"
    if 6 <= h < 14:
        return "Asia"
    if 14 <= h < 19:
        return "London"
    if 19 <= h < 23:
        return "London/NY overlap"
    return "NY/late"


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute("select 1 from sqlite_master where type='table' and name=?", (name,)).fetchone() is not None


def parse_json(value: Any, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value) if isinstance(value, str) else value
    except Exception:
        return default


def row_get(row: sqlite3.Row, key: str, default: Any = None) -> Any:
    try:
        return row[key] if key in row.keys() else default
    except Exception:
        return default


def analytics_score(row: sqlite3.Row) -> Any:
    return row_get(row, "order_score") or row_get(row, "setup_score") or row_get(row, "total_score")


def score_band(score: Any) -> str:
    try:
        s = int(score)
    except Exception:
        return "unknown"
    if s < 50:
        return "<50"
    if s < 60:
        return "50-59"
    if s < 70:
        return "60-69"
    if s < 80:
        return "70-79"
    if s < 90:
        return "80-89"
    return "90+"


def setup_type(row: sqlite3.Row) -> str:
    stored = row_get(row, "setup_type")
    if stored:
        return str(stored)
    src = str(row["source"] or "")
    if "scalp" in src.lower():
        return "scalp-watch"
    regime = str(row["regime"] or "").lower()
    reasons = parse_json(row["reason_codes_json"], [])
    reason_text = " ".join(map(str, reasons)).lower() if isinstance(reasons, list) else str(reasons).lower()
    if "range" in regime or "mean" in regime:
        return "rejection/mean-reversion"
    if "trend" in regime or "momentum" in regime:
        return "continuation/trend"
    if "break" in reason_text:
        return "breakout"
    if "pullback" in reason_text:
        return "pullback"
    return "unknown"


def risk_units(row: sqlite3.Row) -> float:
    try:
        direction = str(row["direction"])
        entry_low = float(row["entry_low"])
        entry_high = float(row["entry_high"])
        sl = float(row["sl"])
        if direction == "BUY":
            return max(0.01, entry_high - sl)
        return max(0.01, sl - entry_low)
    except Exception:
        return 0.01


def outcome_r(row: sqlite3.Row) -> float:
    result = str(row["result"] or "").upper()
    risk = risk_units(row)
    mfe = float(row["max_favorable"] or 0)
    mae = float(row["max_adverse"] or 0)
    if result in WIN_RESULTS:
        if result == "PARTIAL_BE":
            return max(0.1, (mfe / risk) * float(row["partial_fraction"] or 0.5))
        return max(0.1, mfe / risk)
    if result in LOSS_RESULTS:
        return -max(0.1, mae / risk)
    if result in NEUTRAL_RESULTS:
        return 0.0
    return 0.0


def is_win(row: sqlite3.Row) -> bool:
    return str(row["result"] or "").upper() in WIN_RESULTS


def is_loss(row: sqlite3.Row) -> bool:
    return str(row["result"] or "").upper() in LOSS_RESULTS


def summarize(rows: Iterable[sqlite3.Row]) -> dict[str, Any]:
    rs = list(rows)
    n = len(rs)
    wins = sum(1 for r in rs if is_win(r))
    losses = sum(1 for r in rs if is_loss(r))
    neutral = n - wins - losses
    mfe = [float(r["max_favorable"] or 0) for r in rs]
    mae = [float(r["max_adverse"] or 0) for r in rs]
    rvals = [outcome_r(r) for r in rs]
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "neutral": neutral,
        "win_rate": (wins / n * 100) if n else 0.0,
        "avg_mfe": sum(mfe) / n if n else 0.0,
        "avg_mae": sum(mae) / n if n else 0.0,
        "expectancy_r": sum(rvals) / n if n else 0.0,
    }


def fmt_summary(s: dict[str, Any]) -> str:
    return (
        f"n={s['n']} win={s['wins']} loss={s['losses']} neutral={s['neutral']} "
        f"WR={s['win_rate']:.1f}% MFE={s['avg_mfe']:.2f} MAE={s['avg_mae']:.2f} ExpR={s['expectancy_r']:.2f}"
    )


def group_lines(title: str, rows: list[sqlite3.Row], key_fn, min_n: int = 1) -> list[str]:
    groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        groups[str(key_fn(r))].append(r)
    out = [f"## {title}"]
    items = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    if not items:
        out.append("- ไม่มีข้อมูล")
        return out
    for key, vals in items:
        if len(vals) < min_n:
            continue
        out.append(f"- {key}: {fmt_summary(summarize(vals))}")
    return out


def duplicate_zone_stats(rows: list[sqlite3.Row]) -> tuple[int, list[str]]:
    ordered = sorted(rows, key=lambda r: parse_dt(r["created_at"]) or datetime.min.replace(tzinfo=timezone.utc))
    dup_count = 0
    examples: list[str] = []
    for i, r in enumerate(ordered):
        dt = parse_dt(r["created_at"])
        if not dt:
            continue
        center = (float(r["entry_low"]) + float(r["entry_high"])) / 2
        width = max(0.01, float(r["entry_high"]) - float(r["entry_low"]))
        for prev in reversed(ordered[:i]):
            pdt = parse_dt(prev["created_at"])
            if not pdt:
                continue
            minutes = (dt - pdt).total_seconds() / 60
            if minutes > 45:
                break
            if str(prev["direction"]) != str(r["direction"]):
                continue
            pcenter = (float(prev["entry_low"]) + float(prev["entry_high"])) / 2
            overlap = max(0.0, min(float(prev["entry_high"]), float(r["entry_high"])) - max(float(prev["entry_low"]), float(r["entry_low"])))
            if abs(center - pcenter) <= 3.0 or overlap / width >= 0.35:
                dup_count += 1
                if len(examples) < 5:
                    examples.append(f"Order #{r['id']} ใกล้ #{prev['id']} {r['direction']} Δ{minutes:.0f}m result={r['result']}")
                break
    return dup_count, examples


def stale_stats(rows: list[sqlite3.Row]) -> dict[str, Any]:
    ages: list[float] = []
    stale_rows: list[sqlite3.Row] = []
    for r in rows:
        odt = parse_dt(r["created_at"])
        sdt = parse_dt(r["signal_created_at"])
        if not odt or not sdt:
            continue
        age_min = abs((odt - sdt).total_seconds()) / 60
        ages.append(age_min)
        if age_min > 10:
            stale_rows.append(r)
    return {
        "with_signal_time": len(ages),
        "avg_age_min": sum(ages) / len(ages) if ages else 0.0,
        "stale_count": len(stale_rows),
        "stale_summary": summarize(stale_rows),
    }


def recommendations(rows: list[sqlite3.Row]) -> list[str]:
    recs: list[str] = []
    by_dir: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        by_dir[str(r["direction"])].append(r)
    for direction, vals in by_dir.items():
        s = summarize(vals)
        if s["n"] >= 5 and s["win_rate"] < 45:
            recs.append(f"{direction}: WR ต่ำ {s['win_rate']:.1f}% จาก {s['n']} ไม้ → เพิ่ม gate หรือพักฝั่งนี้เมื่อ MTF ไม่ confirm")
    if len(by_dir.get("SELL", [])) < 5:
        recs.append(f"data gap: SELL sample มี {len(by_dir.get('SELL', []))} ไม้ → ยังห้ามสรุปว่า SELL logic ดี/แย่; ต้องเก็บผลเพิ่มก่อน calibrate ฝั่ง SELL")
    # Score-band calibration uses Phase 1B order_score/setup_score when present, else falls back to signal total_score.
    bands: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        bands[score_band(analytics_score(r))].append(r)
    for band, vals in sorted(bands.items()):
        s = summarize(vals)
        if s["n"] >= 5 and s["expectancy_r"] < 0:
            recs.append(f"score {band}: ExpR {s['expectancy_r']:.2f} จาก {s['n']} ไม้ → ห้ามเพิ่ม order ใน band นี้จนมี confirmation เพิ่ม")
    score_coverage = sum(1 for r in rows if row_get(r, "order_score") is not None or row_get(r, "setup_score") is not None)
    setup_coverage = sum(1 for r in rows if row_get(r, "setup_type"))
    if score_coverage < max(5, len(rows) // 2):
        recs.append("data quality: Phase 1B fields addedแล้ว แต่ historical outcomes ยังไม่มี order_score/setup_score → รอ order ใหม่ปิดก่อน calibrate score band")
    setup_groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for r in rows:
        setup_groups[setup_type(r)].append(r)
    if setup_coverage < max(5, len(rows) // 2) or len(setup_groups) <= 2:
        recs.append("setup taxonomy: Phase 1B fields addedแล้ว แต่ historical sample ยังไม่แยก setup_type → รอ sample ใหม่เพื่อแยก rejection/breakout/continuation/pullback")
    dup_count, _ = duplicate_zone_stats(rows)
    if dup_count >= 3:
        recs.append(f"duplicate zone: พบ {dup_count} ไม้ซ้ำ/ใกล้ใน 45 นาที → คง/เพิ่ม duplicate guard และวัดผลหลังแก้")
    if not recs:
        recs.append("ข้อมูลยังไม่ชี้ว่าต้องแก้ logic ทันที → เก็บ sample เพิ่มและคง gate ปัจจุบัน")
    return recs[:3]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate Phase 1 trad analytics evidence report")
    ap.add_argument("--db-path", default=os.getenv("TRADINGVIEW_MCP_DB_PATH") or str(DEFAULT_DB))
    ap.add_argument("--symbol", default="XAUUSD")
    ap.add_argument("--timeframe", default="15m")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--min-group-n", type=int, default=1)
    args = ap.parse_args(argv)

    db = Path(args.db_path).expanduser()
    if not db.exists():
        print(f"ERROR: DB not found: {db}")
        return 2
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    if not table_exists(con, "trade_plan_outcomes"):
        print("ERROR: table trade_plan_outcomes not found")
        return 2

    rows = con.execute(
        """
        SELECT o.*, s.created_at AS signal_created_at, s.total_score, s.decision, s.bias,
               s.regime, s.reason_codes_json, s.score_breakdown_json
        FROM trade_plan_outcomes o
        LEFT JOIN trade_signals s ON s.id = o.source_signal_id
        WHERE UPPER(o.symbol)=UPPER(?) AND o.timeframe=? AND o.status='closed'
        ORDER BY o.id DESC
        LIMIT ?
        """,
        (args.symbol, args.timeframe, args.limit),
    ).fetchall()
    rows = list(reversed(rows))

    scalp_count = 0
    if table_exists(con, "telegram_scalp_watch_alerts"):
        scalp_count = con.execute(
            "SELECT count(*) FROM telegram_scalp_watch_alerts WHERE UPPER(symbol)=UPPER(?) AND timeframe=?",
            (args.symbol, args.timeframe),
        ).fetchone()[0]

    lines: list[str] = []
    lines.append("# Phase 1 MGT/Analyst Evidence Report")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()} UTC")
    lines.append(f"Scope: {args.symbol} {args.timeframe}, last {len(rows)} closed outcomes, scalp-watch alerts={scalp_count}")
    lines.append("")
    lines.append("## Overall")
    lines.append(f"- {fmt_summary(summarize(rows))}")
    score_coverage = sum(1 for r in rows if row_get(r, "order_score") is not None or row_get(r, "setup_score") is not None)
    setup_coverage = sum(1 for r in rows if row_get(r, "setup_type"))
    session_coverage = sum(1 for r in rows if row_get(r, "session_label"))
    lines.append(f"- Phase 1B field coverage: score={score_coverage}/{len(rows)}, setup_type={setup_coverage}/{len(rows)}, session_label={session_coverage}/{len(rows)}")
    lines.append("")
    for title, fn in [
        ("By direction", lambda r: r["direction"]),
        ("By session", lambda r: row_get(r, "session_label") or session_name(r["created_at"])),
        ("By setup type", setup_type),
        ("By score band", lambda r: score_band(analytics_score(r))),
        ("By regime", lambda r: r["regime"] or "unknown"),
        ("By result", lambda r: r["result"] or "unknown"),
    ]:
        lines.extend(group_lines(title, rows, fn, args.min_group_n))
        lines.append("")

    dup_count, examples = duplicate_zone_stats(rows)
    lines.append("## Duplicate-zone behavior")
    lines.append(f"- near-duplicate same-direction zones within 45m: {dup_count}/{len(rows)}")
    for ex in examples:
        lines.append(f"  • {ex}")
    lines.append("")

    st = stale_stats(rows)
    lines.append("## Stale-data impact")
    lines.append(f"- orders with linked signal timestamp: {st['with_signal_time']}/{len(rows)}")
    lines.append(f"- avg order-vs-signal age: {st['avg_age_min']:.1f}m")
    lines.append(f"- >10m stale-linked orders: {st['stale_count']} | {fmt_summary(st['stale_summary'])}")
    lines.append("")

    lines.append("## Top 3 MGT recommendations")
    for i, rec in enumerate(recommendations(rows), start=1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    lines.append("Note: evidence report only; no trading logic was modified.")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
