#!/usr/bin/env python3
"""Collect and cache the latest XAUUSD compact trade signal.

Default mode is silent on success so it is safe for Hermes cron no_agent jobs.
Use --json for smoke tests/manual inspection.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradingview_mcp.core.jobs.analyze_and_store_signal import analyze_and_store_signal  # noqa: E402
from tradingview_mcp.core.services.mt5_market_data_service import (  # noqa: E402
    Mt5SnapshotError,
    analyze_mt5_coin,
    run_mt5_multi_timeframe_analysis,
)
from tradingview_mcp.core.storage.mt5_quote_repository import Mt5QuoteRepository  # noqa: E402


def _retryable_error(result: dict) -> bool:
    raw_error = result.get("error")
    if isinstance(raw_error, dict):
        return bool(raw_error.get("retryable"))
    return False


def _persist_mt5_quote(result: dict, db_path: str | None) -> None:
    technical = result.get("technical") or {}
    price_data = technical.get("price_data") or {}
    tick_time_ms = technical.get("timestamp")
    if tick_time_ms is None or price_data.get("bid") is None or price_data.get("ask") is None:
        return
    repository = Mt5QuoteRepository(db_path)
    repository.save_quote(
        "XAUUSD",
        int(tick_time_ms),
        float(price_data["bid"]),
        float(price_data["ask"]),
        price_data.get("spread_points"),
    )
    retention_days = int(os.getenv("TRAD_MT5_QUOTE_RETENTION_DAYS", "7"))
    repository.cleanup_retention(int(tick_time_ms) - retention_days * 86_400_000)


def main(argv: list[str] | None = None, analyze_fn=analyze_and_store_signal) -> int:
    parser = argparse.ArgumentParser(description="Collect latest trad signal into SQLite")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--exchange", default="OANDA")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument(
        "--data-source",
        choices=("tradingview", "mt5"),
        default=(os.getenv("TRAD_MARKET_DATA_SOURCE") or "tradingview").strip().lower(),
    )
    parser.add_argument("--mt5-snapshot-path", default=os.getenv("TRAD_MT5_SNAPSHOT_PATH"))
    parser.add_argument(
        "--db-path",
        default=os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH"),
        help="SQLite DB path (also supports TRADINGVIEW_MCP_DB_PATH or TRAD_SIGNAL_DB_PATH)",
    )
    parser.add_argument("--json", action="store_true", help="Print compact result JSON")
    parser.add_argument("--print-ai-required", action="store_true", help="Print only when ai_gate.should_ask_ai is true")
    args = parser.parse_args(argv)

    analyze_kwargs = {
        "symbol": args.symbol,
        "exchange": args.exchange,
        "timeframe": args.timeframe,
        "db_path": args.db_path,
    }
    if args.data_source == "mt5":
        def mt5_coin(symbol: str, exchange: str, timeframe: str):
            try:
                return analyze_mt5_coin(symbol, exchange, timeframe, snapshot_path=args.mt5_snapshot_path)
            except Mt5SnapshotError as exc:
                return {"error": {"code": "MT5_SNAPSHOT_UNAVAILABLE", "message": str(exc), "retryable": True}}

        def mt5_mtf(full_symbol: str, exchange: str):
            try:
                return run_mt5_multi_timeframe_analysis(full_symbol, exchange, snapshot_path=args.mt5_snapshot_path)
            except Mt5SnapshotError as exc:
                return {"error": {"code": "MT5_SNAPSHOT_UNAVAILABLE", "message": str(exc), "retryable": True}}

        analyze_kwargs.update({
            "exchange": "MT5",
            "analyze_coin_fn": mt5_coin,
            "multi_timeframe_fn": mt5_mtf,
        })
    result = analyze_fn(**analyze_kwargs)
    if result.get("error"):
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        elif not _retryable_error(result):
            print(json.dumps(result, ensure_ascii=False), file=sys.stderr)
        return 0 if _retryable_error(result) else 1

    if args.data_source == "mt5":
        _persist_mt5_quote(result, args.db_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.print_ai_required and (result.get("ai_gate") or {}).get("should_ask_ai"):
        print(json.dumps({"ai_required": True, "signal": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
