import pytest
from trad_auto.core import Candle, Config, validate


def candles():
    return [Candle(i * 900, 100, 102, 98, 101) for i in range(10)]


def test_confirmed_pivots_and_structure_no_lookahead():
    from trad_auto.core import pivots, structure
    bars = [Candle(i * 900, p, p + 1, p - 1, p) for i, p in enumerate([10, 12, 10, 13, 11, 14, 12])]
    assert pivots(bars[:2], 1) == []
    assert pivots(bars[:3], 1) == [{'index': 1, 'confirmed_at': 2, 'kind': 'high', 'price': 13}]
    assert structure(bars, 1)['trend'] == 'bullish'
    assert structure(bars, 1)['highs'] == 'HH'
    assert structure(bars, 1)['lows'] == 'HL'
    inverse = [Candle(b.time, 30-b.open, 30-b.low, 30-b.high, 30-b.close) for b in bars]
    assert structure(inverse, 1)['trend'] == 'bearish'
    assert structure(inverse, 1)['highs'] == 'LH'
    assert structure(inverse, 1)['lows'] == 'LL'
    assert structure(candles(), 1)['trend'] == 'range'


def setup_bars():
    # Two rising highs/lows, a close above 115, then bullish wick rejection.
    prices = [100, 105, 101, 110, 104, 114, 108, 110, 113]
    bars = [Candle(i*900, p, p+1, p-1, p) for i, p in enumerate(prices)]
    bars += [Candle(8100, 114, 119, 113, 118), Candle(9000, 116, 119, 114, 118)]
    return bars


@pytest.mark.parametrize('inverse,expected', [(False, 'BUY'), (True, 'SELL')])
def test_bos_retest_rejection_plan(inverse, expected):
    from trad_auto.core import analyze
    bars = setup_bars()
    if inverse:
        bars = [Candle(b.time, 250-b.open, 250-b.low, 250-b.high, 250-b.close) for b in bars]
    result = analyze(bars, Config(timeframe='M15', pivot=1, rr=2), now=9900, bid=117.8, ask=118, tick_time=9900)
    assert result['action'] == expected
    assert result['execution_enabled'] is False
    assert result['bos']['index'] == 9
    assert result['rr'] == 2
    assert abs(result['target']-result['entry']) == pytest.approx(2*abs(result['entry']-result['stop']))


@pytest.mark.parametrize('case', ['flat', 'stale', 'spread', 'tick_stale', 'tick_future', 'quote_nan', 'crossed', 'no_retest', 'htf_conflict'])
def test_analysis_fail_closed(case):
    from trad_auto.core import analyze
    bars = setup_bars()
    kwargs = dict(now=9900, bid=117.8, ask=118, tick_time=9900)
    if case == 'flat': bars = candles()
    if case == 'stale': kwargs['now'] = 20000
    if case == 'spread': kwargs['ask'] = 122
    if case == 'tick_stale': kwargs['tick_time'] = 9000
    if case == 'tick_future': kwargs['tick_time'] = 9903
    if case == 'quote_nan': kwargs['bid'] = float('nan')
    if case == 'crossed': kwargs['bid'] = 120
    if case == 'no_retest': bars[-1] = Candle(9000, 118, 121, 117, 120)
    if case == 'htf_conflict': kwargs['higher_trend'] = 'bearish'
    result = analyze(bars, Config(timeframe='M15', pivot=1), **kwargs)
    assert result['action'] == 'WAIT'
    assert result['reason']
    assert 'entry' not in result


def test_replay_prefix_invariance_and_counts():
    from trad_auto.core import replay
    bars = setup_bars()
    cfg = Config(timeframe='M15', pivot=1)
    before = replay(bars, cfg)
    extended = bars + [Candle(9900, 118, 120, 114, 119), Candle(10800, 119, 125, 118, 124)]
    after = replay(extended, cfg)
    assert before['counts'] == {'BUY': 1, 'SELL': 0}
    assert before['setups'] == [s for s in after['setups'] if s['asof'] <= 9900]
    assert before['spread_checked'] is False
    assert before['profitability_evaluated'] is False
    assert before['execution_enabled'] is False
    assert len({(s['action'], s['bos']['time']) for s in after['setups']}) == len(after['setups'])
    with pytest.raises(ValueError):
        replay([*bars, bars[-1]], cfg)


def test_replay_higher_timeframe_uses_only_closed_prefix():
    from trad_auto.core import replay
    bars = setup_bars()
    # Future H1 candles cannot supply trend to a past M15 setup.
    future = [Candle(40000+i*3600, 100+i, 102+i, 98+i, 101+i) for i in range(10)]
    assert replay(bars, Config(timeframe='M15', pivot=1), higher_bars=future)['counts'] == {'BUY': 0, 'SELL': 0}


def test_valid_closed_data():
    assert validate(candles(), Config(timeframe='M15'), now=9000) is None


@pytest.mark.parametrize('field,value', [('rr', 0), ('rr', float('nan')), ('pivot', 0), ('max_spread', -1), ('symbol', ''), ('timeframe', 'M7')])
def test_bad_config(field, value):
    with pytest.raises(ValueError):
        Config(**{field: value})


@pytest.mark.parametrize('kind', ['nan', 'negative', 'envelope', 'duplicate', 'unsorted', 'forming', 'stale', 'short'])
def test_bad_data(kind):
    data = candles()
    if kind == 'nan': data[-1] = Candle(8100, 100, float('nan'), 98, 101)
    if kind == 'negative': data[-1] = Candle(8100, 100, 102, -1, 101)
    if kind == 'envelope': data[-1] = Candle(8100, 105, 102, 98, 101)
    if kind == 'duplicate': data[-1] = data[-2]
    if kind == 'unsorted': data.reverse()
    if kind == 'forming': data[-1] = Candle(9000, 100, 102, 98, 101)
    if kind == 'short': data = data[:2]
    with pytest.raises(ValueError):
        validate(data, Config(timeframe='M15'), now=12000 if kind == 'stale' else 9000)
