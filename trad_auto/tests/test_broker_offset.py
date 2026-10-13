from types import SimpleNamespace as NS
import pytest
from test_provider import FakeMT5
from test_live_execution import LiveAPI
from test_execution import PLAN


def test_provider_explicit_offset_normalizes_bars_and_quote():
    from trad_auto.provider import MT5Provider
    api = FakeMT5()
    api.rows = [dict(time=11700, open=100, high=102, low=99, close=101)]
    with MT5Provider(api, broker_utc_offset_hours=3) as provider:
        assert provider.candles('GOLD', 'M15', 10, now=2000)[0].time == 900
        assert provider.quote('GOLD')['tick_time'] == -8900


def test_subsecond_clock_skew_is_not_mistaken_for_future_tick():
    from trad_auto.core import Config, quote_check
    quote_check(Config(symbol='GOLD'), 9900.25, 101., 101.2, 9901)
    with pytest.raises(ValueError, match='future tick'):
        quote_check(Config(symbol='GOLD'), 9900.25, 101., 101.2, 9903)


def test_live_subsecond_skew_is_accepted_but_larger_future_tick_is_not(tmp_path):
    from trad_auto.execution import execute_live_order
    api = LiveAPI()
    api.copy_rates_from_pos = lambda *args: [dict(time=20700)]
    api.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.2, time=20701)
    kwargs = dict(symbol='GOLD', timeframe='M5', plan=PLAN, now=9900.25,
                  db_path=tmp_path/'db', daily_loss_limit_usd=30, broker_utc_offset_hours=3)
    assert execute_live_order(api, **kwargs)['state'] == 'filled'
    api2 = LiveAPI()
    api2.copy_rates_from_pos = api.copy_rates_from_pos
    api2.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.2, time=20703)
    with pytest.raises(ValueError, match='quote'):
        execute_live_order(api2, **{**kwargs, 'db_path': tmp_path/'other'})
    assert not api2.sends


def test_demo_explicit_offset_uses_normalized_execution_tick(tmp_path):
    from trad_auto.execution import execute_demo_order
    from test_execution import FakeAPI
    api = FakeAPI()
    api.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.2, time=20700)
    result = execute_demo_order(api, symbol='GOLD', timeframe='M5', plan=PLAN,
                                now=9900, db_path=tmp_path/'db', broker_utc_offset_hours=3)
    assert result['state'] == 'filled'
    assert api.sends[0]['volume'] == 0.01


def test_live_requires_explicit_offset(tmp_path):
    from trad_auto.execution import execute_live_order
    api = LiveAPI()
    with pytest.raises(ValueError, match='offset'):
        execute_live_order(api, symbol='GOLD', timeframe='M5', plan=PLAN,
                           now=9900, db_path=tmp_path/'db', daily_loss_limit_usd=30)
    assert not api.sends


@pytest.mark.parametrize('tick_time, bar_time, message', [
    (20700, 20700, None), (20000, 20700, 'quote'),
    (20700, 20400, 'forming bar'), (9900, 9900, 'forming bar'),
])
def test_live_offset_freshness_and_bar_consistency(tmp_path, tick_time, bar_time, message):
    from trad_auto.execution import execute_live_order
    api = LiveAPI()
    api.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.2, time=tick_time)
    api.copy_rates_from_pos = lambda *args: [dict(time=bar_time)]
    kwargs = dict(symbol='GOLD', timeframe='M5', plan=PLAN, now=9900,
                  db_path=tmp_path/'db', daily_loss_limit_usd=30, broker_utc_offset_hours=3)
    if message:
        with pytest.raises(ValueError, match=message):
            execute_live_order(api, **kwargs)
        assert not api.sends
    else:
        assert execute_live_order(api, **kwargs)['state'] == 'filled'


def test_history_window_uses_utc_day_shifted_to_broker_clock(tmp_path):
    from datetime import datetime, timezone
    from trad_auto.execution import execute_live_order
    api = LiveAPI()
    now = datetime(2026, 10, 13, 10, 58, tzinfo=timezone.utc).timestamp()
    raw = int(now) + 10800
    api.symbol_info_tick = lambda symbol: NS(bid=101., ask=101.2, time=raw)
    api.copy_rates_from_pos = lambda *args: [dict(time=raw - raw % 300)]
    windows = []
    original = api.history_deals_get
    def history(*args, **kwargs):
        if args: windows.append(args)
        return original(*args, **kwargs)
    api.history_deals_get = history
    plan = {**PLAN, 'asof': int(now) - int(now) % 300}
    execute_live_order(api, symbol='GOLD', timeframe='M5', plan=plan, now=now,
                       db_path=tmp_path/'db', daily_loss_limit_usd=30, broker_utc_offset_hours=3)
    assert windows
    assert all(start == datetime(2026, 10, 13, 3, tzinfo=timezone.utc)
               and end == datetime.fromtimestamp(now + 10800, timezone.utc)
               for start, end in windows)


def test_server_switch_after_check_blocks_send(tmp_path):
    from trad_auto.execution import execute_live_order
    api = LiveAPI()
    def change(request):
        api.server = 'other-server'
        return NS(retcode=0)
    api.order_check = change
    with pytest.raises(ValueError, match='account'):
        execute_live_order(api, symbol='GOLD', timeframe='M5', plan=PLAN,
                           now=9900, db_path=tmp_path/'db', daily_loss_limit_usd=30,
                           broker_utc_offset_hours=0)
    assert not api.sends
