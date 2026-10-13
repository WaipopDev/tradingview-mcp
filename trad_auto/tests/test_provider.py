from types import SimpleNamespace as NS
import pytest


class FakeMT5:
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 60
    def __init__(self):
        self.closed = False
        self.start = None
        self.connected = True
        self.visible = True
        self.rows = [dict(time=900, open=100, high=102, low=99, close=101),
                     dict(time=1800, open=101, high=103, low=100, close=102)]
    def initialize(self): return True
    def shutdown(self): self.closed = True
    def terminal_info(self): return NS(connected=self.connected, trade_allowed=False)
    def symbol_info(self, symbol):
        return NS(name='GOLD', visible=self.visible) if symbol == 'GOLD' else None
    def symbol_info_tick(self, symbol): return NS(time=1900, bid=101, ask=101.2)
    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        self.start = start
        return self.rows


def test_read_only_provider_exact_symbol_closed_bars_and_shutdown():
    from trad_auto.provider import MT5Provider, ProviderError
    api = FakeMT5()
    with MT5Provider(api) as provider:
        assert provider.status() == {'connected': True, 'terminal_trade_allowed': False, 'execution_enabled': False}
        with pytest.raises(ProviderError, match='exact symbol'):
            provider.candles('XAUUSD', 'M15', 100, now=2000)
        bars = provider.candles('GOLD', 'M15', 100, now=2000)
        assert [b.time for b in bars] == [900]
        assert api.start == 1
        assert provider.quote('GOLD') == {'bid': 101., 'ask': 101.2, 'tick_time': 1900}
    assert api.closed


@pytest.mark.parametrize('failure', ['initialize', 'disconnected', 'hidden', 'rates', 'tick'])
def test_provider_failure_is_sanitized_and_closes(failure):
    from trad_auto.provider import MT5Provider, ProviderError
    api = FakeMT5()
    if failure == 'initialize': api.initialize = lambda: False
    if failure == 'disconnected': api.connected = False
    if failure == 'hidden': api.visible = False
    if failure == 'rates': api.rows = None
    if failure == 'tick': api.symbol_info_tick = lambda _: None
    with pytest.raises(ProviderError):
        with MT5Provider(api) as provider:
            provider.candles('GOLD', 'M15', 100, now=2000)
            provider.quote('GOLD')
    assert api.closed
