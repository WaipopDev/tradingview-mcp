from dataclasses import replace
import json

import pytest

from test_core import setup_bars
from test_cli import Provider
from trad_auto.core import Candle, Config, analyze
from trad_auto.cli import main


def scalp_bars(inverse=False):
    bars = [replace(b, time=i * 300) for i, b in enumerate(setup_bars())]
    if inverse:
        bars = [Candle(b.time, 250-b.open, 250-b.low, 250-b.high, 250-b.close) for b in bars]
    return bars


@pytest.mark.parametrize('inverse,side', [(False, 'BUY'), (True, 'SELL')])
def test_scalping_defaults_equal_stop_target_distance(inverse, side):
    config = Config(pivot=1)
    assert config.timeframe == 'M5'
    assert config.rr == 1.0
    result = analyze(scalp_bars(inverse), config, now=3300, bid=117.8, ask=118, tick_time=3300)
    assert result['action'] == side
    assert result['rr'] == 1.0
    assert abs(result['target'] - result['entry']) == pytest.approx(abs(result['entry'] - result['stop']))
    assert result['execution_enabled'] is False


@pytest.mark.parametrize('override,expected_rr', [([], 1.0), (['--rr', '2'], 2.0)])
def test_cli_scalping_default_and_rr_override(capsys, override, expected_rr):
    class ScalpProvider(Provider):
        def candles(self, symbol, timeframe, count, *, now):
            assert timeframe == 'M5'
            return scalp_bars()

        def quote(self, symbol):
            return {'bid': 117.8, 'ask': 118, 'tick_time': 3300}

    code = main(['analyze', '--symbol', 'GOLD', '--pivot', '1', '--no-htf', *override],
                provider_factory=ScalpProvider, clock=lambda: 3300)
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result['timeframe'] == 'M5'
    assert result['action'] == 'BUY'
    assert result['rr'] == expected_rr
    assert abs(result['target'] - result['entry']) == pytest.approx(expected_rr * abs(result['entry'] - result['stop']))
    assert result['execution_enabled'] is False
