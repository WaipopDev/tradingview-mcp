#!/usr/bin/env python3
"""Market-hours guard for XAUUSD cron collectors.

Returns 0 when market is considered open, 1 when closed.
Default XAUUSD closed window: Friday 22:00 UTC through Sunday 22:00 UTC
(approximately Saturday 05:00 through Monday 05:00 Thailand time).
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone


def xauusd_is_open(now: datetime | None = None) -> bool:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    weekday = now.weekday()  # Mon=0 ... Sun=6
    hour = now.hour
    if weekday == 5:  # Saturday UTC
        return False
    if weekday == 6:  # Sunday UTC before reopen
        return hour >= 22
    if weekday == 4 and hour >= 22:  # Friday after close
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="XAUUSD")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    is_open = xauusd_is_open()
    if not args.quiet:
        print("open" if is_open else "closed")
    return 0 if is_open else 1


if __name__ == "__main__":
    raise SystemExit(main())
