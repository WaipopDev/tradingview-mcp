#!/usr/bin/env python3
"""Analyze which SMC feature filters improve historical backtest edge.

Reads `backtest_trades` for a stored run, joins entry candles to
`historical_smc_features`, and evaluates individual/combined feature filters.
This is read-only analysis; it does not modify production trading logic.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FEATURES = [
    "ema_trend",
    "liquidity_sweep",
    "choch",
    "bos",
    "fvg",
    "order_block",
    "price_action_confirm",
    "order_flow_proxy",
]


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def latest_run_id(con: sqlite3.Connection, symbol: str, strategy: str) -> int | None:
    row = con.execute(
        "SELECT id FROM backtest_runs WHERE UPPER(symbol)=UPPER(?) AND strategy=? ORDER BY id DESC LIMIT 1",
        (symbol, strategy),
    ).fetchone()
    return None if row is None else int(row["id"])


def max_loss_streak(rows: list[sqlite3.Row]) -> int:
    streak = 0
    worst = 0
    for r in rows:
        if r["result"] == "SL":
            streak += 1
            worst = max(worst, streak)
        elif r["result"] == "TP":
            streak = 0
    return worst


def metrics(rows: list[sqlite3.Row]) -> dict[str, Any]:
    total = len(rows)
    wins = sum(1 for r in rows if r["result"] == "TP")
    losses = sum(1 for r in rows if r["result"] == "SL")
    time_exit = sum(1 for r in rows if r["result"] == "TIME_EXIT")
    exp_r = sum(float(r["r_multiple"]) for r in rows) / total if total else 0.0
    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "time_exit": time_exit,
        "win_rate": wins / total * 100.0 if total else 0.0,
        "expectancy_r": exp_r,
        "avg_mfe": sum(float(r["mfe"]) for r in rows) / total if total else 0.0,
        "avg_mae": sum(float(r["mae"]) for r in rows) / total if total else 0.0,
        "max_loss_streak": max_loss_streak(rows),
    }


def feature_supports(row: sqlite3.Row, feature: str) -> bool:
    value = row[feature]
    direction = row["direction"]
    return value == direction


def feature_opposes(row: sqlite3.Row, feature: str) -> bool:
    value = row[feature]
    direction = row["direction"]
    return value in {"BUY", "SELL"} and value != direction


def timeframe_seconds(timeframe: str) -> int:
    tf = timeframe.strip().lower()
    if tf.endswith("m"):
        return int(tf[:-1]) * 60
    if tf.endswith("h"):
        return int(tf[:-1]) * 3600
    if tf in {"1d", "d"}:
        return 86400
    return 0


def load_joined(con: sqlite3.Connection, run_id: int, feature_lag_bars: int = 0) -> list[sqlite3.Row]:
    run = con.execute("SELECT timeframe FROM backtest_runs WHERE id=?", (run_id,)).fetchone()
    lag_seconds = timeframe_seconds(str(run["timeframe"])) * max(0, int(feature_lag_bars)) if run else 0
    sql = """
        SELECT
          t.*,
          f.ema_trend,
          f.liquidity_sweep,
          f.choch,
          f.bos,
          f.fvg,
          f.order_block,
          f.price_action_confirm,
          f.order_flow_proxy,
          f.feature_score_buy,
          f.feature_score_sell,
          f.volume_ratio,
          f.features_json
        FROM backtest_trades t
        LEFT JOIN historical_smc_features f
          ON UPPER(f.symbol)=UPPER(t.symbol)
         AND UPPER(f.exchange)=UPPER(t.exchange)
         AND f.timeframe=t.timeframe
         AND f.ts=(t.entry_ts - ?)
        WHERE t.run_id=?
        ORDER BY t.entry_ts ASC, t.id ASC
    """
    return con.execute(sql, (lag_seconds, run_id)).fetchall()


def combo_results(rows: list[sqlite3.Row], min_trades: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    # Individual support, oppose-block, and combinations of supportive features.
    for feat in FEATURES:
        selected = [r for r in rows if feature_supports(r, feat)]
        if len(selected) >= min_trades:
            m = metrics(selected)
            out.append({"rule": f"require {feat}=direction", "features": [feat], "mode": "require_all", **m})
        blocked = [r for r in rows if not feature_opposes(r, feat)]
        if len(blocked) >= min_trades and len(blocked) < len(rows):
            m = metrics(blocked)
            out.append({"rule": f"block {feat}=opposite", "features": [feat], "mode": "block_opposite", **m})

    for n in (2, 3, 4):
        for combo in itertools.combinations(FEATURES, n):
            selected = [r for r in rows if all(feature_supports(r, f) for f in combo)]
            if len(selected) >= min_trades:
                m = metrics(selected)
                out.append({"rule": "require all: " + "+".join(combo), "features": list(combo), "mode": "require_all", **m})
            any_selected = [r for r in rows if any(feature_supports(r, f) for f in combo)]
            if len(any_selected) >= min_trades and len(any_selected) < len(rows):
                m = metrics(any_selected)
                out.append({"rule": "require any: " + "+".join(combo), "features": list(combo), "mode": "require_any", **m})

    # Score-style rule: not every condition required, just N supportive SMC marks.
    for threshold in range(1, 6):
        selected = []
        for r in rows:
            direction = r["direction"]
            score = int(r["feature_score_buy"] or 0) if direction == "BUY" else int(r["feature_score_sell"] or 0)
            if score >= threshold:
                selected.append(r)
        if len(selected) >= min_trades and len(selected) < len(rows):
            m = metrics(selected)
            out.append({"rule": f"SMC supportive score >= {threshold}", "features": FEATURES, "mode": "score_threshold", **m})
    return sorted(out, key=lambda x: (x["expectancy_r"], x["total"]), reverse=True)


def session_direction_breakdown(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[sqlite3.Row]] = {}
    for r in rows:
        groups.setdefault((str(r["direction"]), str(r["session_label"])), []).append(r)
    out = []
    for (direction, session), rs in groups.items():
        out.append({"direction": direction, "session": session, **metrics(rs)})
    return sorted(out, key=lambda x: x["expectancy_r"], reverse=True)


def build_report(con: sqlite3.Connection, run_id: int, min_trades: int, top_n: int, feature_lag_bars: int = 0) -> str:
    run = con.execute("SELECT * FROM backtest_runs WHERE id=?", (run_id,)).fetchone()
    rows = load_joined(con, run_id, feature_lag_bars)
    baseline = metrics(rows)
    feature_rows = [r for r in rows if r["ema_trend"] is not None]
    combos = combo_results(rows, min_trades)
    top = combos[:top_n]

    lines: list[str] = []
    lines.append("# Historical SMC Feature Combination Analysis")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()} UTC")
    lines.append(f"Backtest run: #{run_id} {run['exchange']}:{run['symbol']} {run['timeframe']} {run['strategy']}")
    lines.append(f"Date range: {run['date_from']} → {run['date_to']}")
    lines.append("Mode: read-only feature/filter analysis; production entry logic unchanged.")
    lines.append(f"Feature lag bars: {feature_lag_bars} (0=same entry candle, 1=prior closed candle / safer anti-lookahead check)")
    lines.append("")
    lines.append("## Baseline")
    lines.append(f"- Trades: {baseline['total']} | WR {baseline['win_rate']:.1f}% | ExpR {baseline['expectancy_r']:.3f} | max loss streak {baseline['max_loss_streak']} | MFE {baseline['avg_mfe']:.2f} | MAE {baseline['avg_mae']:.2f}")
    lines.append(f"- Trades joined to SMC features: {len(feature_rows)}/{len(rows)}")
    lines.append("")
    lines.append("## Direction/session baseline")
    for g in session_direction_breakdown(rows):
        lines.append(f"- {g['direction']} {g['session']}: trades {g['total']} | WR {g['win_rate']:.1f}% | ExpR {g['expectancy_r']:.3f} | maxLS {g['max_loss_streak']}")
    lines.append("")
    lines.append(f"## Top feature/filter simulations (min trades={min_trades})")
    if not top:
        lines.append("- No feature combination met sample threshold.")
    else:
        for r in top:
            delta = r["expectancy_r"] - baseline["expectancy_r"]
            coverage = r["total"] / baseline["total"] * 100 if baseline["total"] else 0
            lines.append(f"- {r['rule']}: trades {r['total']} ({coverage:.1f}%) | WR {r['win_rate']:.1f}% | ExpR {r['expectancy_r']:.3f} (Δ {delta:+.3f}) | maxLS {r['max_loss_streak']} | MFE {r['avg_mfe']:.2f} MAE {r['avg_mae']:.2f}")
    lines.append("")
    lines.append("## Individual feature support")
    for feat in FEATURES:
        selected = [r for r in rows if feature_supports(r, feat)]
        if selected:
            m = metrics(selected)
            lines.append(f"- {feat}=direction: trades {m['total']} | WR {m['win_rate']:.1f}% | ExpR {m['expectancy_r']:.3f}")
        else:
            lines.append(f"- {feat}=direction: trades 0")
    lines.append("")
    lines.append("## Practical reading")
    if top:
        best = top[0]
        lines.append(f"- Best paper filter: {best['rule']} with ExpR {best['expectancy_r']:.3f}, but coverage {best['total']}/{baseline['total']}. Treat as hypothesis, not production approval.")
    lines.append("- Prefer filters that improve ExpR and reduce max loss streak without cutting sample size too aggressively.")
    lines.append("- Next safe step: manually inspect top 2-3 filters and then run sequence-aware managed-exit replay before production entry filtering.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--run-id", type=int, default=None)
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--strategy", default="production_entry_replay")
    p.add_argument("--min-trades", type=int, default=30)
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--feature-lag-bars", type=int, default=0, help="0=same entry candle; 1=prior closed candle to reduce lookahead risk")
    p.add_argument("--output")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    with sqlite3.connect(Path(args.db_path).expanduser()) as con:
        con.row_factory = sqlite3.Row
        run_id = args.run_id or latest_run_id(con, args.symbol, args.strategy)
        if run_id is None:
            print("ERROR: no matching backtest run found")
            return 2
        rows = load_joined(con, run_id, args.feature_lag_bars)
        if not rows:
            print(f"ERROR: no trades for run_id={run_id}")
            return 2
        if args.json:
            result = {"run_id": run_id, "baseline": metrics(rows), "top": combo_results(rows, args.min_trades)[: args.top]}
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        report = build_report(con, run_id, args.min_trades, args.top, args.feature_lag_bars)
    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report + "\n", encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
