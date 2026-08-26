# Session Summary — Trad/MGT Backtest & Replay

Generated: 2026-08-05 13:35:24 +07
Repo: `/Users/waipop/MainWTN/Hermes/trad`
DB: `/Users/waipop/.tradingview-mcp/trading_signals.sqlite3`
Instrument: `OANDA:XAUUSD`

## Executive Summary

MGT workflow progressed from data instrumentation to historical TradingView candle storage, DB-backed backtesting, approximate live-logic replay, filter optimization, and finally exact production-entry replay before touching real Telegram/order logic.

Key decision: do not modify production Telegram/order logic yet. Use exact production-entry replay and shadow/paper validation first.

Latest best evidence is `production_entry_replay` run #7:

- 15m timeframe, 4-week-ish historical candles
- 1442 production candidates
- 310 duplicate-blocked
- 399 adaptive-blocked
- 686 trades
- WR 49.4%
- ExpR +0.11
- Avg MFE 8.33
- Avg MAE 6.36
- Max loss streak 8

## Historical Candle Coverage

| Timeframe | Bars | First UTC | Last UTC | Span |
|---|---:|---|---|---:|
| 5m | 6162 | 2026-07-05T22:00:00+00:00 | 2026-08-05T05:25:00+00:00 | 30.31 days |
| 15m | 2688 | 2026-06-24T19:30:00+00:00 | 2026-08-05T05:15:00+00:00 | 41.41 days |
| 1h | 2688 | 2026-02-20T00:00:00+00:00 | 2026-08-05T05:00:00+00:00 | 166.21 days |

## Completed Phases

### Phase 1 — Analyst Evidence Report

Purpose: analyze real DB outcomes before changing logic.

Known report metrics from DB:

- Closed outcomes: 37
- Win: 21
- Loss: 15
- BE/neutral: 1
- Overall win rate: 56.8%
- Expectancy: +0.55R
- BUY: 36 trades, WR 58.3%, ExpR +0.57
- SELL: 1 trade only, insufficient sample
- London/NY overlap: 33 trades, WR 60.6%, ExpR +0.62
- Duplicate-zone behavior existed in historical data: 26/37 trades near duplicates within 45 minutes
- Stale linked orders >10 minutes: 0

### Phase 1B — Data Capture Fields

Purpose: capture future calibration data without changing trading logic.

Added analytics fields to future orders/scalp watches:

- `order_score`
- `setup_score`
- `setup_type`
- `session_label`
- metadata JSON

Constraint: historical outcomes still have 0/37 coverage for these new fields until new orders close.

### Phase 2A — TradingView Historical Candle Storage

Purpose: collect candles from TradingView and store locally in SQLite.

Added:

- `historical_candles`
- `historical_fetch_runs`
- `scripts/collect_tradingview_history.py`
- `src/tradingview_mcp/core/services/tradingview_history_service.py`

Important note: collector uses TradingView chart websocket and stores candles by bars, not by calendar period.

### Phase 2B — DB Historical Candle Backtesting

Purpose: run deterministic strategy-family backtests from `historical_candles`.

Added:

- `backtest_runs`
- `backtest_trades`
- `scripts/run_historical_backtest.py`
- `src/tradingview_mcp/core/services/historical_backtest_service.py`

Initial strategy families:

- `ema_trend`
- `bollinger_rejection`

Initial real DB runs:

| Run | Strategy | TF | Trades | WR | ExpR | Max Loss Streak |
|---:|---|---|---:|---:|---:|---:|
| 1 | ema_trend | 5m | 1 | 100.0% | +1.20 | 0 |
| 2 | bollinger_rejection | 15m | 5 | 40.0% | -0.12 | 3 |

### Phase 2C — Approximate Live-Logic Replay

Purpose: approximate current live Telegram entry behavior over historical candles before touching real logic.

Added strategy:

- `live_logic_replay`

Logic covered:

- EMA/RSI/Bollinger rejection/continuation
- score gate
- RSI hot/cold guard
- 45m duplicate-zone guard

Results:

| Run | Strategy | Gate | Trades | WR | ExpR | Avg MFE | Avg MAE | Max Loss Streak |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 3 | live_logic_replay | 70 | 778 | 36.5% | -0.07 | 7.45 | 7.93 | 12 |
| 4 | live_logic_replay | 85 | 185 | 34.1% | -0.15 | 7.16 | 9.25 | 9 |

MGT finding: approximate replay was negative expectancy. Do not loosen entry logic.

### Phase 2D — Filter Optimization

Purpose: test evidence-only filters before any production change.

Added controls:

- `allowed_sessions`
- `allowed_directions`
- `allowed_setups`
- `mtf_filter`
- 1h EMA20/EMA50 MTF alignment

Added optimizer:

- `scripts/optimize_live_logic_filters.py`

Optimizer tested 588 combinations.

Best small-sample candidate:

| Run | Filter | Trades | WR | ExpR | Max Loss Streak |
|---:|---|---:|---:|---:|---:|
| 5 | SELL rejection only, Asia+NY/late, 1h with-trend, gate 70 | 23 | 47.8% | +0.18 | 4 |

Best high-confidence candidate, min 100 trades:

| Run | Filter | Trades | WR | ExpR | Avg MFE | Avg MAE | Max Loss Streak |
|---:|---|---:|---:|---:|---:|---:|---:|
| 6 | SELL only, Asia+NY/late, 1h with-trend, gate 70 | 162 | 39.5% | +0.07 | 7.20 | 7.29 | 6 |

MGT finding: filters can make replay slightly positive, but margin is thin. Need exact production replay before touching real alerts.

### Exact Production-Entry Replay

Purpose: follow MGT decision to replay production-like deterministic entry behavior before touching live logic.

Added strategy:

- `production_entry_replay`

Mirrored production concepts:

- hard floor score >=70
- XAUUSD SL band 5–8 price units
- entry-zone derivation
- duplicate/open same-side guard
- 45m recent similar-zone guard
- 90m/adaptive loss guard
- RSI hot/cold guard

Constraint:

- This uses historical candles to synthesize the original `trade_signals` technical payload.
- It is closer to production entry-alert behavior than Phase 2C.
- It is still not byte-for-byte replay of every live collector payload.
- No production Telegram/order logic was changed.

Run #7 summary:

| Metric | Value |
|---|---:|
| Production candidates | 1442 |
| Duplicate blocked | 310 |
| Adaptive blocked | 399 |
| Trades | 686 |
| Wins | 339 |
| Losses | 306 |
| Win rate | 49.4% |
| Expectancy | +0.11R |
| Avg MFE | 8.33 |
| Avg MAE | 6.36 |
| Max loss streak | 8 |

Run #7 breakdown by session:

| Session | Trades | WR | ExpR |
|---|---:|---:|---:|
| Asia | 261 | 56.3% | +0.19 |
| London/NY overlap | 148 | 48.0% | +0.15 |
| London | 157 | 46.5% | ~0.00 |
| NY/late | 120 | 40.0% | +0.04 |

Run #7 breakdown by direction:

| Direction | Trades | WR | ExpR |
|---|---:|---:|---:|
| SELL | 306 | 50.0% | +0.16 |
| BUY | 380 | 48.9% | +0.07 |

MGT finding:

- Exact production-entry replay is materially better than approximate rejection replay.
- Overall positive expectancy: +0.11R.
- Asia and SELL are strongest segments.
- Still needs shadow/paper validation before real production logic change.

## Git Commits Pushed

| Commit | Message |
|---|---|
| 3d88c47 | feat: add trad phase 1 analytics tracking |
| 4aa8e49 | feat: store TradingView historical candles |
| babb250 | feat: add historical candle backtesting |
| 3b1adf0 | feat: add live logic replay backtest |
| e4af19d | feat: add live logic filter optimization |
| af84f62 | feat: add production entry replay backtest |

Latest pushed HEAD:

- `af84f62 (HEAD -> main, origin/main, origin/HEAD) feat: add production entry replay backtest`

## Verification

Latest test status:

- `python3 -m py_compile ...` passed
- `uv run pytest tests/unit/services/test_historical_backtest_service.py tests/unit/services/test_tradingview_history_service.py tests/unit/jobs/test_score_latest_signal.py` passed
- Result: 9 passed

## Current Recommendation

Do not change production Telegram/order logic yet.

Recommended next step:

1. Run shadow/paper validation using `production_entry_replay` assumptions.
2. Compare new real alerts/outcomes with replay predictions.
3. If confirmed, propose a small production change only for the strongest segment first:
   - Asia session
   - SELL side
   - keep duplicate/adaptive guards active
4. Commit/push only after tests and real DB verification.
