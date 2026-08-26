#!/usr/bin/env python3
"""Warn Telegram when trading DB price is stale while orders are open."""
from __future__ import annotations
import argparse, os, sqlite3, subprocess
from datetime import datetime, timezone
from pathlib import Path


def db_path():
    return Path(os.getenv('TRADINGVIEW_MCP_DB_PATH') or os.getenv('TRAD_SIGNAL_DB_PATH') or Path.home()/'.tradingview-mcp'/'trading_signals.sqlite3').expanduser()


def parse_dt(s):
    if not s: return None
    try:
        d=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--db-path', default=str(db_path())); p.add_argument('--symbol', default='XAUUSD'); p.add_argument('--timeframe', default='15m'); p.add_argument('--target', default=os.getenv('TRAD_TELEGRAM_TARGET') or 'telegram:8237892676'); p.add_argument('--max-age-seconds', type=int, default=180); p.add_argument('--dry-run', action='store_true'); args=p.parse_args(argv)
    con=sqlite3.connect(Path(args.db_path).expanduser()); con.row_factory=sqlite3.Row
    con.execute('''CREATE TABLE IF NOT EXISTS telegram_stale_data_alerts (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, timeframe TEXT, bucket INTEGER, target TEXT, delivered_at TEXT, UNIQUE(symbol,timeframe,bucket,target))''')
    latest=con.execute('select id,price,created_at from trade_signals where upper(symbol)=upper(?) and timeframe=? order by id desc limit 1',(args.symbol,args.timeframe)).fetchone()
    open_count=con.execute("select count(*) from trade_plan_outcomes where upper(symbol)=upper(?) and timeframe=? and status in ('pending','entered')",(args.symbol,args.timeframe)).fetchone()[0]
    if not latest or open_count==0: return 0
    dt=parse_dt(latest['created_at']); now=datetime.now(timezone.utc); age=int((now-dt).total_seconds()) if dt else 999999
    if age < args.max_age_seconds: return 0
    bucket=age//900
    if con.execute('select 1 from telegram_stale_data_alerts where symbol=? and timeframe=? and bucket=? and target=?',(args.symbol,args.timeframe,bucket,args.target)).fetchone(): return 0
    msg=f"⚠️ XAUUSD data stale\nDB price: {latest['price']}\nข้อมูลล่าสุดเก่า {age//60} นาที แต่ยังมี order เปิด {open_count} ไม้\nงดเชื่อสถานะ TP/SL อัตโนมัติจนกว่าดึงราคากลับมาปกติ"
    if args.dry_run:
        print(msg); return 0
    sent=subprocess.run(['hermes','send','--quiet','--to',args.target,'--subject','XAUUSD data stale',msg],text=True,capture_output=True)
    if sent.returncode!=0:
        print(sent.stderr.strip() or sent.stdout.strip()); return sent.returncode
    con.execute('insert or ignore into telegram_stale_data_alerts(symbol,timeframe,bucket,target,delivered_at) values(?,?,?,?,?)',(args.symbol,args.timeframe,bucket,args.target,now.isoformat())); con.commit(); return 0

if __name__=='__main__': raise SystemExit(main())
