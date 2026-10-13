"""Read-only on-demand sync of personally entered MT5 orders and deals."""
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import sqlite3

from .execution import ExecutionError


def sync_manual_orders(api, *, db_path, now, initial_since=None):
    """Import manual broker history into separate ledger tables, never submit an order."""
    account = api.account_info()
    if account is None or not getattr(account, 'login', None):
        raise ExecutionError('account unavailable for history sync')
    identity = f"{getattr(account, 'server', '')}|{account.login}"
    account_key = hashlib.sha256(identity.encode()).hexdigest()
    tick = api.symbol_info_tick('GOLD')
    if tick is None or not isinstance(tick.time, (int, float)) or not math.isfinite(tick.time):
        raise ExecutionError('GOLD clock unavailable for history sync')
    observed_offset = round(tick.time - now)
    if abs(observed_offset) > 6 * 3600:
        raise ExecutionError('broker clock offset out of range')
    if abs(observed_offset) <= 120:
        observed_offset = 0
    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=5) as conn:
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('''CREATE TABLE IF NOT EXISTS manual_sync_config (
            account_key TEXT PRIMARY KEY, since INTEGER NOT NULL, broker_offset INTEGER)''')
        if 'broker_offset' not in {row[1] for row in conn.execute('PRAGMA table_info(manual_sync_config)')}:
            conn.execute('ALTER TABLE manual_sync_config ADD COLUMN broker_offset INTEGER')
        conn.execute('''CREATE TABLE IF NOT EXISTS manual_orders (
            account_key TEXT NOT NULL, ticket INTEGER NOT NULL, time_setup INTEGER NOT NULL,
            time_done INTEGER, symbol TEXT NOT NULL, type INTEGER NOT NULL,
            state INTEGER NOT NULL, volume_initial REAL NOT NULL, volume_current REAL NOT NULL,
            price_open REAL NOT NULL, sl REAL NOT NULL, tp REAL NOT NULL,
            position_id INTEGER NOT NULL, PRIMARY KEY (account_key, ticket))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS manual_deals (
            account_key TEXT NOT NULL, ticket INTEGER NOT NULL, order_ticket INTEGER NOT NULL,
            time INTEGER NOT NULL, symbol TEXT NOT NULL, type INTEGER NOT NULL,
            entry INTEGER NOT NULL, volume REAL NOT NULL, price REAL NOT NULL,
            position_id INTEGER NOT NULL, profit REAL NOT NULL,
            commission REAL NOT NULL, swap REAL NOT NULL,
            PRIMARY KEY (account_key, ticket))''')
        existing = conn.execute('SELECT since, broker_offset FROM manual_sync_config WHERE account_key=?',
                                (account_key,)).fetchone()
        since = existing[0] if existing else int(now if initial_since is None else initial_since)
        offset = existing[1] if existing and existing[1] is not None else observed_offset
        if abs(observed_offset - offset) > 120:
            raise ExecutionError('broker clock offset changed; history sync blocked')
        if since <= 0 or since > now:
            raise ExecutionError('invalid sync start time')
        broker_since, broker_now = since + offset, now + offset
        start = datetime.fromtimestamp(broker_since, timezone.utc)
        end = datetime.fromtimestamp(broker_now, timezone.utc)
        try:
            orders = api.history_orders_get(start, end)
            deals = api.history_deals_get(start, end)
        except Exception:
            raise ExecutionError('broker history unavailable') from None
        if orders is None or deals is None:
            raise ExecutionError('broker history unavailable')
        current = api.account_info()
        if current is None or f"{getattr(current, 'server', '')}|{current.login}" != identity:
            raise ExecutionError('account changed during history sync')
        order_reasons = {api.ORDER_REASON_CLIENT, api.ORDER_REASON_MOBILE, api.ORDER_REASON_WEB}
        deal_reasons = {api.DEAL_REASON_CLIENT, api.DEAL_REASON_MOBILE, api.DEAL_REASON_WEB}
        imported_orders = 0
        imported_deals = 0
        conn.execute('BEGIN IMMEDIATE')
        for item in orders:
            if item.reason not in order_reasons or item.magic != 0 or item.time_setup < broker_since or item.time_setup > broker_now:
                continue
            found = conn.execute('SELECT 1 FROM manual_orders WHERE account_key=? AND ticket=?',
                                 (account_key, item.ticket)).fetchone()
            conn.execute('''INSERT INTO manual_orders
                (account_key, ticket, time_setup, time_done, symbol, type, state, volume_initial,
                 volume_current, price_open, sl, tp, position_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(account_key, ticket) DO UPDATE SET
                time_done=excluded.time_done, state=excluded.state,
                volume_current=excluded.volume_current, price_open=excluded.price_open,
                sl=excluded.sl, tp=excluded.tp''',
                (account_key, item.ticket, item.time_setup, item.time_done, item.symbol, item.type,
                 item.state, item.volume_initial, item.volume_current, item.price_open,
                 item.sl, item.tp, item.position_id))
            imported_orders += not bool(found)
        for item in deals:
            if item.reason not in deal_reasons or item.magic != 0 or item.time < broker_since or item.time > broker_now:
                continue
            cur = conn.execute('''INSERT OR IGNORE INTO manual_deals
                (account_key, ticket, order_ticket, time, symbol, type, entry, volume, price,
                 position_id, profit, commission, swap)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (account_key, item.ticket, item.order, item.time, item.symbol, item.type,
                 item.entry, item.volume, item.price, item.position_id, item.profit,
                 item.commission, item.swap))
            imported_deals += cur.rowcount
        conn.execute('''INSERT INTO manual_sync_config (account_key, since, broker_offset)
                        VALUES (?, ?, ?) ON CONFLICT(account_key) DO UPDATE SET
                        broker_offset=excluded.broker_offset WHERE manual_sync_config.broker_offset IS NULL''',
                     (account_key, since, offset))
        conn.commit()
    return {'new_orders': imported_orders, 'new_deals': imported_deals,
            'since': since, 'broker_offset_seconds': offset, 'db_path': str(path)}
