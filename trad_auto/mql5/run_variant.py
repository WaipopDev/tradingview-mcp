"""Run one documented tester variant in the portable terminal.

Closes the portable terminal (never the live one), writes the .set input file and
the tester config for the requested risk budget, relaunches with /portable, and
waits for the fresh TESTER_SUMMARY line written by the EA.

Usage: run_variant.py <risk_percent> <label>
"""
from ctypes import windll, wintypes, WINFUNCTYPE, c_bool, create_unicode_buffer
from pathlib import Path
import json
import subprocess
import sys
import time

PORTABLE = Path('D:/Hermes/mt5-portable')
PORTABLE_MARKER = 'XMGlobal-MT5 10: Demo Account'
ROOT = Path(__file__).resolve().parent


def portable_windows(close: bool = False) -> list:
    user32 = windll.user32
    closed = []

    def callback(hwnd, _):
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, wintypes.byref(pid))
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buf = create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if PORTABLE_MARKER in buf.value:
            closed.append((pid.value, buf.value[:60]))
            if close:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
        return True

    user32.EnumWindows(WINFUNCTYPE(c_bool, wintypes.HWND, wintypes.LPARAM)(callback), 0)
    return closed


def summaries() -> list:
    found = []
    for path in sorted(PORTABLE.glob('Tester/Agent-*/logs/*.log')):
        for line in path.read_bytes().decode('utf-16', 'replace').splitlines():
            if 'TESTER_SUMMARY' in line:
                found.append(line.split('TESTER_SUMMARY', 1)[1].strip())
    return found


def main():
    risk = float(sys.argv[1])
    label = sys.argv[2]
    seen = len(summaries())
    print(json.dumps({'closing': portable_windows(close=True)}))
    # The previous instance must release the portable folder before a new one
    # can run the tester; a short fixed sleep was not enough (verified no-op run).
    deadline = time.time() + 120
    while time.time() < deadline and portable_windows():
        time.sleep(5)
    if portable_windows():
        raise SystemExit('portable terminal did not close; refusing to launch a second instance')
    time.sleep(20)
    profiles = PORTABLE / 'MQL5/Profiles/Tester'
    profiles.mkdir(parents=True, exist_ok=True)
    (profiles / f'{label}.set').write_text(f'InpRiskPercent={risk}\n', encoding='ascii')
    ini = (ROOT / 'tester.ini').read_text(encoding='ascii')
    ini = ini.replace('ShutdownTerminal=1', 'ShutdownTerminal=0')
    ini = ini.replace('Expert=NakedChartTester.ex5', f'Expert=NakedChartTester.ex5\nExpertParameters={label}.set')
    ini = ini.replace('Report=reports\\NakedChartTester-20260911-20261011', f'Report=reports\\{label}')
    (PORTABLE / 'tester.ini').write_text(ini, encoding='ascii')
    process = subprocess.Popen([str(PORTABLE / 'terminal64.exe'), '/portable',
                                f'/config:{PORTABLE / "tester.ini"}'])
    started = time.time()
    summary = None
    while time.time() - started < 420:
        found = summaries()
        if len(found) > seen:
            summary = found[-1]
            break
        time.sleep(5)
    report = PORTABLE / 'reports' / f'{label}.htm'
    print(json.dumps({'label': label, 'risk_percent': risk, 'pid': process.pid,
                      'summary': summary, 'report': str(report) if report.exists() else None,
                      'elapsed_seconds': round(time.time() - started)}))
    if summary is None:
        raise SystemExit('no new TESTER_SUMMARY; inspect the portable tester log')


if __name__ == '__main__':
    main()
