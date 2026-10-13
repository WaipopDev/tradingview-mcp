"""Official MetaTrader5 adapter. Only connection and market-data reads."""
from .core import Candle, SECONDS
from .broker_time import offset_seconds


class ProviderError(RuntimeError):
    pass


class MT5Provider:
    def __init__(self, api=None, *, broker_utc_offset_hours=0):
        self.api = api
        self.offset = offset_seconds(broker_utc_offset_hours)

    def __enter__(self):
        if self.api is None:
            try:
                import MetaTrader5
            except ImportError:
                raise ProviderError('install the mt5 extra on Windows') from None
            self.api = MetaTrader5
        try:
            if not self.api.initialize():
                raise ProviderError('MT5 initialization failed')
        except Exception:
            self.api.shutdown()
            raise ProviderError('MT5 initialization failed') from None
        return self

    def __exit__(self, *args):
        self.api.shutdown()

    def status(self):
        info = self.api.terminal_info()
        return {'connected': bool(info and info.connected),
                'terminal_trade_allowed': bool(info and info.trade_allowed),
                'execution_enabled': False}

    def _symbol(self, symbol):
        if not self.status()['connected']:
            raise ProviderError('MT5 not connected')
        info = self.api.symbol_info(symbol)
        if info is None or info.name != symbol:
            raise ProviderError('exact symbol not available; specify broker symbol explicitly')
        if not info.visible:
            raise ProviderError('symbol not visible; add it manually in Market Watch')

    def candles(self, symbol, timeframe, count, *, now):
        self._symbol(symbol)
        if timeframe not in SECONDS or type(count) is not int or not 10 <= count <= 5000:
            raise ProviderError('invalid timeframe or candle count (10..5000)')
        rows = self.api.copy_rates_from_pos(symbol, getattr(self.api, 'TIMEFRAME_'+timeframe), 1, count)
        if rows is None or len(rows) == 0:
            raise ProviderError('closed candle data unavailable')
        # Keep original ordering: malformed provider ordering must fail validation.
        bars = [Candle(int(r['time']) - self.offset, float(r['open']), float(r['high']), float(r['low']), float(r['close'])) for r in rows]
        return [b for b in bars if b.time + SECONDS[timeframe] <= now]

    def quote(self, symbol):
        self._symbol(symbol)
        tick = self.api.symbol_info_tick(symbol)
        if tick is None:
            raise ProviderError('tick unavailable')
        return {'bid': float(tick.bid), 'ask': float(tick.ask), 'tick_time': int(tick.time) - self.offset}
