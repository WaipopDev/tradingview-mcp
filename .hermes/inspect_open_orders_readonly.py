#!/usr/bin/env python3
import os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
p=Path(os.path.expanduser('~/.tradingview-mcp/trading_signals.sqlite3'))
con=sqlite3.connect(p); con.execute('PRAGMA query_only=ON'); con.row_factory=sqlite3.Row
rows=con.execute("SELECT id,source,direction,status,entry_low,entry_high,entry_price,created_at,last_checked_at FROM trade_plan_outcomes WHERE status IN ('pending','entered') ORDER BY id").fetchall()
now=datetime.now(timezone.utc)
for r in rows:
    try:
        t=datetime.fromisoformat(str(r['created_at']).replace('Z','+00:00')); t=t if t.tzinfo else t.replace(tzinfo=timezone.utc)
        age=(now-t).total_seconds()/60
    except Exception: age=-1
    print(f"#{r['id']} {r['source']} {r['direction']} {r['status']} age_min={age:.1f} zone={r['entry_low']}-{r['entry_high']} entry={r['entry_price']}")
print(f"open_count={len(rows)}")
