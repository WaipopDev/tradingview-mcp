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


def main() -> int:
    parser = argparse.ArgumentParser(description="Ask AI + Telegram alert only when ai_gate.should_ask_ai is true")
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--timeframe", default="15m")
    parser.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET", "telegram"))
    parser.add_argument("--dry-run", action="store_true", help="Print what would be sent without asking AI or sending Telegram")
    args = parser.parse_args()

    signal = TradeSignalRepository().get_latest_trade_signal(args.symbol, args.timeframe)
    if not should_ask_ai_for_signal(signal):
        return 0

    assert signal is not None
    gate = signal.get("ai_gate") or {}
    fingerprint = str(gate.get("signal_fingerprint") or "") if isinstance(gate, dict) else ""
    if not fingerprint:
        return 0

    prompt = build_ai_prompt(signal)
    if args.dry_run:
        print(prompt)
        return 0

    ai = _run([
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

    SignalAiResponseRepository().insert_ai_response(
        symbol=str(signal.get("symbol") or args.symbol),
        timeframe=str(signal.get("timeframe") or args.timeframe),
        signal_fingerprint=fingerprint,
        ai_response=response,
        source="cron-telegram-alert",
    )

    sent = _run([
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
