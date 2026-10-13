"""Collect and parse evidence from a completed portable tester run.

Writes artifacts/portable-summary.json. Metrics stay null when a file is
missing, so a blocked or partial run can never be reported as zero trades.
"""
from pathlib import Path
import hashlib
import json
import re

PORTABLE = Path('D:/Hermes/mt5-portable')
ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_of(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ('utf-16', 'utf-8', 'cp1252'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', 'replace')


def report_metrics(report: Path) -> dict:
    if not report.exists():
        return {}
    text = re.sub(r'<[^>]+>', ' ', text_of(report))
    text = re.sub(r'&nbsp;?', ' ', text)
    flat = re.sub(r'\s+', ' ', text)
    wanted = {
        'initial_deposit': r'Initial Deposit\s*:?\s*([\d\s.,]+)',
        'net_profit': r'Total Net Profit\s*:?\s*([-\d\s.,]+)',
        'profit_factor': r'Profit Factor\s*:?\s*([\d.,]+)',
        'trades': r'Total Trades\s*:?\s*([\d\s]+)',
        'balance_drawdown_maximal': r'Balance Drawdown Maximal\s*:?\s*([\d\s.,]+\(?[\d.,]*%?\)?)',
        'equity_drawdown_maximal': r'Equity Drawdown Maximal\s*:?\s*([\d\s.,]+\(?[\d.,]*%?\)?)',
        'bars': r'Bars\s*:?\s*([\d\s]+)',
        'ticks': r'Ticks\s*:?\s*([\d\s]+)',
        'modeling_quality': r'([\d.]+%)\s*(?:real ticks|modelling quality)',
        'symbol_period': r'Symbol\s*:?\s*([A-Za-z0-9.#_-]+)\s*Period\s*:?\s*([A-Za-z0-9]+)',
    }
    found = {}
    for name, pattern in wanted.items():
        match = re.search(pattern, flat, re.I)
        found[name] = match.groups() if match else None
    return found


def main():
    ARTIFACTS.mkdir(exist_ok=True)
    summary_path = PORTABLE / 'MQL5/Files/NakedChartTester-summary.json'
    reports = sorted((PORTABLE / 'reports').glob('*.html'))
    tester_logs = sorted((PORTABLE / 'Tester/logs').glob('*.log'))
    terminal_logs = sorted((PORTABLE / 'logs').glob('*.log'))
    ea_summary = json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else None
    tester_text = '\n'.join(text_of(path) for path in tester_logs)
    terminal_text = '\n'.join(text_of(path) for path in terminal_logs)
    for path, name in [(p, f'portable-{p.name}') for p in reports + tester_logs + terminal_logs]:
        (ARTIFACTS / name).write_bytes(path.read_bytes())
    payload = {
        'status': 'completed' if (ea_summary and reports) else 'incomplete',
        'ea_summary': ea_summary,
        'report_section': report_metrics(reports[-1]) if reports else {},
        'tester_log_lines': [line for line in tester_text.splitlines() if line.strip()][:40],
        'blocker_present': 'not started' in tester_text.lower() or 'not started' in terminal_text.lower(),
        'authorized': 'authorized on' in terminal_text.lower(),
        'credentials_copied': False,
        'artifacts': {},
    }
    for path in [summary_path, *reports, *tester_logs, *terminal_logs]:
        if path.exists():
            payload['artifacts'][str(path)] = {'bytes': path.stat().st_size, 'sha256': sha256(path)}
    out = ARTIFACTS / 'portable-summary.json'
    out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2)[:4000])


if __name__ == '__main__':
    main()
