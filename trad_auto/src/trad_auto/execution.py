"""One-shot demo-only MT5 execution with a durable, fail-closed SQLite ledger."""
import hashlib
from datetime import datetime, timezone
import math
from pathlib import Path
import sqlite3
from .broker_time import offset_seconds, check_forming_bar


class ExecutionError(ValueError):
    """Safe, non-sensitive user-facing execution rejection."""


def _valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _state(conn, signal_id, state, *, order=None, deal=None, filled_price=None):
    conn.execute('UPDATE orders SET state=?, order_ticket=?, deal_ticket=?, filled_price=? WHERE signal_id=?',
                 (state, order, deal, filled_price, signal_id))
    conn.commit()


def execute_live_order(api, *, symbol, timeframe, plan, now, db_path, daily_loss_limit_usd, broker_utc_offset_hours=None):
    if broker_utc_offset_hours is None:
        raise ExecutionError('explicit broker UTC offset required for live execution')
    offset = offset_seconds(broker_utc_offset_hours)
    if daily_loss_limit_usd != 30 or not _valid_number(daily_loss_limit_usd):
        raise ExecutionError('explicit daily loss limit of 30 USD required')
    return _execute_order(api, symbol=symbol, timeframe=timeframe, plan=plan,
                          now=now, db_path=db_path, live=True, limit=daily_loss_limit_usd, offset=offset)


def execute_demo_order(api, *, symbol, timeframe, plan, now, db_path, broker_utc_offset_hours=0):
    return _execute_order(api, symbol=symbol, timeframe=timeframe, plan=plan,
                          now=now, db_path=db_path, live=False, limit=None,
                          offset=offset_seconds(broker_utc_offset_hours))


def _live_risk(api, account, now, request, limit, offset):
    current = api.account_info()
    if (current is None or current.trade_mode != getattr(api, 'ACCOUNT_TRADE_MODE_REAL', 2)
            or not getattr(current, 'login', None) or current.login != account.login
            or not getattr(current, 'server', None) or current.server != account.server
            or getattr(current, 'currency', None) != 'USD'):
        raise ExecutionError('live account changed or USD currency unavailable')
    start = datetime.fromtimestamp(now, timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end = datetime.fromtimestamp(now, timezone.utc)
    from datetime import timedelta
    deals = api.history_deals_get(start + timedelta(seconds=offset), end + timedelta(seconds=offset))
    positions = api.positions_get()
    if deals is None or positions is None:
        raise ExecutionError('broker history or positions unavailable')
    realized = 0.
    for deal in deals:
        fields = [getattr(deal, key, None) for key in ('profit', 'commission', 'swap', 'fee')]
        if not all(_valid_number(v) for v in fields):
            raise ExecutionError('broker history loss computation unavailable')
        realized += sum(fields)
    risk = 0.
    for position in positions:
        if not all(_valid_number(getattr(position, key, None)) for key in ('volume', 'price_open', 'sl')) or position.sl <= 0:
            raise ExecutionError('open position loss computation unavailable')
        direction = api.ORDER_TYPE_BUY if position.type == api.ORDER_TYPE_BUY else api.ORDER_TYPE_SELL
        if position.type not in (api.ORDER_TYPE_BUY, api.ORDER_TYPE_SELL):
            raise ExecutionError('open position direction unavailable')
        value = api.order_calc_profit(direction, position.symbol, position.volume, position.price_open, position.sl)
        if not _valid_number(value):
            raise ExecutionError('open position loss computation unavailable')
        risk += max(0., -value)
    proposed = api.order_calc_profit(request['type'], request['symbol'], request['volume'], request['price'], request['sl'])
    if not _valid_number(proposed) or proposed >= 0:
        raise ExecutionError('proposed loss computation unavailable')
    if max(0., -realized) + risk - proposed > limit:
        raise ExecutionError('daily loss limit exceeded')


def _execute_order(api, *, symbol, timeframe, plan, now, db_path, live, limit, offset):
    """Submit once to an explicitly verified demo account; never retry uncertain sends."""
    account = api.account_info()
    terminal = api.terminal_info()
    if account is None or account.trade_mode != getattr(api, 'ACCOUNT_TRADE_MODE_REAL' if live else 'ACCOUNT_TRADE_MODE_DEMO', 2 if live else 0):
        raise ExecutionError('demo account required; real-money account blocked')
    if live and (not getattr(account, 'login', None) or not getattr(account, 'server', None)):
        raise ExecutionError('live account identity unavailable')
    if not terminal or not terminal.connected or not terminal.trade_allowed or terminal.tradeapi_disabled:
        raise ExecutionError('terminal not ready for demo execution')
    if not account.trade_allowed or not account.trade_expert:
        raise ExecutionError('account not allowed to execute')
    if plan.get('action') not in ('BUY', 'SELL') or not plan.get('data_ready'):
        raise ExecutionError('no actionable validated signal')
    from .core import SECONDS
    interval = SECONDS[timeframe]
    if live:
        try:
            check_forming_bar(api, symbol, timeframe, now, offset)
        except Exception:
            raise ExecutionError('broker forming bar inconsistent with offset or clock') from None
    asof = plan.get('asof')
    if not _valid_number(asof) or not 0 <= now - asof < interval:
        raise ExecutionError('stale signal')
    info = api.symbol_info(symbol)
    if info is None or info.name != symbol or not info.visible or info.trade_mode != getattr(api, 'SYMBOL_TRADE_MODE_FULL', 4):
        raise ExecutionError('symbol not available for trading')
    tick = api.symbol_info_tick(symbol)
    if tick is None or not all(_valid_number(v) for v in (tick.bid, tick.ask, tick.time)):
        raise ExecutionError('invalid execution quote')
    if not -2 <= now - (tick.time - offset) <= 120 or tick.bid <= 0 or tick.ask <= 0 or tick.ask < tick.bid:
        raise ExecutionError('stale or invalid execution quote')
    price = tick.ask if plan['action'] == 'BUY' else tick.bid
    stop = plan.get('stop')
    target = plan.get('target')
    entry = plan.get('entry')
    rr = plan.get('rr')
    if not _valid_number(rr) or rr <= 0 or not all(_valid_number(v) for v in (stop, target, entry)):
        raise ExecutionError('stop/target/rr not valid')
    side = 1 if plan['action'] == 'BUY' else -1
    if not (side * (entry - stop) > 0 and side * (target - entry) > 0):
        raise ExecutionError('stop/target direction invalid')
    if not _valid_number(info.trade_tick_size) or info.trade_tick_size <= 0:
        raise ExecutionError('invalid tick size')
    quantum = info.trade_tick_size
    sl = round(round(stop / quantum) * quantum, info.digits)
    tp = round(round((price + side * rr * abs(price - sl)) / quantum) * quantum, info.digits)
    min_distance = info.trade_stops_level * info.point
    if side * (tick.bid - sl) <= min_distance or side * (tp - tick.ask) <= min_distance:
        raise ExecutionError('stop/target too close to market')
    volume = 0.01 if live else info.volume_min  # fixed live lot; demo retains broker minimum
    if live and (volume < info.volume_min or volume > info.volume_max or abs(round(volume / info.volume_step) * info.volume_step - volume) > 1e-9):
        raise ExecutionError('0.01 lot unsupported by broker')
    if not _valid_number(volume) or volume <= 0 or volume > info.volume_max or not _valid_number(info.volume_step) or info.volume_step <= 0:
        raise ExecutionError('invalid minimum volume')
    positions = api.positions_get(symbol=symbol)
    if positions is None:
        raise ExecutionError('positions unavailable')
    if positions:
        raise ExecutionError('existing position blocks another order')
    filling_ioc = getattr(api, 'SYMBOL_FILLING_IOC', 2)
    if not info.filling_mode & filling_ioc:
        raise ExecutionError('IOC filling not supported')
    signal = f"{symbol}|{timeframe}|{plan['action']}|{plan['bos']['time']}|{asof}"
    signal_id = hashlib.sha256(signal.encode()).hexdigest()
    request = dict(action=api.TRADE_ACTION_DEAL, symbol=symbol, volume=volume,
                   type=api.ORDER_TYPE_BUY if side == 1 else api.ORDER_TYPE_SELL,
                   price=price, sl=sl, tp=tp, deviation=10, magic=20261012,
                   comment='trad_auto:' + signal_id[:12],
                   type_time=api.ORDER_TIME_GTC, type_filling=api.ORDER_FILLING_IOC)
    path = Path(db_path).expanduser()
    if live:
        try:
            _live_risk(api, account, now, request, limit, offset)
        except ExecutionError:
            raise
        except Exception:
            raise ExecutionError('live risk data unavailable') from None
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path, timeout=5) as conn:
        conn.execute('PRAGMA synchronous=FULL')
        conn.execute('''CREATE TABLE IF NOT EXISTS orders (
            signal_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
            side TEXT NOT NULL, asof INTEGER NOT NULL, state TEXT NOT NULL,
            requested_price REAL NOT NULL, stop REAL NOT NULL, target REAL NOT NULL,
            volume REAL NOT NULL, order_ticket INTEGER, deal_ticket INTEGER,
            filled_price REAL)''')
        conn.execute('BEGIN IMMEDIATE')
        if conn.execute("SELECT 1 FROM orders WHERE state='pending' LIMIT 1").fetchone():
            # Release the write lock; never submit while another attempt is unresolved.
            conn.rollback()
            if conn.execute('SELECT 1 FROM orders WHERE signal_id=?', (signal_id,)).fetchone():
                raise ExecutionError('signal already recorded; do not resubmit')
            raise ExecutionError('pending order requires manual reconciliation')
        try:
            conn.execute('''INSERT INTO orders
                (signal_id, symbol, timeframe, side, asof, state, requested_price, stop, target, volume)
                VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)''',
                (signal_id, symbol, timeframe, plan['action'], asof, price, sl, tp, volume))
            conn.commit()  # persist reservation BEFORE any network call
        except sqlite3.IntegrityError:
            raise ExecutionError('signal already recorded; do not resubmit') from None
        try:
            checked = api.order_check(request)
        except Exception:
            raise ExecutionError('order check unavailable; pending record requires review') from None
        if checked is None or checked.retcode not in (0, api.TRADE_RETCODE_DONE):
            _state(conn, signal_id, 'rejected')
            raise ExecutionError('order check rejected; no order sent')
        # Recheck account and position just before sending; a user can switch terminals.
        if live:
            try:
                check_forming_bar(api, symbol, timeframe, now, offset)
                _live_risk(api, account, now, request, limit, offset)
            except ExecutionError:
                _state(conn, signal_id, 'rejected')
                raise
            except Exception:
                _state(conn, signal_id, 'rejected')
                raise ExecutionError('live risk data unavailable') from None
        else:
            current = api.account_info()
            if (current is None or current.trade_mode != getattr(api, 'ACCOUNT_TRADE_MODE_DEMO', 0)
                    or getattr(current, 'login', None) != getattr(account, 'login', None)
                    or getattr(current, 'server', None) != getattr(account, 'server', None)):
                _state(conn, signal_id, 'rejected')
                raise ExecutionError('demo account changed; no order sent')
        positions = api.positions_get(symbol=symbol)
        if positions is None or positions:
            _state(conn, signal_id, 'rejected')
            raise ExecutionError('positions changed or unavailable; no order sent')
        if live:
            latest = api.account_info()
            terminal_now = api.terminal_info()
            tick_now = api.symbol_info_tick(symbol)
            if (latest is None or latest.login != account.login or latest.trade_mode != account.trade_mode
                    or latest.server != account.server or latest.currency != 'USD' or not latest.trade_allowed or not latest.trade_expert
                    or terminal_now is None or not terminal_now.connected or not terminal_now.trade_allowed
                    or terminal_now.tradeapi_disabled or tick_now is None
                    or not _valid_number(tick_now.time) or not -2 <= now - (tick_now.time - offset) <= 120
                    or not _valid_number(tick_now.bid) or not _valid_number(tick_now.ask)
                    or tick_now.bid != tick.bid or tick_now.ask != tick.ask):
                _state(conn, signal_id, 'rejected')
                raise ExecutionError('account or quote changed; no order sent')
        try:
            sent = api.order_send(request)
        except Exception:
            raise ExecutionError('send uncertain; inspect terminal and DB before any retry') from None
        if sent is None:
            raise ExecutionError('send uncertain; inspect terminal and DB before any retry')
        if sent.retcode != api.TRADE_RETCODE_DONE:
            # A non-DONE retcode can still be ambiguous (partial fill, timeout).
            raise ExecutionError('send uncertain; inspect terminal and DB before any retry')
        order, deal = int(sent.order), int(sent.deal)
        if order <= 0 or deal <= 0:
            raise ExecutionError('send uncertain; inspect terminal and DB before any retry')
        _state(conn, signal_id, 'pending', order=order, deal=deal)
        try:
            deals = api.history_deals_get(ticket=deal)
        except Exception:
            deals = None
        matched = next((d for d in deals or () if d.ticket == deal and d.order == order
                        and d.symbol == symbol and _valid_number(d.volume) and d.volume > 0
                        and _valid_number(d.price) and d.price > 0), None)
        if matched is None:
            raise ExecutionError('send uncertain; inspect terminal and DB before any retry')
        _state(conn, signal_id, 'filled', order=order, deal=deal, filled_price=matched.price)
    return {'state': 'filled', 'order': order, 'deal': deal, 'symbol': symbol,
            'side': plan['action'], 'volume': matched.volume, 'price': price,
            'filled_price': matched.price, 'stop': sl,
            'target': tp, 'db_path': str(path)}
