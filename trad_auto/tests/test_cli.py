import json
import pytest
from test_core import setup_bars
from trad_auto.core import Candle


class Provider:
    def __init__(self, fail=None): self.fail, self.closed = fail, False
    def __enter__(self): return self
    def __exit__(self, *args): self.closed = True
    def status(self):
        return {'connected': self.fail != 'disconnected', 'terminal_trade_allowed': False, 'execution_enabled': False}
    def candles(self, symbol, timeframe, count, *, now):
        assert symbol == 'GOLD'
        if self.fail == 'provider': raise RuntimeError('secret account 12345')
        if timeframe == 'H1':
            return [Candle(i*3600, 100, 102, 99, 101) for i in range(10)]
        return setup_bars()
    def quote(self, symbol):
        return {'bid': 117.8, 'ask': 118, 'tick_time': 9000 if self.fail == 'stale' else 9900}


def run(capsys, args, provider):
    from trad_auto.cli import main
    # These legacy fixtures contain M15 candles; defaults are tested separately.
    code = main([*args, '--timeframe', 'M15'], provider_factory=lambda: provider, clock=lambda: 9900)
    return code, json.loads(capsys.readouterr().out)


@pytest.mark.parametrize('command', ['doctor', 'analyze', 'replay'])
def test_cli_injected_real_core(capsys, command):
    provider = Provider()
    code, result = run(capsys, [command, '--symbol', 'GOLD', '--pivot', '1', '--no-htf'], provider)
    assert code == 0
    assert result['execution_enabled'] is False
    if command == 'analyze': assert result['action'] == 'BUY'
    if command == 'doctor':
        assert result['connected'] and result['fresh'] and result['data_ready']
    if command == 'replay': assert result['counts']['BUY'] == 1
    assert provider.closed


@pytest.mark.parametrize('failure', ['provider', 'stale', 'disconnected'])
def test_cli_doctor_separates_connection_readiness(capsys, failure):
    provider = Provider(failure)
    code, result = run(capsys, ['doctor', '--symbol', 'GOLD', '--no-htf'], provider)
    assert code == 2
    assert result['connected'] is (failure != 'disconnected')
    assert result['data_ready'] is False
    assert result['execution_enabled'] is False
    assert '12345' not in str(result)
    assert provider.closed


@pytest.mark.parametrize('args', [['analyze', '--rr', 'nan'], ['oops'], ['analyze', '--bars', '0'], ['analyze', '--pivot', 'x']])
def test_cli_invalid_args_json(capsys, args):
    code, result = run(capsys, args, Provider())
    assert code == 2
    assert result['action'] == 'WAIT'


def test_module_entrypoint_json_failure():
    import os
    import subprocess
    import sys
    from pathlib import Path
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[1] / 'src')
    completed = subprocess.run([sys.executable, '-m', 'trad_auto', 'analyze', '--rr', '0'], capture_output=True, text=True, env=env)
    assert completed.returncode == 2
    assert json.loads(completed.stdout)['action'] == 'WAIT'
    assert completed.stderr == ''


def test_provider_valueerror_never_leaks(capsys):
    class UnsafeProvider(Provider):
        def candles(self, *args, **kwargs):
            raise ValueError('private account 12345')
    code, result = run(capsys, ['doctor', '--symbol', 'GOLD'], UnsafeProvider())
    assert code == 2
    assert '12345' not in str(result)


def test_cleanup_failure_returns_nonzero_wait_without_plan(capsys):
    class BrokenCleanup(Provider):
        def __exit__(self, *args):
            raise RuntimeError('private 12345')
    code, result = run(capsys, ['analyze', '--symbol', 'GOLD', '--pivot', '1', '--no-htf'], BrokenCleanup())
    assert code == 2
    assert result['action'] == 'WAIT'
    assert 'entry' not in result
    assert '12345' not in str(result)


def test_cli_required_htf_failure_blocks_plan(capsys):
    code, result = run(capsys, ['analyze', '--symbol', 'GOLD', '--pivot', '1'], Provider())
    assert code == 2
    assert result['action'] == 'WAIT'
    assert result['data_ready'] is False


def test_manual_demo_execution_records_verified_deal(capsys, tmp_path):
    from test_execution import FakeAPI
    api = FakeAPI()
    api.symbol_info_tick = lambda symbol: type('Tick', (), {'bid': 117.8, 'ask': 118., 'time': 9900})()
    class DemoProvider(Provider):
        def __init__(self):
            super().__init__()
            self.api = api
    from trad_auto.cli import main
    path = tmp_path / 'ledger.sqlite3'
    code = main(['execute-demo', '--symbol', 'GOLD', '--pivot', '1', '--no-htf',
                 '--timeframe', 'M15', '--db-path', str(path)],
                provider_factory=DemoProvider, clock=lambda: 9900)
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result['execution_enabled'] is True
    assert result['execution']['state'] == 'filled'
    assert path.is_file()
    assert len(api.sends) == 1


def test_sync_manual_cli_does_not_require_fresh_market_data(capsys, tmp_path):
    from test_manual_sync import FakeAPI
    api = FakeAPI()
    class HistoryProvider:
        def __enter__(self):
            self.api = api
            return self
        def __exit__(self, *args):
            pass
        def candles(self, *args, **kwargs):
            raise AssertionError('sync must not fetch candles')
    from trad_auto.cli import main
    db = tmp_path / 'ledger.sqlite3'
    code = main(['sync-manual', '--db-path', str(db), '--since-utc',
                 '1970-01-01T00:25:00Z'], provider_factory=HistoryProvider, clock=lambda: 3000)
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result['manual_sync']['new_orders'] == 1
    assert result['manual_sync']['new_deals'] == 1
    assert result['execution_enabled'] is False


def test_demo_execution_never_submits_to_live_account(capsys, tmp_path):
    from test_execution import FakeAPI
    api = FakeAPI(demo=False)
    class LiveProvider(Provider):
        def __init__(self):
            super().__init__()
            self.api = api
    from trad_auto.cli import main
    code = main(['execute-demo', '--symbol', 'GOLD', '--pivot', '1', '--no-htf',
                 '--timeframe', 'M15', '--db-path', str(tmp_path / 'ledger.sqlite3')],
                provider_factory=LiveProvider, clock=lambda: 9900)
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result['execution_enabled'] is False
    assert not api.sends
