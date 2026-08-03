#!/usr/bin/env python3
"""Collect and cache the latest XAUUSD compact trade signal.

Default mode is silent on success so it is safe for Hermes cron no_agent jobs.
Use --json for smoke tests/manual inspection.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradingview_mcp.core.jobs.analyze_and_store_signal import analyze_and_store_signal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect latest trad signal into SQLite")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--exchange", default="OANDA")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--json", action="store_true", help="Print compact result JSON")
    parser.add_argument("--print-ai-required", action="store_true", help="Print only when ai_gate.should_ask_ai is true")
    args = parser.parse_args()

    result = analyze_and_store_signal(symbol=args.symbol, exchange=args.exchange, timeframe=args.timeframe)
    if result.get("error"):
        print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        raw_error = result.get("error")
        error = raw_error if isinstance(raw_error, dict) else {}
        return 0 if error.get("retryable") else 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.print_ai_required and (result.get("ai_gate") or {}).get("should_ask_ai"):
        print(json.dumps({"ai_required": True, "signal": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
