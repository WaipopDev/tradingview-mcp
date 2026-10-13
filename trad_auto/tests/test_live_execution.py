from types import SimpleNamespace as NS
import pytest
from test_execution import FakeAPI, PLAN
from trad_auto.execution import execute_live_order
from trad_auto.cli import main

def test_live_command_requires_explicit_limit(capsys):
    assert main(['execute-live', '--symbol', 'GOLD']) == 2
    assert 'daily-loss-limit-usd' in capsys.readouterr().out

class LiveAPI(FakeAPI):
    def __init__(self):
        super().__init__(demo=False)
        self.login = 123
        self.server = 'test-server'
        self.deals = []
        self.all_positions = []
        self.profit = -10.
        self.history_available = True
    def account_info(self):
        return NS(trade_mode=2, login=self.login, server=self.server, currency='USD', trade_allowed=True, trade_expert=True)
    TIMEFRAME_M5 = 5
    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        assert start == 0 and count == 1
        return [dict(time=9900)]
    def history_deals_get(self, *args, **kwargs):
        if args:
            return self.deals if self.history_available else None
        return super().history_deals_get(*args, **kwargs)
    def positions_get(self, symbol=None):
        return self.positions if symbol else self.all_positions
    def order_calc_profit(self, side, symbol, volume, entry, exit_price):
        return self.profit

def call(api, path, limit=30):
    return execute_live_order(api, symbol='GOLD', timeframe='M5', plan=PLAN,
                              now=9900, db_path=path, daily_loss_limit_usd=limit,
                              broker_utc_offset_hours=0)

def test_live_sends_exact_volume_and_stops(tmp_path):
    api = LiveAPI()
    result = call(api, tmp_path/'db')
    assert result['state'] == 'filled'
    assert len(api.sends) == 1
    assert api.sends[0]['volume'] == .01
    assert api.sends[0]['sl'] and api.sends[0]['tp']

def test_realized_costs_and_open_risk_block(tmp_path):
    api = LiveAPI()
    api.deals = [NS(profit=-10, commission=-2, swap=-1, fee=-1)]
    api.all_positions = [NS(symbol='OTHER', type=0, volume=.01, price_open=100, sl=90)]
    with pytest.raises(ValueError, match='daily loss'):
        call(api, tmp_path/'db')
    assert not api.sends

def test_unavailable_history_and_currency_fail_closed(tmp_path):
    api = LiveAPI()
    api.history_available = False
    with pytest.raises(ValueError, match='history'):
        call(api, tmp_path/'db')
    api.history_available = True
    api.account_info = lambda: NS(trade_mode=2, login=123, server='test-server', currency='EUR', trade_allowed=True, trade_expert=True)
    with pytest.raises(ValueError, match='USD'):
        call(api, tmp_path/'db')
    assert not api.sends

def test_quote_switch_at_check_blocks_send(tmp_path):
    api = LiveAPI()
    def switch(request):
        api.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.3, time=9900)
        return NS(retcode=0)
    api.order_check = switch
    with pytest.raises(ValueError, match='quote'):
        call(api, tmp_path/'db')
    assert not api.sends

def test_account_switch_at_check_blocks_send(tmp_path):
    api = LiveAPI()
    def switch(request):
        api.login = 456
        return NS(retcode=0)
    api.order_check = switch
    with pytest.raises(ValueError, match='account'):
        call(api, tmp_path/'db')
    assert not api.sends
