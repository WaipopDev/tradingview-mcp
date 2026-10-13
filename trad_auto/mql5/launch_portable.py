"""Launch the durable portable terminal so the configured test runs on startup.

Refuses to launch unless the EA binary and compile log are present, and polls
for the raw report plus the EA's own summary file. /portable keeps this
completely separate from the user's live terminal and data folder.
"""
from pathlib import Path
import json
import subprocess
import sys
import time

PORTABLE = Path('D:/Hermes/mt5-portable')
ROOT = Path(__file__).resolve().parent


def main():
    wait = float(sys.argv[1]) if len(sys.argv) > 1 else 900
    for required in (PORTABLE / 'terminal64.exe', PORTABLE / 'MQL5/Experts/NakedChartTester.ex5',
                     PORTABLE / 'tester.ini'):
        if not required.exists():
            raise SystemExit(f'missing {required}; run prepare_portable.py first')
    summary = PORTABLE / 'MQL5/Files/NakedChartTester-summary.json'
    report = PORTABLE / 'reports/NakedChartTester-20260911-20261011.html'
    for stale in (summary, report):
        stale.unlink(missing_ok=True)
    process = subprocess.Popen([str(PORTABLE / 'terminal64.exe'), '/portable',
                                f'/config:{PORTABLE / "tester.ini"}'])
    print(json.dumps({'pid': process.pid, 'portable': str(PORTABLE)}))
    deadline = time.time() + wait
    while time.time() < deadline:
        if summary.exists() and report.exists():
            break
        if process.poll() is not None and not summary.exists():
            break
        time.sleep(10)
    print(json.dumps({'summary_exists': summary.exists(), 'report_exists': report.exists(),
                      'terminal_exit': process.poll(), 'waited_seconds': round(wait - (deadline - time.time()))}))


if __name__ == '__main__':
    main()
