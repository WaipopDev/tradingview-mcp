#!/usr/bin/env python3
"""On-demand XAUUSD entry check: always answers via Telegram.

Not scheduled — run manually when asked something like "ตอนนี้มีจุดเข้าไหม".
Reuses the exact entry-derivation and gating logic from the sibling
`trad_entry_alert.py` (same directory) so the answer matches what the
automated 2-minute cron would decide. The only behavior difference is that
this always sends a reply, including a "no entry, here's why" message for
cases where the cron version would just stay silent.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = Path(
    os.getenv("TRAD_REPO_ROOT", str(Path.home() / "MainWTN" / "Hermes" / "trad"))
)


def _load_entry_alert():
    spec = importlib.util.spec_from_file_location(
        "trad_entry_alert", HERE / "trad_entry_alert.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def refresh_signal(symbol: str, timeframe: str, db_path: str) -> None:
    """Best-effort live refresh before answering; fail-soft into whatever is
    already in the DB (e.g. if the repo checkout or `uv` isn't reachable from
    wherever this script was deployed)."""
    collector = REPO_ROOT / "scripts" / "collect_trad_signal.py"
    if not collector.exists():
        return
    uv = os.getenv("TRAD_UV_BIN", str(Path.home() / ".local" / "bin" / "uv"))
    try:
        subprocess.run(
            [
                uv, "run", "python", str(collector),
                "--symbol", symbol, "--timeframe", timeframe,
                "--db-path", db_path, "--json",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def no_entry_message(symbol: str, price: float | None, reason: str) -> str:
    price_text = f"{price:g}" if price is not None else "-"
    return "\n".join([
        f"{symbol} ตอนนี้: {price_text}",
        "ยังไม่มีจุดเข้าตามเกณฑ์ตอนนี้",
        f"เหตุผล: {reason}",
    ])


def _reply(message: str, target: str, dry_run: bool) -> int:
    if dry_run:
        print(message)
        return 0
    sent = subprocess.run(
        ["hermes", "send", "--quiet", "--to", target, "--subject", "XAUUSD: มีจุดเข้าไหม", message],
        text=True,
        capture_output=True,
        check=False,
    )
    if sent.returncode != 0:
        print(sent.stderr.strip() or sent.stdout.strip(), file=sys.stderr)
    return sent.returncode


def main(argv: list[str] | None = None) -> int:
    ea = _load_entry_alert()
    p = argparse.ArgumentParser(
        description="On-demand check: is there an XAUUSD entry point right now?"
    )
    p.add_argument("--db-path", default=str(ea.db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--max-age-seconds", type=int, default=420)
    p.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET") or "telegram:8237892676")
    p.add_argument("--dry-run", action="store_true", help="Print the answer instead of sending Telegram")
    p.add_argument("--no-refresh", action="store_true", help="Skip the live data refresh; read the DB as-is")
    args = p.parse_args(argv)

    if not args.no_refresh:
        refresh_signal(args.symbol, args.timeframe, args.db_path)

    with ea.connect(Path(args.db_path).expanduser()) as con:
        row = ea.latest_signal(con, args.symbol, args.timeframe)
        if row is None or row["price"] is None:
            return _reply(f"{args.symbol}: ยังไม่มีข้อมูลราคาใน DB", args.target, args.dry_run)

        age = ea.signal_age_seconds(row)
        if age is None or age > args.max_age_seconds:
            age_text = "ไม่ทราบ" if age is None else f"{age:.0f} วินาที"
            message = "\n".join([
                f"{args.symbol} ล่าสุดที่มี: {ea.fmt(row['price'])}",
                f"ข้อมูลเก่าเกินไป (อายุ {age_text}, เกณฑ์ {args.max_age_seconds}s) ไม่ตอบจุดเข้าตอนนี้",
            ])
            return _reply(message, args.target, args.dry_run)

        order, fp = ea.derive_order(row)
        skip_reason = (
            ea.signal_quality_reason(row)
            or ea.global_entry_floor_reason(order)
            or ea.order_geometry_reason(order)
            or ea.open_duplicate_reason(con, order)
            or ea.recent_similar_zone_reason(con, order)
            or ea.adaptive_skip_reason(con, order)
        )
        if skip_reason:
            return _reply(no_entry_message(args.symbol, order.get("price"), skip_reason), args.target, args.dry_run)

        if ea.already_sent(con, order["symbol"], order["timeframe"], fp, args.target):
            message = "\n".join([
                f"{args.symbol} ตอนนี้: {ea.fmt(order['price'])}",
                f"มีจุดเข้า {order['direction']} โซนนี้อยู่แล้ว (เคยส่งไปก่อนหน้านี้) รอ TP/SL เดิม",
            ])
            return _reply(message, args.target, args.dry_run)

        outcome_id = ea.ensure_outcome(con, order, fp)
        message = ea.message_for_order(order, outcome_id)
        result = _reply(message, args.target, args.dry_run)
        if result == 0 and not args.dry_run:
            ea.mark_sent(con, order, fp, args.target, outcome_id)
        return result


if __name__ == "__main__":
    raise SystemExit(main())
