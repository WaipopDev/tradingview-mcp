#!/usr/bin/env python3
from pathlib import Path
p=Path.home()/"Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/logs/20260806.log"
raw=p.read_bytes(); text=raw.decode("utf-16-le","replace").replace("\ufeff","")
for line in text.splitlines():
    if any(t in line for t in ("14:36:19","14:36:20","14:36:21","14:36:22")):
        print(line)
