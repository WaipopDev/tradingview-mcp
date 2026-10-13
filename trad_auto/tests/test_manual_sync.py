import sqlite3
from types import SimpleNamespace as NS

import pytest
from trad_auto.manual_sync import sync_manual_orders


class FakeAPI:
    ORDER_REASON_CLIENT = 0
    ORDER_REASON_MOBILE = 1
    ORDER_REASON_WEB = 2
    DEAL_REASON_CLIENT = 0
    DEAL_REASON_MOBILE = 1
    DEAL_REASON_WEB = 2

    def __init__(self):
        self.orders = [NS(ticket=11, reason=0, magic=0, time_setup=2000, time_done=2002,
                          symbol='GOLD', type=0, state=4, volume_initial=0.01,
                          volume_current=0., price_open=4000., sl=3990., tp=4010., position_id=31),
                       NS(ticket=12, reason=3, magic=20261012, time_setup=2000)]
        self.deals = [NS(ticket=21, order=11, reason=0, magic=0, entry=0,
                         time=2002, symbol='GOLD', type=0, volume=0.01, price=4000.5,
                         position_id=31, profit=0., commission=-0.1, swap=0.),
                      NS(ticket=22, order=12, reason=3, magic=20261012, entry=0, time=2002)]
        self.mode = 2
        self.login = 9876
        self.last_range = None

    def account_info(self):
        return NS(login=self.login, trade_mode=self.mode)

    def symbol_info_tick(self, symbol):
        return NS(time=3000)

    def history_orders_get(self, start, end):
        self.last_range = (start, end)
        return self.orders

    def history_deals_get(self, start, end):
        return self.deals


def test_sync_manual_orders_from_cutoff_idempotently(tmp_path):
    api = FakeAPI()
    db = tmp_path / 'ledger.sqlite3'
    first = sync_manual_orders(api, db_path=db, now=3000, initial_since=1500)
    second = sync_manual_orders(api, db_path=db, now=3100)
    assert first['new_orders'] == 1 and first['new_deals'] == 1
    assert second['new_orders'] == 0 and second['new_deals'] == 0
    assert first['since'] == second['since'] == 1500
    assert api.last_range[0].utcoffset().total_seconds() == 0
    with sqlite3.connect(db) as conn:
        row = conn.execute('SELECT ticket, symbol, volume_initial, price_open FROM manual_orders').fetchone()
        deal = conn.execute('SELECT ticket, order_ticket, price FROM manual_deals').fetchone()
    assert row == (11, 'GOLD', 0.01, 4000.)
    assert deal == (21, 11, 4000.5)


def test_sync_never_sends_and_keeps_accounts_separate(tmp_path):
    api = FakeAPI()
    db = tmp_path / 'ledger.sqlite3'
    sync_manual_orders(api, db_path=db, now=3000, initial_since=1500)
    api.login = 9877
    result = sync_manual_orders(api, db_path=db, now=3100, initial_since=1500)
    assert result['new_orders'] == 1
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM manual_orders').fetchone()[0] == 2


def test_history_failure_does_not_advance_cutoff_or_store_partial_data(tmp_path):
    api = FakeAPI()
    api.history_deals_get = lambda *args: None
    db = tmp_path / 'ledger.sqlite3'
    with pytest.raises(ValueError, match='history'):
        sync_manual_orders(api, db_path=db, now=3000, initial_since=1500)
    with sqlite3.connect(db) as conn:
        assert conn.execute('SELECT COUNT(*) FROM manual_orders').fetchone()[0] == 0


def test_broker_clock_ahead_syncs_entries_by_physical_cutoff(tmp_path):
    api = FakeAPI()
    api.symbol_info_tick = lambda symbol: NS(time=13800)  # broker records +3h
    api.orders[0].time_setup = 12800
    api.deals[0].time = 12802
    result = sync_manual_orders(api, db_path=tmp_path / 'ledger.sqlite3',
                                now=3000, initial_since=1500)
    assert result['new_orders'] == result['new_deals'] == 1
    assert result['broker_offset_seconds'] == 10800
    assert int(api.last_range[1].timestamp()) == 13800


def test_only_entries_at_or_after_cutoff(tmp_path):
    api = FakeAPI()
    api.orders.append(NS(ticket=13, reason=0, magic=0, time_setup=1499))
    api.deals.append(NS(ticket=23, reason=0, magic=0, time=1499))
    result = sync_manual_orders(api, db_path=tmp_path / 'ledger.sqlite3', now=3000, initial_since=1500)
    assert result['new_orders'] == result['new_deals'] == 1
