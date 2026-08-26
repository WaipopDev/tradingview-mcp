#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

DB = Path(os.path.expanduser("~/.tradingview-mcp/trading_signals.sqlite3"))


def pct(n: int, d: int) -> float:
    return round(n * 100.0 / d, 1) if d else 0.0


def f(v):
    return None if v is None else float(v)


def classified_result(result: str | None) -> str:
    r = str(result or "")
    if r.startswith("TP") or r == "PARTIAL_BE":
        return "WIN"
    if r in {"SL", "CUT"}:
        return "LOSS"
    if r in {"BE", "TRAIL_SL"}:
        return "NEUTRAL"
    return "OTHER"


def aggregate(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[str(r[key] if r[key] is not None else "NULL")].append(r)
    out = []
    for name, group in sorted(groups.items()):
        c = Counter(classified_result(r["result"]) for r in group)
        decided = c["WIN"] + c["LOSS"]
        out.append({
            key: name,
            "n": len(group),
            "wins": c["WIN"],
            "losses": c["LOSS"],
            "neutral": c["NEUTRAL"],
            "decided_wr_pct": pct(c["WIN"], decided),
            "all_closed_win_pct": pct(c["WIN"], len(group)),
            "avg_mfe": round(mean(f(r["max_favorable"]) or 0 for r in group), 2),
            "avg_mae": round(mean(f(r["max_adverse"]) or 0 for r in group), 2),
        })
    return out


def main():
    print(json.dumps({"db": str(DB), "exists": DB.exists(), "size_bytes": DB.stat().st_size if DB.exists() else None}))
    if not DB.exists():
        raise SystemExit(2)
    # SQLite may need to open WAL/SHM sidecars even for a read-only audit.
    # Open normally, then enforce query_only so every write statement is rejected.
    con = sqlite3.connect(DB)
    con.execute("PRAGMA query_only=ON")
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("TABLES=" + json.dumps(tables))
    cols = [r[1] for r in con.execute("PRAGMA table_info(trade_plan_outcomes)")]
    print("OUTCOME_COLUMNS=" + json.dumps(cols))

    rows = con.execute("SELECT * FROM trade_plan_outcomes WHERE status='closed' ORDER BY id").fetchall()
    counts = Counter(classified_result(r["result"]) for r in rows)
    result_counts = Counter(str(r["result"] or "NULL") for r in rows)
    print("OVERALL=" + json.dumps({
        "closed": len(rows),
        "results": result_counts,
        "classes": counts,
        "decided_wr_pct": pct(counts["WIN"], counts["WIN"] + counts["LOSS"]),
        "all_closed_win_pct": pct(counts["WIN"], len(rows)),
    }))

    for key in ["source", "direction", "setup_type", "session_label"]:
        if key in cols:
            print(key.upper() + "=" + json.dumps(aggregate(rows, key), ensure_ascii=False))

    for score_col in ["setup_score", "order_score"]:
        if score_col not in cols:
            continue
        buckets = defaultdict(list)
        for r in rows:
            v = f(r[score_col])
            bucket = "NULL" if v is None else ("<60" if v < 60 else "60-69" if v < 70 else "70-79" if v < 80 else ">=80")
            buckets[bucket].append(r)
        out = []
        for b, group in sorted(buckets.items()):
            c = Counter(classified_result(r["result"]) for r in group)
            out.append({"bucket": b, "n": len(group), "wins": c["WIN"], "losses": c["LOSS"], "neutral": c["NEUTRAL"], "decided_wr_pct": pct(c["WIN"], c["WIN"] + c["LOSS"])})
        print(score_col.upper() + "=" + json.dumps(out))

    losses = [r for r in rows if classified_result(r["result"]) == "LOSS"]
    never_entered_losses = [r for r in losses if r["entry_price"] is None or r["entered_at"] is None]
    entered_losses = [r for r in losses if r["entry_price"] is not None and r["entered_at"] is not None]
    missed = [r for r in losses if (f(r["max_favorable"]) or 0) >= 5.0 and not r["partial_taken_at"]]
    corrected_wins = counts["WIN"]
    corrected_losses = len(entered_losses)
    print("LOSS_DIAGNOSTICS=" + json.dumps({
        "losses": len(losses),
        "never_entered_false_losses": len(never_entered_losses),
        "entered_losses": len(entered_losses),
        "corrected_decided_wr_excluding_never_entered_pct": pct(corrected_wins, corrected_wins + corrected_losses),
        "never_entered_by_source_direction": dict(Counter(f"{r['source']}:{r['direction']}:{r['result']}" for r in never_entered_losses)),
        "loss_avg_mfe": round(mean(f(r["max_favorable"]) or 0 for r in losses), 2) if losses else 0,
        "loss_median_mfe": round(median(f(r["max_favorable"]) or 0 for r in losses), 2) if losses else 0,
        "loss_avg_mae": round(mean(f(r["max_adverse"]) or 0 for r in losses), 2) if losses else 0,
        "mfe_ge_3": sum((f(r["max_favorable"]) or 0) >= 3 for r in losses),
        "mfe_ge_5": sum((f(r["max_favorable"]) or 0) >= 5 for r in losses),
        "mfe_ge_5_unprotected": len(missed),
        "mfe_zero": sum((f(r["max_favorable"]) or 0) <= 0.05 for r in losses),
    }))

    detail_cols = ["id", "source", "direction", "result", "entry_price", "entry_low", "entry_high", "sl", "tp1", "current_price", "max_favorable", "max_adverse", "setup_score", "order_score", "setup_type", "session_label", "management_state", "partial_taken_at", "created_at", "closed_at", "exit_reason", "source_signal_id"]
    detail_cols = [c for c in detail_cols if c in cols]
    recent_losses = sorted(losses, key=lambda r: r["id"], reverse=True)[:30]
    print("RECENT_LOSSES=" + json.dumps([{c: r[c] for c in detail_cols} for r in recent_losses], ensure_ascii=False))
    print("NEVER_ENTERED_FALSE_LOSSES=" + json.dumps([{c: r[c] for c in detail_cols} for r in never_entered_losses], ensure_ascii=False))
    print("MISSED_PROTECTION=" + json.dumps([{c: r[c] for c in detail_cols} for r in missed], ensure_ascii=False))

    # Cross-dimensions for the newer, metadata-rich sample.
    for keys in [("source", "direction"), ("source", "session_label"), ("direction", "session_label")]:
        groups = defaultdict(list)
        for r in rows:
            groups[tuple(str(r[k] if r[k] is not None else "NULL") for k in keys)].append(r)
        out = []
        for names, group in sorted(groups.items()):
            c = Counter(classified_result(r["result"]) for r in group)
            out.append({**dict(zip(keys, names)), "n": len(group), "wins": c["WIN"], "losses": c["LOSS"], "neutral": c["NEUTRAL"], "decided_wr_pct": pct(c["WIN"], c["WIN"] + c["LOSS"])})
        print("X_".join(k.upper() for k in keys) + "=" + json.dumps(out, ensure_ascii=False))

    # Join source signal context where available.
    if "trade_signals" in tables:
        joined = con.execute("""
            SELECT o.id, o.source, o.direction, o.result, o.max_favorable, o.max_adverse,
                   o.setup_score, o.order_score, o.setup_type, o.session_label,
                   s.bias signal_bias, s.decision, s.total_score signal_score,
                   s.regime, s.price signal_price, s.created_at signal_created_at
            FROM trade_plan_outcomes o
            LEFT JOIN trade_signals s ON s.id=o.source_signal_id
            WHERE o.status='closed' AND o.result IN ('SL','CUT')
            ORDER BY o.id DESC
        """).fetchall()
        print("LOSS_SIGNAL_CONTEXT=" + json.dumps([dict(r) for r in joined], ensure_ascii=False))


if __name__ == "__main__":
    main()
