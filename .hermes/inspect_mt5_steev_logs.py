#!/usr/bin/env python3
from pathlib import Path
root=Path.home()/"Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5"
paths=[root/"MQL5/Logs/20260806.log",root/"logs/20260806.log"]
needles=("SteevStyleGridEA","SGRID","Grid placed","risk lock","risk-lock","lock=","EMERGENCY","basket SL","basket TP","daily loss","equity DD","retcode","initialized")
for p in paths:
    raw=p.read_bytes()
    enc="utf-16-le" if raw[:2] in (b'\xff\xfe',b'\xfe\xff') or raw.count(b'\x00')>len(raw)//10 else "utf-8"
    text=raw.decode(enc,"replace").replace("\ufeff","")
    lines=[line for line in text.splitlines() if any(n.lower() in line.lower() for n in needles)]
    print(f"=== {p} encoding={enc} matched={len(lines)} ===")
    for line in lines[-250:]: print(line)
