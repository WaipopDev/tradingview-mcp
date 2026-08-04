#!/usr/bin/env python3
"""Ask AI and notify Telegram only when the deterministic trade signal requests it."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tradingview_mcp.core.jobs.ai_signal_alert import build_ai_prompt, build_telegram_subject, should_ask_ai_for_signal  # noqa: E402
from tradingview_mcp.core.storage.repositories import SignalAiResponseRepository, TradeSignalRepository  # noqa: E402


def _run(cmd: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, capture_output=True, check=False)


def _clean_response(stdout: str) -> str:
    lines = [line.rstrip() for line in stdout.splitlines()]
    # `hermes chat -Q` normally returns only the final response; keep a small
    # guard for optional session footer lines if a provider prints them later.
    filtered = [line for line in lines if not line.startswith("Session ID:")]
    return "\n".join(filtered).strip()


def _fingerprint_for_signal(signal: dict, ai_repo: SignalAiResponseRepository) -> str:
    gate = signal.get("ai_gate") or {}
    if isinstance(gate, dict):
        fingerprint = str(gate.get("signal_fingerprint") or "")
        if fingerprint:
            return fingerprint
    return ai_repo.fingerprint_signal(signal)


def main(
    argv: list[str] | None = None,
    *,
    trade_repo: TradeSignalRepository | None = None,
    ai_repo: SignalAiResponseRepository | None = None,
    run_fn=_run,
) -> int:
    parser = argparse.ArgumentParser(description="Ask AI + Telegram alert only when ai_gate.should_ask_ai is true")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument(
        "--db-path",
        default=os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH"),
        help="SQLite DB path (also supports TRADINGVIEW_MCP_DB_PATH or TRAD_SIGNAL_DB_PATH)",
    )
    parser.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET"), help="Telegram target/channel; required unless --dry-run or --no-send")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt or cached alert without asking AI or sending Telegram")
    parser.add_argument("--no-send", action="store_true", help="Ask/cache AI if needed, then print alert without sending Telegram")
    args = parser.parse_args(argv)

    trade_repo = trade_repo or TradeSignalRepository(args.db_path)
    ai_repo = ai_repo or SignalAiResponseRepository(args.db_path)

    signal = trade_repo.get_latest_trade_signal(args.symbol, args.timeframe)
    if not signal:
        return 0

    gate = signal.get("ai_gate") or {}
    cached_response = str(gate.get("cached_response") or "") if isinstance(gate, dict) else ""
    fingerprint = _fingerprint_for_signal(signal, ai_repo)
    if not fingerprint:
        return 0
    symbol = str(signal.get("symbol") or args.symbol)
    timeframe = str(signal.get("timeframe") or args.timeframe)
    if not cached_response:
        cached_response = ai_repo.get_cached_response(symbol, timeframe, fingerprint) or ""

    target = args.target or "dry-run" if args.dry_run else args.target
    if not target and not args.no_send:
        print("TRAD_TELEGRAM_TARGET or --target is required unless --dry-run/--no-send", file=sys.stderr)
        return 2

    if target and target != "dry-run" and ai_repo.has_alert_delivery(args.symbol, args.timeframe, fingerprint, target):
        return 0

    response = cached_response
    if not response:
        if not should_ask_ai_for_signal(signal):
            return 0

        prompt = build_ai_prompt(signal)
        if args.dry_run:
            print(prompt)
            return 0

        ai = run_fn([
            "hermes",
            "chat",
            "-Q",
            "--max-turns",
            "1",
            "--source",
            "trad-ai-alert-cron",
            "-t",
            "safe",
            "-q",
            prompt,
        ])
        if ai.returncode != 0:
            print(ai.stderr.strip() or ai.stdout.strip(), file=sys.stderr)
            return ai.returncode

        response = _clean_response(ai.stdout)
        if not response:
            print("AI returned empty response", file=sys.stderr)
            return 1

        ai_repo.insert_ai_response(
            symbol=symbol,
            timeframe=timeframe,
            signal_fingerprint=fingerprint,
            ai_response=response,
            source="cron-telegram-alert",
        )

    if args.dry_run or args.no_send:
        print(response)
        return 0

    sent = run_fn([
        "hermes",
        "send",
        "--quiet",
        "--to",
        args.target,
        "--subject",
        build_telegram_subject(signal),
        response,
    ])
    if sent.returncode != 0:
        print(sent.stderr.strip() or sent.stdout.strip(), file=sys.stderr)
        return sent.returncode
    ai_repo.mark_alert_delivered(args.symbol, args.timeframe, fingerprint, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
