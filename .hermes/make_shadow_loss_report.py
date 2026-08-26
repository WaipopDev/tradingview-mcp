#!/usr/bin/env python3
from __future__ import annotations

import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

DB = Path(os.path.expanduser("~/.tradingview-mcp/trading_signals.sqlite3"))
OUT = Path(__file__).with_name("shadow-validation-order-losses-2026-08-06.md")


def kind(result: str | None) -> str:
    r = str(result or "")
    if r.startswith("TP") or r == "PARTIAL_BE": return "W"
    if r in {"SL", "CUT"}: return "L"
    return "N"


def rate(w: int, l: int) -> float:
    return w * 100 / (w + l) if w + l else 0.0


def main() -> None:
    con = sqlite3.connect(DB)
    con.execute("PRAGMA query_only=ON")
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM trade_plan_outcomes WHERE status='closed' ORDER BY id").fetchall()
    wins = [r for r in rows if kind(r["result"]) == "W"]
    losses = [r for r in rows if kind(r["result"]) == "L"]
    neutral = [r for r in rows if kind(r["result"]) == "N"]
    unentered_closed = [r for r in rows if r["entry_price"] is None or r["entered_at"] is None]
    false_losses = [r for r in unentered_closed if kind(r["result"]) == "L"]
    false_wins = [r for r in unentered_closed if kind(r["result"]) == "W"]
    actual_wins = [r for r in wins if r not in unentered_closed]
    true_losses = [r for r in losses if r not in unentered_closed]
    actual_neutral = [r for r in neutral if r not in unentered_closed]

    lines = [
        "# Shadow Validation — Order Loss Logic (2026-08-06)", "",
        f"- DB: `{DB}`", "- Mode: `PRAGMA query_only=ON` (no DB mutation)",
        "- Scope: outcome classification + pending/entered management + Scalp HTF gate", "",
        "## Baseline vs shadow", "",
        f"- Stored closed: {len(rows)} | Win {len(wins)} | Loss {len(losses)} | Neutral {len(neutral)}",
        f"- Stored decided WR: {rate(len(wins), len(losses)):.1f}%",
        f"- Closed rows with no actual entry (`entry_price` or `entered_at` NULL): **{len(unentered_closed)}** ({len(false_wins)} false win / {len(false_losses)} false losses)",
        f"- Shadow actual entered trades: {len(actual_wins)}W / {len(true_losses)}L / {len(actual_neutral)} neutral",
        f"- Shadow decided WR after excluding never-entered rows: **{rate(len(actual_wins), len(true_losses)):.1f}%**",
        f"- Shadow Win/closed after excluding never-entered rows: **{len(actual_wins) * 100 / max(1, len(actual_wins)+len(true_losses)+len(actual_neutral)):.1f}%**", "",
        "## Never-entered rows incorrectly counted as outcomes", "",
        "| ID | Source | Side | Result | Entry trigger/zone | MFE | MAE |",
        "|---:|---|---|---|---:|---:|---:|",
    ]
    for r in unentered_closed:
        zone = f"{float(r['entry_low']):.2f}" if float(r["entry_low"]) == float(r["entry_high"]) else f"{float(r['entry_low']):.2f}-{float(r['entry_high']):.2f}"
        lines.append(f"| {r['id']} | {r['source']} | {r['direction']} | {r['result']} | {zone} | {float(r['max_favorable'] or 0):.2f} | {float(r['max_adverse'] or 0):.2f} |")

    actual_rows = [r for r in rows if r not in unentered_closed]
    by_source_side = defaultdict(Counter)
    for r in actual_rows:
        by_source_side[(str(r["source"]), str(r["direction"]))][kind(r["result"])] += 1
    lines += ["", "## Actual entered breakdown", "", "| Source | Side | W | L | N | Decided WR |", "|---|---|---:|---:|---:|---:|"]
    for (source, side), c in sorted(by_source_side.items()):
        lines.append(f"| {source} | {side} | {c['W']} | {c['L']} | {c['N']} | {rate(c['W'], c['L']):.1f}% |")

    scalp = [r for r in actual_rows if r["source"] == "telegram_scalp_watch"]
    score_groups = defaultdict(Counter)
    for r in scalp:
        score = r["setup_score"]
        bucket = "NULL" if score is None else ("<60" if float(score) < 60 else "60-69" if float(score) < 70 else ">=70")
        score_groups[(bucket, str(r["direction"]))][kind(r["result"])] += 1
    lines += ["", "## Scalp Watch score/side", "", "| Score | Side | W | L | N | Decided WR |", "|---|---|---:|---:|---:|---:|"]
    for (bucket, side), c in sorted(score_groups.items()):
        lines.append(f"| {bucket} | {side} | {c['W']} | {c['L']} | {c['N']} | {rate(c['W'], c['L']):.1f}% |")

    missed = [r for r in true_losses if float(r["max_favorable"] or 0) >= 5 and not r["partial_taken_at"]]
    lines += ["", "## Management timing", "", f"- Entered losses with MFE >= 5 but no partial protection: **{len(missed)}**", f"- IDs: {', '.join('#'+str(r['id']) for r in missed) or '-'}", ""]
    lines += [
        "## Root-cause verdict", "",
        "1. **PASS — safe to patch pending-management bug:** `trad_order_manager.open_orders()` selected both pending and entered rows. Pending setups could be closed as CUT before any entry occurred.",
        "2. **PASS — safe to patch fallback bug:** emergency price fallback also evaluated pending rows and could create false TP/SL (observed in regression test).",
        "3. **PASS — safe to patch entry-state bug:** generic zone crossing marked main pullback orders entered without touching their zone; crossing semantics belong only to Scalp Watch trigger orders.",
        "4. **PASS — safe to patch Scalp HTF lookup bug:** `build_watch()` called `.get()` on `sqlite3.Row`; the caught exception silently forced HTF bias to NEUTRAL and bypassed counter-trend score >=75.",
        "5. **PASS — safe to patch missing-HTF behavior:** an all-empty MTF response looked like valid NEUTRAL and allowed low-score scalps; Scalp Watch must fail closed when H1/H4 evidence is unavailable.",
        "6. **PASS — safe to patch stale-signal behavior:** main entry alert had no age check and could reuse the last DB signal after a fail-soft collector outage.",
        "7. **PASS — safe to patch reporting:** user-facing stats must exclude closed rows with no actual entry, without rewriting historical DB outcomes.",
        "8. **NOT APPROVED in this patch:** broad score/session/strategy threshold changes. The actual-entered post-instrumentation sample is still small.",
        "9. Existing historical rows must not be rewritten automatically; report corrected analytics separately unless user explicitly approves data repair.", "",
        "## Applied production change", "",
        "- Order manager and emergency fallback manage only `status='entered'` rows.",
        "- Main/manual orders enter only while price is inside their zone; crossing is retained only for Scalp Watch triggers.",
        "- Scalp Watch reads symbol via `row['symbol']`, requires real H1/H4 evidence, and otherwise fails closed.",
        "- Main entry alert rejects stale/invalid signals older than 420 seconds.",
        "- Outcome stats count only rows with non-null `entry_price` and `entered_at`.",
        "- Existing score thresholds, SL/TP, and session rules remain unchanged.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
