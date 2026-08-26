#!/usr/bin/env python3
from pathlib import Path
root=Path.home()/"Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5"
for rel in ("MQL5/Logs/20260806.log","logs/20260806.log"):
 p=root/rel; raw=p.read_bytes(); text=raw.decode("utf-16-le","replace").replace("\ufeff","")
 print("===",rel,"===")
 for line in text.splitlines():
  if any(t in line for t in ("13:55:34","13:55:35","13:55:36","13:55:37")):
   print(line)
