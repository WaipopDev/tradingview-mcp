import sqlite3
from types import SimpleNamespace as NS

import pytest

from trad_auto.execution import execute_demo_order


class FakeAPI:
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    TRADE_ACTION_DEAL = 1
    ORDER_TIME_GTC = 0
    ORDER_FILLING_IOC = 1
    TRADE_RETCODE_DONE = 10009

    def __init__(self, *, demo=True):
        self.sends = []
        self.demo = demo
        self.positions = []
        self.result = NS(retcode=10009, order=42, deal=43, price=101.2, volume=0.01)

    def account_info(self):
        return NS(trade_mode=0 if self.demo else 2, trade_allowed=True, trade_expert=True)

    def terminal_info(self):
        return NS(connected=True, trade_allowed=True, tradeapi_disabled=False)

    def symbol_info(self, symbol):
        return NS(name='GOLD', visible=True, trade_mode=4, volume_min=0.01, volume_step=0.01,
                  volume_max=100., digits=2, point=0.01, trade_stops_level=5,
                  filling_mode=2, trade_tick_size=0.01)

    def symbol_info_tick(self, symbol):
        return NS(bid=101., ask=101.2, time=9900)

    def positions_get(self, symbol):
        return self.positions

    def order_check(self, request):
        return NS(retcode=0)

    def order_send(self, request):
        self.sends.append(request)
        return self.result

    def history_deals_get(self, *args, **kwargs):
        return [NS(ticket=43, order=42, symbol='GOLD', volume=0.01, price=101.25)]


PLAN = {'action': 'BUY', 'entry': 101., 'stop': 99., 'target': 103., 'rr': 1., 'asof': 9700,
        'bos': {'time': 9000}, 'data_ready': True}


def call(api, path, plan=PLAN):
    return execute_demo_order(api, symbol='GOLD', timeframe='M5', plan=plan,
                              now=9900, db_path=path)


def test_demo_order_is_verified_and_recorded(tmp_path):
    api = FakeAPI()
    db = tmp_path / 'orders.sqlite3'
    result = call(api, db)
    assert result['state'] == 'filled'
    assert result['order'] == 42
    assert result['filled_price'] == 101.25
    assert len(api.sends) == 1
    request = api.sends[0]
    assert request['volume'] == 0.01
    assert request['price'] == 101.2
    assert request['sl'] == 99.
    assert request['tp'] == 103.4  # RR recalculated from executable quote
    with sqlite3.connect(db) as conn:
        row = conn.execute('SELECT state, order_ticket, deal_ticket, volume, symbol, filled_price FROM orders').fetchone()
    assert row == ('filled', 42, 43, 0.01, 'GOLD', 101.25)


def test_live_account_never_sends_or_creates_order(tmp_path):
    api = FakeAPI(demo=False)
    with pytest.raises(ValueError, match='demo'):
        call(api, tmp_path / 'orders.sqlite3')
    assert not api.sends


def test_repeat_signal_does_not_submit_twice(tmp_path):
    api = FakeAPI()
    path = tmp_path / 'orders.sqlite3'
    call(api, path)
    with pytest.raises(ValueError, match='already'):
        call(api, path)
    assert len(api.sends) == 1


def test_existing_position_blocks_order(tmp_path):
    api = FakeAPI()
    api.positions = [NS(ticket=99)]
    with pytest.raises(ValueError, match='position'):
        call(api, tmp_path / 'orders.sqlite3')
    assert not api.sends


def test_ambiguous_send_remains_pending_for_manual_reconciliation(tmp_path):
    api = FakeAPI()
    api.order_send = lambda request: None
    path = tmp_path / 'orders.sqlite3'
    with pytest.raises(ValueError, match='uncertain'):
        call(api, path)
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT state FROM orders').fetchone()[0] == 'pending'
    with pytest.raises(ValueError, match='already'):
        call(api, path)


def test_pending_order_blocks_different_signal_too(tmp_path):
    api = FakeAPI()
    api.order_send = lambda request: None
    path = tmp_path / 'orders.sqlite3'
    with pytest.raises(ValueError, match='uncertain'):
        call(api, path)
    with pytest.raises(ValueError, match='pending'):
        call(api, path, {**PLAN, 'bos': {'time': 9300}})
    with sqlite3.connect(path) as conn:
        assert conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0] == 1


def test_order_check_rejection_no_send(tmp_path):
    api = FakeAPI()
    api.order_check = lambda request: NS(retcode=10016)
    with pytest.raises(ValueError, match='check'):
        call(api, tmp_path / 'orders.sqlite3')
    assert not api.sends


def test_account_switch_during_order_check_blocks_send(tmp_path):
    api = FakeAPI()
    def switch(request):
        api.demo = False
        return NS(retcode=0)
    api.order_check = switch
    with pytest.raises(ValueError, match='demo'):
        call(api, tmp_path / 'orders.sqlite3')
    assert not api.sends


def test_stale_plan_and_no_stop_fail_closed(tmp_path):
    api = FakeAPI()
    with pytest.raises(ValueError, match='stale'):
        call(api, tmp_path / 'orders.sqlite3', {**PLAN, 'asof': 9300})
    with pytest.raises(ValueError, match='stop'):
        call(api, tmp_path / 'orders.sqlite3', {**PLAN, 'stop': 102.})
    assert not api.sends
