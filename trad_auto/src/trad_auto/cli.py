"""JSON-only results and fail-closed CLI; provider and clock are injectable."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
from .core import Config, SECONDS, ValidationError, analyze, quote_check, replay, structure, validate
from .execution import ExecutionError, execute_demo_order, execute_live_order
from .manual_sync import sync_manual_orders
from .provider import MT5Provider, ProviderError
from .broker_time import offset_seconds, check_forming_bar


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValidationError(message)


def main(argv=None, *, provider_factory=MT5Provider, clock=time.time):
    result = {'action': 'WAIT', 'connected': False, 'fresh': False, 'data_ready': False, 'execution_enabled': False}
    code = 2
    try:
        parser = Parser(description='Local MT5 closed-candle analysis and manual demo-only execution')
        parser.add_argument('command', choices=['doctor', 'analyze', 'replay', 'execute-demo', 'execute-live', 'sync-manual'])
        parser.add_argument('--daily-loss-limit-usd', type=float, help='required for live execution: exactly 30 USD')
        parser.add_argument('--broker-utc-offset-hours', type=float, help='explicit broker timestamp offset from UTC; required for live')
        parser.add_argument('--since-utc', help='first sync cutoff, ISO 8601 UTC; stored per account')
        parser.add_argument('--db-path', default=str(Path.home() / '.trad_auto' / 'orders.sqlite3'),
                            help='durable SQLite ledger for execution and manual sync')
        parser.add_argument('--symbol', default='XAUUSD', help='exact broker symbol, never aliased')
        parser.add_argument('--timeframe', choices=SECONDS, default=Config.timeframe)
        parser.add_argument('--bars', type=int, default=260)
        parser.add_argument('--pivot', type=int, default=2)
        parser.add_argument('--rr', type=float, default=Config.rr)
        parser.add_argument('--max-spread', type=float, default=1.0, help='absolute price units, not points')
        parser.add_argument('--max-tick-age', type=float, default=120.0)
        parser.add_argument('--retest-bars', type=int, default=4)
        parser.add_argument('--no-htf', action='store_true', help='explicitly disable H1 alignment filter')
        args = parser.parse_args(argv)
        if args.command == 'execute-live' and args.daily_loss_limit_usd != 30:
            raise ValidationError('execute-live requires --daily-loss-limit-usd 30')
        if args.command == 'execute-live' and args.broker_utc_offset_hours is None:
            raise ValidationError('execute-live requires explicit --broker-utc-offset-hours')
        try:
            offset = offset_seconds(args.broker_utc_offset_hours if args.broker_utc_offset_hours is not None else 0)
        except ValueError:
            raise ValidationError('invalid broker UTC offset hours') from None
        if args.command != 'execute-live' and args.daily_loss_limit_usd is not None:
            raise ValidationError('daily-loss-limit-usd applies only to execute-live')
        if args.command == 'sync-manual':
            since = None
            if args.since_utc:
                try:
                    start = datetime.fromisoformat(args.since_utc.replace('Z', '+00:00'))
                    if start.tzinfo is None or start.utcoffset().total_seconds() != 0:
                        raise ValueError('not UTC')
                    since = int(start.timestamp())
                except (ValueError, OverflowError):
                    raise ValidationError('since-utc must be a UTC ISO 8601 timestamp') from None
            with provider_factory() as provider:
                if hasattr(provider, 'status'):
                    result.update(provider.status())
                    result['execution_enabled'] = False
                result['manual_sync'] = sync_manual_orders(
                    provider.api, db_path=args.db_path, now=clock(), initial_since=since)
            result.update(mode='sync-manual', reason='read-only broker history synced')
            print(json.dumps(result, ensure_ascii=True, allow_nan=False))
            return 0
        config = Config(symbol=args.symbol, timeframe=args.timeframe, pivot=args.pivot, rr=args.rr,
                        max_spread=args.max_spread, max_tick_age=args.max_tick_age, retest_bars=args.retest_bars)
        if not 2*config.pivot+6 <= args.bars <= 5000:
            raise ValidationError('bars must be between 2*pivot+6 and 5000')
        result.update(symbol=config.symbol, timeframe=config.timeframe, mode=args.command, higher_timeframe=None if args.no_htf or config.timeframe == 'H1' else 'H1')
        with (MT5Provider(broker_utc_offset_hours=args.broker_utc_offset_hours or 0) if provider_factory is MT5Provider else provider_factory()) as provider:
            result.update(provider.status())
            result['execution_enabled'] = False
            if not result['connected']:
                raise ProviderError('MT5 not connected')
            now = clock()
            if args.broker_utc_offset_hours is not None and args.command != 'replay':
                check_forming_bar(provider.api, config.symbol, config.timeframe, now, offset)
            bars = provider.candles(config.symbol, config.timeframe, args.bars, now=now)
            result['candles'] = len(bars)
            result['last_closed_time'] = bars[-1].time if bars else None
            higher = provider.candles(config.symbol, 'H1', args.bars, now=now) if result['higher_timeframe'] else None
            if args.command == 'replay':
                result.update(replay(bars, config, higher))
                result.update(historical_data_ready=True, reason='descriptive counts only; current freshness and historical spread not asserted')
                code = 0
            else:
                quote = provider.quote(config.symbol)
                # Only publish finite sanitized quote diagnostics; never terminal/account objects.
                age = now - quote['tick_time']
                result['tick_age_seconds'] = age if math.isfinite(age) else None
                spread = quote['ask'] - quote['bid']
                result['spread_price_units'] = spread if math.isfinite(spread) else None
                result['fresh'] = bool(bars and -2 <= age <= config.max_tick_age and 0 <= now-(bars[-1].time+SECONDS[config.timeframe]) <= SECONDS[config.timeframe])
                validate(bars, config, now)
                quote_check(config, now, **quote)
                higher_trend = None
                if higher is not None:
                    validate(higher, replace(config, timeframe='H1'), now)
                    higher_trend = structure(higher, config.pivot)['trend']
                result['higher_trend'] = higher_trend
                result['data_ready'] = True
                if args.command == 'doctor':
                    result['reason'] = 'market data ready; demo execution available via execute-demo only'
                else:
                    result.update(analyze(bars, config, now=now, higher_trend=higher_trend, **quote))
                    if args.command in ('execute-demo', 'execute-live'):
                        if result['action'] == 'WAIT':
                            result['reason'] = 'no confirmed setup; no order submitted'
                        else:
                            executor = execute_live_order if args.command == 'execute-live' else execute_demo_order
                            kwargs = {'daily_loss_limit_usd': args.daily_loss_limit_usd, 'broker_utc_offset_hours': args.broker_utc_offset_hours} if args.command == 'execute-live' else {'broker_utc_offset_hours': args.broker_utc_offset_hours or 0}
                            result['execution'] = executor(
                                provider.api, symbol=config.symbol, timeframe=config.timeframe,
                                plan=result, now=now, db_path=args.db_path, **kwargs)
                            result['execution_enabled'] = True
                code = 0 if result['data_ready'] else 2
    except (ValidationError, ProviderError, ExecutionError) as exc:
        code = 2
        result.update(action='WAIT', data_ready=False, reason=str(exc), execution_enabled=False)
    except Exception:
        code = 2
        # Provider exceptions may contain credentials or identifiers: do not echo them.
        result.update(action='WAIT', data_ready=False, reason='provider failure; check local terminal and dependencies', execution_enabled=False)
    if code != 0:
        for field in ('entry', 'stop', 'target', 'rr', 'entry_basis', 'bos', 'structure', 'asof', 'setups', 'counts', 'historical_data_ready'):
            result.pop(field, None)
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return code
