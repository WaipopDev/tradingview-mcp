"""Collect only this isolated run's evidence; never read the user's logs."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
from prepare_isolated import ISOLATED, ROOT

artifacts = ROOT/'artifacts'
artifacts.mkdir(exist_ok=True)
for source, name in [(ISOLATED/'logs/20261011.log','terminal-20261011.log'), (ISOLATED/'Tester/logs/20261011.log','tester-20261011.log'), (ROOT/'NakedChartTester.log','compile.log')]:
    shutil.copy2(source,artifacts/name)
terminal = (artifacts/'terminal-20261011.log').read_text(encoding='utf-16')
tester = (artifacts/'tester-20261011.log').read_text(encoding='utf-16')
assert 'tester not started because the account is not specified' in tester
assert '0 errors, 0 warnings' in (artifacts/'compile.log').read_text(encoding='utf-16')
reports = list((ISOLATED/'reports').glob('*'))
assert not reports, 'New reports require fresh parsing, not blocked-run summary'
result = subprocess.run([str(ROOT.parents[1]/'.venv/Scripts/python.exe'),'-m','pytest','trad_auto/tests','trad_auto/mql5/test_port.py','-q'],cwd=ROOT.parents[1],capture_output=True,text=True)
(artifacts/'pytest.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
assert result.returncode == 0
summary = {
    'status':'blocked_before_tester_start',
    'blocker':'tester not started because the account is not specified',
    'compiled':True,'compiler_errors':0,'compiler_warnings':0,
    'terminal_build':6230,'terminal_exit_code_signed':-1000012353,
    'requested':{'symbol':'GOLD','period':'M5','higher_timeframe':'H1','from_date':'2026.09.11','to_date':'2026.10.11','date_convention':'start midnight inclusive, end midnight exclusive; broker/tester time; not runtime-verified','model':4,'deposit':100,'currency':'USD','leverage':'1:1000','risk_equity_percent':1,'rr':1,'max_spread_price_units':1.0,'pivot':2,'retest_bars':4,'lookback_bars':260,'optimization':False},
    'raw_report_exists':False,
    'metrics':dict.fromkeys(['actual_from','actual_to','modeling_quality','ticks','bars','trades','net_profit','ending_balance','profit_factor','max_drawdown','winrate','commission','swap','fees','risk_skipped']),
    'mql_selftests':{'synthetic_fixtures':169,'compiled':True,'executed':False,'failures':None},
    'python_tests':{'exit_code':result.returncode,'output':result.stdout.strip()},
    'credentials_copied':False,
    'live_terminal_modified':False,
    'live_orders_submitted':False,
    'next_requirement':'User-authenticated isolated broker session; do not copy credentials/configuration from the main terminal.',
    'artifacts':{},
}
for p in [ROOT/'NakedChartTester.ex5',ROOT/'NakedChartTester.mq5',ROOT/'NakedCore.mqh',ROOT/'CoreSelfTest.mqh',artifacts/'compile.log',artifacts/'terminal-20261011.log',artifacts/'tester-20261011.log']:
    summary['artifacts'][str(p.relative_to(ROOT))]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(artifacts/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
