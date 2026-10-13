"""Prepare isolated portable MT5: allowlisted binaries + nonsecret market data only.
Never read/copy source Config, profiles, accounts, logs, trades, mail, or credentials.
"""
from pathlib import Path
import os
import shutil
import subprocess
import json

ROOT = Path(__file__).resolve().parent
ISOLATED = Path('C:/Users/waipo/AppData/Local/hermes/cache/scratch/trad-auto-mt5-isolated')
SOURCE = Path('C:/Program Files/MetaTrader 5')
MARKET = Path('C:/Users/waipo/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/bases')

def main():
    ISOLATED.mkdir(parents=True, exist_ok=True)
    for name in ('terminal64.exe','MetaEditor64.exe','metatester64.exe'):
        shutil.copy2(SOURCE/name,ISOLATED/name)
    copied, skipped = [], []
    for server in ('XMGlobal-MT5 8','XMGlobal-MT5 10'):
        for kind in ('history','ticks'):
            source = MARKET/server/kind/'GOLD'
            target = ISOLATED/'bases'/server/kind/'GOLD'
            if source.exists():
                for file in source.rglob('*'):
                    if not file.is_file():
                        continue
                    destination = target / file.relative_to(source)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(file, destination)
                        copied.append(str(file.relative_to(MARKET)))
                    except PermissionError:
                        skipped.append(str(file.relative_to(MARKET)))
        for source in (MARKET/server/'symbols').glob('symbols-*.dat'):
            target = ISOLATED/'bases'/server/'symbols'/source.name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            copied.append(str(source.relative_to(MARKET)))
    for name in ('reports','MQL5/Experts','MQL5/Profiles/Tester'):
        (ISOLATED/name).mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'tester.ini',ISOLATED/'tester.ini')
    result = subprocess.run([str(ISOLATED/'MetaEditor64.exe'),'/portable',f'/compile:{ROOT / "NakedChartTester.mq5"}','/log'], timeout=180)
    manifest = {'isolated_path':str(ISOLATED),'compiler_returncode':result.returncode,'market_data_files':copied,'locked_market_files_skipped':skipped,'credentials_copied':False}
    (ROOT/'isolation-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'isolated_path':str(ISOLATED),'compiler_returncode':result.returncode,'market_files_count':len(copied),'ex5_exists':(ROOT/'NakedChartTester.ex5').exists()}))

if __name__=='__main__':
    main()
