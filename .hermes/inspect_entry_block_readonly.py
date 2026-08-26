#!/usr/bin/env python3
import os, sqlite3, json
from pathlib import Path
p=Path(os.path.expanduser('~/.tradingview-mcp/trading_signals.sqlite3'))
con=sqlite3.connect(p); con.execute('PRAGMA query_only=ON'); con.row_factory=sqlite3.Row
sig=con.execute("SELECT id,price,bias,decision,total_score,regime,created_at FROM trade_signals WHERE UPPER(symbol)='XAUUSD' AND timeframe='15m' ORDER BY created_at DESC,id DESC LIMIT 1").fetchone()
print('LATEST_SIGNAL='+json.dumps(dict(sig),ensure_ascii=False))
for side in ('BUY','SELL'):
 rows=con.execute("SELECT id,source,direction,status,result,entry_price,entered_at,setup_score,order_score,created_at,closed_at FROM trade_plan_outcomes WHERE UPPER(symbol)='XAUUSD' AND timeframe='15m' AND direction=? AND status='closed' ORDER BY closed_at DESC,id DESC LIMIT 8",(side,)).fetchall()
 print(side+'_ADAPTIVE_ROWS='+json.dumps([dict(r) for r in rows],ensure_ascii=False))
 actual=con.execute("SELECT id,source,direction,result,entry_price,entered_at,setup_score,order_score,closed_at FROM trade_plan_outcomes WHERE UPPER(symbol)='XAUUSD' AND timeframe='15m' AND direction=? AND status='closed' AND source='telegram_entry_alert' AND entry_price IS NOT NULL AND entered_at IS NOT NULL ORDER BY closed_at DESC,id DESC LIMIT 8",(side,)).fetchall()
 print(side+'_ACTUAL_MAIN_ROWS='+json.dumps([dict(r) for r in actual],ensure_ascii=False))
