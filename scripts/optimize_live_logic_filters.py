#!/usr/bin/env python3
"""Phase 2D grid experiments for live_logic_replay filters.

Runs no-store backtests over local TradingView candles and optionally stores the
best candidate run for audit.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradingview_mcp.core.services.historical_backtest_service import run_db_backtest


def candidate_grid() -> list[dict[str, Any]]:
    sessions = [None, "Asia", "London", "London/NY overlap", "NY/late", "Asia,London", "Asia,NY/late"]
    directions = [None, "BUY", "SELL"]
    mtf_filters = ["off", "with_trend", "strict_with_trend"]
    score_gates = [70, 80, 85, 90]
    setups = [None, "live_logic/BUY_rejection", "live_logic/SELL_rejection"]
    grid: list[dict[str, object]] = []
    for score_gate in score_gates:
        for mtf_filter in mtf_filters:
            for allowed_sessions in sessions:
                for allowed_directions in directions:
                    for allowed_setups in setups:
                        if allowed_setups == "live_logic/BUY_rejection" and allowed_directions == "SELL":
                            continue
                        if allowed_setups == "live_logic/SELL_rejection" and allowed_directions == "BUY":
                            continue
                        grid.append({
                            "score_gate": score_gate,
                            "mtf_filter": mtf_filter,
                            "allowed_sessions": allowed_sessions,
                            "allowed_directions": allowed_directions,
                            "allowed_setups": allowed_setups,
                        })
    return grid


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Optimize live_logic_replay filters")
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--mtf-timeframe", default="1h")
    p.add_argument("--rr", type=float, default=1.2)
    p.add_argument("--sl-atr", type=float, default=1.0)
    p.add_argument("--max-hold-bars", type=int, default=8)
    p.add_argument("--min-trades", type=int, default=20)
    p.add_argument("--top", type=int, default=12)
    p.add_argument("--store-best", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    rows = []
    for params in candidate_grid():
        result = run_db_backtest(
            symbol=args.symbol,
            exchange=args.exchange,
            timeframe=args.timeframe,
            strategy="live_logic_replay",
            score_gate=int(params["score_gate"]),
            rr=args.rr,
            sl_atr=args.sl_atr,
            max_hold_bars=args.max_hold_bars,
            store=False,
            allowed_sessions=params["allowed_sessions"],
            allowed_directions=params["allowed_directions"],
            allowed_setups=params["allowed_setups"],
            mtf_filter=str(params["mtf_filter"]),
            mtf_timeframe=args.mtf_timeframe,
        )
        if "error" in result:
            continue
        row = {**params, **{k: result[k] for k in ["total_trades", "wins", "losses", "win_rate", "expectancy_r", "avg_mfe", "avg_mae", "max_loss_streak"]}}
        rows.append(row)
    eligible = [r for r in rows if int(r["total_trades"]) >= args.min_trades]
    eligible.sort(key=lambda r: (float(r["expectancy_r"]), float(r["win_rate"]), int(r["total_trades"])), reverse=True)
    best = eligible[0] if eligible else None
    stored_best = None
    if args.store_best and best:
        stored_best = run_db_backtest(
            symbol=args.symbol,
            exchange=args.exchange,
            timeframe=args.timeframe,
            strategy="live_logic_replay",
            score_gate=int(best["score_gate"]),
            rr=args.rr,
            sl_atr=args.sl_atr,
            max_hold_bars=args.max_hold_bars,
            store=True,
            allowed_sessions=best.get("allowed_sessions"),
            allowed_directions=best.get("allowed_directions"),
            allowed_setups=best.get("allowed_setups"),
            mtf_filter=str(best.get("mtf_filter") or "off"),
            mtf_timeframe=args.mtf_timeframe,
        )
    payload = {"count": len(rows), "eligible_count": len(eligible), "best": best, "top": eligible[: args.top], "stored_best": stored_best}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"tested={len(rows)} eligible={len(eligible)} min_trades={args.min_trades}")
        for i, r in enumerate(eligible[: args.top], 1):
            print(
                f"#{i} trades={r['total_trades']} WR={float(r['win_rate']):.1f}% ExpR={float(r['expectancy_r']):.2f} "
                f"MFE={float(r['avg_mfe']):.2f} MAE={float(r['avg_mae']):.2f} LS={r['max_loss_streak']} "
                f"score={r['score_gate']} mtf={r['mtf_filter']} sessions={r['allowed_sessions']} "
                f"dir={r['allowed_directions']} setup={r['allowed_setups']}"
            )
        if stored_best:
            print(f"stored_best_run_id={stored_best.get('run_id')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
