#!/usr/bin/env python3
"""Run DB-backed backtests from `historical_candles`.

Example:
  uv run python scripts/run_historical_backtest.py --symbol XAUUSD --exchange OANDA --timeframe 15m --strategy ema_trend --score-gate 60 --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradingview_mcp.core.services.historical_backtest_service import run_db_backtest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run historical_candles DB backtest")
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--strategy", default="live_logic_replay", choices=["ema_trend", "bollinger_rejection", "live_logic_replay"])
    p.add_argument("--score-gate", type=int, default=60)
    p.add_argument("--rr", type=float, default=1.5)
    p.add_argument("--sl-atr", type=float, default=1.2)
    p.add_argument("--max-hold-bars", type=int, default=12)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--db-path", default=None)
    p.add_argument("--no-store", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    result = run_db_backtest(
        symbol=args.symbol,
        exchange=args.exchange,
        timeframe=args.timeframe,
        strategy=args.strategy,
        db_path=args.db_path,
        score_gate=args.score_gate,
        rr=args.rr,
        sl_atr=args.sl_atr,
        max_hold_bars=args.max_hold_bars,
        limit=args.limit,
        store=not args.no_store,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(
            f"Backtest #{result.get('run_id', '-')} {result['exchange']}:{result['symbol']} {result['timeframe']} {result['strategy']} "
            f"candles={result['candle_count']} trades={result['total_trades']} WR={result['win_rate']:.1f}% "
            f"ExpR={result['expectancy_r']:.2f} MFE={result['avg_mfe']:.2f} MAE={result['avg_mae']:.2f}"
        )
    return 2 if "error" in result else 0


if __name__ == "__main__":
    raise SystemExit(main())
