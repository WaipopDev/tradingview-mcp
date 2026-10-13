"""Launch only our isolated portable terminal. Never target the user's terminal."""
from pathlib import Path
import subprocess
import shutil
import json
from prepare_isolated import ISOLATED, ROOT

binary = ROOT/'NakedChartTester.ex5'
log = (ROOT/'NakedChartTester.log').read_text(encoding='utf-16')
assert '0 errors, 0 warnings' in log and binary.exists(), 'compile not verified'
assert ISOLATED.is_relative_to(Path('C:/Users/waipo/AppData/Local/hermes/cache/scratch'))
shutil.copy2(binary, ISOLATED/'MQL5/Experts'/binary.name)
shutil.copy2(ROOT/'tester.ini',ISOLATED/'tester.ini')
command = [str(ISOLATED/'terminal64.exe'),'/portable',f'/config:{ISOLATED / "tester.ini"}']
process = subprocess.Popen(command, cwd=ISOLATED)
record = {'pid':process.pid,'command':command,'status':'launched_not_completed'}
(ROOT/'launch.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
try:
    print('isolated_exit_code',process.wait(timeout=45))
except subprocess.TimeoutExpired:
    print('Isolated terminal still running after 45 seconds; inspect isolated logs/UI. No process killed.')
