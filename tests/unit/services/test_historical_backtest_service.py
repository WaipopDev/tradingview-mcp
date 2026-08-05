from __future__ import annotations

from datetime import datetime, timezone
import math

from tradingview_mcp.core.services.historical_backtest_service import run_db_backtest
from tradingview_mcp.core.services.tradingview_history_service import HistoricalCandle, ensure_history_schema, store_historical_candles


def _candle(i: int, close: float) -> HistoricalCandle:
    ts = 1760000000 + i * 300
    dt = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    return HistoricalCandle(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="5m",
        ts=ts,
        datetime_utc=dt,
        open=close - 0.2,
        high=close + 0.8,
        low=close - 0.8,
        close=close,
        volume=1000 + i,
    )


def test_run_db_backtest_stores_run_and_trades(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    ensure_history_schema(db_path)
    prices = []
    for i in range(160):
        prices.append(4000.0 + i * 0.08 + math.sin(i / 3) * 2.5)
    candles = [_candle(i, p) for i, p in enumerate(prices)]
    assert store_historical_candles(candles, db_path) == len(candles)

    result = run_db_backtest(
        symbol="XAUUSD",
        exchange="OANDA",
        timeframe="5m",
        strategy="ema_trend",
        score_gate=50,
        rr=1.0,
        sl_atr=0.8,
        max_hold_bars=8,
        db_path=db_path,
    )

    assert "error" not in result
    assert result["run_id"] >= 1
    assert result["candle_count"] == len(candles)
    assert result["total_trades"] >= 1

    import sqlite3

    con = sqlite3.connect(db_path)
    run_count = con.execute("select count(*) from backtest_runs").fetchone()[0]
    trade_count = con.execute("select count(*) from backtest_trades where run_id=?", (result["run_id"],)).fetchone()[0]
    assert run_count == 1
    assert trade_count == result["total_trades"]


def test_run_db_backtest_requires_enough_candles(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    ensure_history_schema(db_path)
    store_historical_candles([_candle(i, 4000 + i) for i in range(20)], db_path)

    result = run_db_backtest(db_path=db_path, timeframe="5m")

    assert "Not enough candles" in result["error"]
