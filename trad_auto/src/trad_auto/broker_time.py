"""Explicit broker wall-clock timestamp conversion; never infer from a tick."""
import math


def offset_seconds(hours):
    if isinstance(hours, bool) or not isinstance(hours, (int, float)) or not math.isfinite(hours) or not -12 <= hours <= 14 or hours * 60 != round(hours * 60):
        raise ValueError('invalid broker UTC offset hours')
    return int(hours * 3600)


def check_forming_bar(api, symbol, timeframe, now, offset):
    """Confirm broker's current bar is the UTC bar containing now."""
    from .core import SECONDS
    rows = api.copy_rates_from_pos(symbol, getattr(api, 'TIMEFRAME_' + timeframe), 0, 1)
    if rows is None or len(rows) != 1:
        raise ValueError('broker forming bar unavailable')
    raw = int(rows[0]['time'])
    interval = SECONDS[timeframe]
    if not raw - offset <= now < raw - offset + interval:
        raise ValueError('broker forming bar inconsistent with offset or clock')
