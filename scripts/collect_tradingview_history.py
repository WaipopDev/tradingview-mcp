#!/usr/bin/env python3
"""Collect TradingView historical candles into the local SQLite DB.

Example:
  uv run python scripts/collect_tradingview_history.py --symbol XAUUSD --exchange OANDA --timeframes 5m,15m,1h --bars 500
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

from tradingview_mcp.core.services.tradingview_history_service import collect_and_store_historical_candles


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect TradingView chart candles into SQLite")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--exchange", default="OANDA")
    parser.add_argument("--timeframes", default="5m,15m,1h", help="Comma-separated list, e.g. 5m,15m,1h")
    parser.add_argument("--bars", type=int, default=500)
    parser.add_argument("--db-path", default=None)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = []
    ok = True
    for tf in [x.strip() for x in args.timeframes.split(",") if x.strip()]:
        result = collect_and_store_historical_candles(
            symbol=args.symbol,
            exchange=args.exchange,
            timeframe=tf,
            bars=args.bars,
            db_path=args.db_path,
            timeout=args.timeout,
        )
        results.append(result)
        if result.get("status") != "ok":
            ok = False

    if args.json:
        print(json.dumps({"ok": ok, "results": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r.get("status") == "ok":
                print(f"OK {r['exchange']}:{r['symbol']} {r['timeframe']} stored={r['stored_bars']} db={r.get('db_path')}")
            else:
                print(f"ERROR {r['exchange']}:{r['symbol']} {r['timeframe']}: {r.get('error')}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
