"""Deterministic closed-candle analysis; no platform or execution dependency."""
from dataclasses import dataclass
import math

SECONDS = {'M5': 300, 'M15': 900, 'M30': 1800, 'H1': 3600}


class ValidationError(ValueError):
    """Safe local validation message, never a raw platform exception."""


@dataclass(frozen=True)
class Candle:
    time: int
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Config:
    symbol: str = 'XAUUSD'
    timeframe: str = 'M5'
    pivot: int = 2
    rr: float = 1.0
    max_spread: float = 1.0
    max_tick_age: float = 120.0
    retest_bars: int = 4

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol.strip() or self.symbol != self.symbol.strip():
            raise ValidationError('symbol must be exact nonempty broker symbol')
        if self.timeframe not in SECONDS:
            raise ValidationError('unsupported timeframe')
        for name in ('pivot', 'retest_bars'):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= 20:
                raise ValidationError(f'invalid {name}')
        for name in ('rr', 'max_spread', 'max_tick_age'):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValidationError(f'invalid {name}')


def pivots(bars, width):
    result = []
    for i in range(width, len(bars) - width):
        neighbors = bars[i-width:i] + bars[i+1:i+width+1]
        if all(bars[i].high > b.high for b in neighbors):
            result.append({'index': i, 'confirmed_at': i + width, 'kind': 'high', 'price': bars[i].high})
        if all(bars[i].low < b.low for b in neighbors):
            result.append({'index': i, 'confirmed_at': i + width, 'kind': 'low', 'price': bars[i].low})
    return result


def structure(bars, width):
    points = pivots(bars, width)
    highs = [p['price'] for p in points if p['kind'] == 'high']
    lows = [p['price'] for p in points if p['kind'] == 'low']
    high_label = ('HH' if highs[-1] > highs[-2] else 'LH' if highs[-1] < highs[-2] else 'EQ') if len(highs) >= 2 else 'unknown'
    low_label = ('HL' if lows[-1] > lows[-2] else 'LL' if lows[-1] < lows[-2] else 'EQ') if len(lows) >= 2 else 'unknown'
    trend = 'bullish' if (high_label, low_label) == ('HH', 'HL') else 'bearish' if (high_label, low_label) == ('LH', 'LL') else 'range'
    return {'trend': trend, 'highs': high_label, 'lows': low_label, 'pivots': points}


def quote_check(config, now, bid, ask, tick_time):
    if not all(math.isfinite(v) and v > 0 for v in (bid, ask, tick_time)) or ask < bid:
        raise ValidationError('invalid quote')
    # Whole-second broker ticks may lead the local clock slightly; never allow more than 2s.
    if not -2 <= now - tick_time <= config.max_tick_age:
        raise ValidationError('stale or future tick')
    if ask - bid > config.max_spread:
        raise ValidationError('spread exceeds maximum price units')


def setup(bars, config, higher_trend=None):
    result = {'action': 'WAIT', 'reason': 'no confirmed BOS/retest/rejection', 'execution_enabled': False}
    latest = bars[-1]
    for j in range(len(bars)-2, max(0, len(bars)-config.retest_bars-2), -1):
        prior = structure(bars[:j], config.pivot)
        trend = prior['trend']
        if trend == 'range' or (higher_trend is not None and higher_trend != trend):
            continue
        bullish = trend == 'bullish'
        kind = 'high' if bullish else 'low'
        level = [p['price'] for p in prior['pivots'] if p['kind'] == kind][-1]
        broken = bars[j-1].close <= level < bars[j].close if bullish else bars[j-1].close >= level > bars[j].close
        if not broken:
            continue
        body = abs(latest.close-latest.open)
        wick = min(latest.open, latest.close)-latest.low if bullish else latest.high-max(latest.open, latest.close)
        rejection = latest.close > latest.open and latest.close > level if bullish else latest.close < latest.open and latest.close < level
        intact = all(b.close > level if bullish else b.close < level for b in bars[j+1:])
        if not (latest.low <= level <= latest.high and rejection and wick >= body and intact):
            continue
        stop = min(b.low for b in bars[j:]) if bullish else max(b.high for b in bars[j:])
        entry = latest.close
        risk = abs(entry-stop)
        target = entry + config.rr*risk if bullish else entry-config.rr*risk
        if risk <= 0 or target <= 0 or not math.isfinite(target):
            continue
        return {**result, 'action': 'BUY' if bullish else 'SELL', 'reason': 'confirmed BOS then retest and wick rejection',
                'entry': entry, 'stop': stop, 'target': target, 'rr': config.rr,
                'entry_basis': 'last_closed_candle_close_not_executable_quote',
                'bos': {'index': j, 'time': bars[j].time, 'level': level},
                'structure': prior, 'higher_trend': higher_trend, 'asof': latest.time+SECONDS[config.timeframe]}
    return result


def analyze(bars, config, *, now, bid, ask, tick_time, higher_trend=None):
    try:
        validate(bars, config, now)
        quote_check(config, now, bid, ask, tick_time)
    except (ValueError, TypeError, OverflowError) as exc:
        return {'action': 'WAIT', 'reason': str(exc), 'execution_enabled': False, 'data_ready': False}
    return {**setup(bars, config, higher_trend), 'data_ready': True}


def replay(bars, config, higher_bars=None):
    from dataclasses import replace
    if not bars:
        raise ValidationError('no historical candles')
    validate(bars, config, bars[-1].time + SECONDS[config.timeframe])
    hconfig = replace(config, timeframe='H1')
    if higher_bars:
        validate(higher_bars, hconfig, higher_bars[-1].time + 3600)
    events, seen = [], set()
    evaluated = 0
    for end in range(2*config.pivot+6, len(bars)+1):
        prefix = bars[:end]
        asof = prefix[-1].time + SECONDS[config.timeframe]
        higher_trend = None
        if higher_bars is not None:
            available = [b for b in higher_bars if b.time + 3600 <= asof]
            try:
                validate(available, hconfig, asof)
            except ValueError:
                continue
            higher_trend = structure(available, config.pivot)['trend']
        evaluated += 1
        plan = setup(prefix, config, higher_trend)
        if plan['action'] != 'WAIT':
            key = (plan['action'], plan['bos']['time'])
            if key not in seen:
                seen.add(key)
                events.append(plan)
    return {'mode': 'historical_setup_counts', 'execution_enabled': False,
            'profitability_evaluated': False, 'spread_checked': False,
            'counts': {side: sum(p['action'] == side for p in events) for side in ('BUY', 'SELL')},
            'evaluated_prefixes': evaluated, 'candles': len(bars), 'setups': events}


def validate(bars, config, now):
    if not math.isfinite(now) or len(bars) < 2 * config.pivot + 6:
        raise ValidationError('insufficient data or invalid clock')
    previous = -1
    seconds = SECONDS[config.timeframe]
    for bar in bars:
        if not isinstance(bar.time, int) or bar.time < 0 or bar.time <= previous:
            raise ValidationError('timestamps must be sorted unique nonnegative integers')
        if not all(math.isfinite(v) and v > 0 for v in (bar.open, bar.high, bar.low, bar.close)):
            raise ValidationError('OHLC must be finite positive')
        if not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high:
            raise ValidationError('invalid OHLC envelope')
        if bar.time + seconds > now:
            raise ValidationError('forming or future candle')
        previous = bar.time
    if now - (bars[-1].time + seconds) > seconds:
        raise ValidationError('stale candles')
