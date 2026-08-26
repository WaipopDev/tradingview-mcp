#!/usr/bin/env python3
from pathlib import Path
p=Path.home()/"Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Logs/20260806.log"
raw=p.read_bytes(); text=raw.decode("utf-16-le","replace").replace("\ufeff","")
for line in text.splitlines():
    if "SteevStyleGridEA (GOLD,H1)" in line and any(t in line for t in ("13:55:","14:07:","14:19:","14:21:","14:36:")):
        print(line)
