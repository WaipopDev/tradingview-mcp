"""Run the fixed tester-only experiment inside the user's authenticated terminal.

The portable copy cannot run a broker-backed test (no account), and credentials
must never be copied, so the tester is started in the user's already-run
terminal via a read-only startup config. That terminal is the only place a
simulated (never live) account context exists.

Safety: tester-only EA (hard MQL_TESTER guards), AllowLiveTrading=0, Enabled=0,
ShutdownTerminal=0 so the user's terminal is never closed. Adds only the EA
files under MQL5/Experts plus a report; no config/account file is read or written.
"""
from pathlib import Path
import json
import subprocess
import sys
import time

DATA = Path('C:/Users/waipo/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075')
INSTALL = Path('C:/Program Files/MetaTrader 5')
ROOT = Path(__file__).resolve().parent
LIVE = ROOT / 'live'
EXPERT = DATA / 'MQL5/Experts/NakedChartTester.ex5'
SUMMARY = DATA / 'MQL5/Files/NakedChartTester-summary.json'
REPORT = DATA / 'reports/NakedChartTester-20260911-20261011.html'
SOURCES = ('NakedChartTester.mq5', 'NakedCore.mqh', 'CoreSelfTest.mqh')


def ini(risk_percent: float) -> str:
    return f"""[Experts]
AllowLiveTrading=0
AllowDllImport=0
Enabled=0
[Tester]
Expert=NakedChartTester.ex5
Symbol=GOLD
Period=M5
Model=4
ExecutionMode=0
Optimization=0
FromDate=2026.09.11
ToDate=2026.10.11
ForwardMode=0
Deposit=100
Currency=USD
Leverage=1:1000
UseLocal=1
UseRemote=0
UseCloud=0
Visual=0
Report=reports\\NakedChartTester-20260911-20261011
ReplaceReport=1
ShutdownTerminal=0
; risk_percent={risk_percent}
"""


def compile_expert():
    for name in SOURCES:
        (DATA / 'MQL5/Experts' / name).write_bytes((ROOT / name).read_bytes())
    log = LIVE / 'compile-live.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(INSTALL / 'MetaEditor64.exe'), f'/compile:{DATA / "MQL5/Experts/NakedChartTester.mq5"}', f'/log:{log}'],
        timeout=300)
    if not log.exists():
        fallback = DATA / 'MQL5/Experts/NakedChartTester.log'
        if fallback.exists():
            log.write_bytes(fallback.read_bytes())
    text = log.read_text(encoding='utf-16') if log.exists() else ''
    return {'compiler_returncode': result.returncode, 'log': str(log),
            'clean': '0 errors, 0 warnings' in text, 'ex5': EXPERT.exists()}


def main():
    LIVE.mkdir(exist_ok=True)
    risk = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    build = compile_expert()
    print(json.dumps({'compile': build}))
    assert build['clean'] and build['ex5'], 'compile not verified; refusing to launch'
    (DATA / 'reports').mkdir(exist_ok=True)
    for stale in (SUMMARY, REPORT):
        stale.unlink(missing_ok=True)
    config = LIVE / 'tester-live.ini'
    config.write_text(ini(risk), encoding='ascii')
    subprocess.Popen([str(INSTALL / 'terminal64.exe'), f'/config:{config}'])
    print(json.dumps({'launched': str(config), 'risk_percent': risk}))
    deadline = time.time() + 900
    while time.time() < deadline:
        if SUMMARY.exists() and REPORT.exists():
            break
        time.sleep(15)
    print(json.dumps({'summary_exists': SUMMARY.exists(), 'report_exists': REPORT.exists(),
                      'waited_seconds': round(900 - (deadline - time.time()))}))


if __name__ == '__main__':
    main()
