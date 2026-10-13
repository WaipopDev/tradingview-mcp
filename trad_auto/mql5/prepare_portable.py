"""Create a durable, self-contained portable MT5 for isolated tester runs.

Copies only allowlisted executables and non-secret GOLD market caches. Never
copies Config, accounts, credentials, profiles, trades, mail, or logs, so the
install starts unauthenticated and must be logged in once by the user.
"""
from pathlib import Path
import json
import shutil

INSTALL = Path('C:/Program Files/MetaTrader 5')
LIVE_BASES = Path('C:/Users/waipo/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/bases')
PORTABLE = Path('D:/Hermes/mt5-portable')
ROOT = Path(__file__).resolve().parent
SERVERS = ('XMGlobal-MT5 8', 'XMGlobal-MT5 10')
BINARIES = ('terminal64.exe', 'MetaEditor64.exe', 'metatester64.exe')
SOURCES = ('NakedChartTester.mq5', 'NakedChartTester.ex5', 'NakedCore.mqh', 'CoreSelfTest.mqh')


def main():
    PORTABLE.mkdir(parents=True, exist_ok=True)
    for name in BINARIES:
        shutil.copy2(INSTALL / name, PORTABLE / name)
    copied, skipped = [], []
    for server in SERVERS:
        for kind in ('history', 'ticks'):
            source = LIVE_BASES / server / kind / 'GOLD'
            if not source.exists():
                continue
            for file in source.rglob('*'):
                if not file.is_file():
                    continue
                target = PORTABLE / 'bases' / server / kind / 'GOLD' / file.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copy2(file, target)
                    copied.append(str(file.relative_to(LIVE_BASES)))
                except PermissionError:
                    skipped.append(str(file.relative_to(LIVE_BASES)))
        for source in (LIVE_BASES / server / 'symbols').glob('symbols-*.dat'):
            target = PORTABLE / 'bases' / server / 'symbols' / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(str(source.relative_to(LIVE_BASES)))
    for name in ('reports', 'MQL5/Experts', 'MQL5/Profiles/Tester', 'MQL5/Files'):
        (PORTABLE / name).mkdir(parents=True, exist_ok=True)
    for name in SOURCES:
        source = ROOT / name
        shutil.copy2(source, PORTABLE / 'MQL5/Experts' / name)
    config = (ROOT / 'tester.ini').read_text(encoding='ascii').replace('ShutdownTerminal=1', 'ShutdownTerminal=0')
    (PORTABLE / 'tester.ini').write_text(config, encoding='ascii')
    manifest = {'portable_path': str(PORTABLE), 'binaries': list(BINARIES),
                'market_files_copied': len(copied), 'market_files_locked_skipped': skipped,
                'credentials_copied': False, 'live_config_copied': False,
                'login_required': True}
    (ROOT / 'portable-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'market_files_locked_skipped'}))
    print('locked_skipped:', len(skipped))


if __name__ == '__main__':
    main()
