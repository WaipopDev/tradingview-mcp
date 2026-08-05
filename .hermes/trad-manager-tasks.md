# Trad Manager Task List

Owner: MGT (Trad Manager Agent)
Scope: MGT supervises Trad, Dashboard, Backend, Data, DevOps, and Other tasks. Primary repo/runtime paths: /Users/waipop/MainWTN/Hermes/trad and local runtime scripts under /Users/waipop/.hermes/scripts
Last autonomous review: 2026-08-05 08:18 ICT

## Workflow
1. Waipop talks to Manager as the control point.
2. Manager reads Analyst reports and DB evidence; never guesses.
3. MGT maintains task lists by department before/after work.
4. Departments: Trad, Dashboard, Backend, Data, DevOps, Other.
5. MGT may propose work to Waipop. Apply code/config changes only when approved or explicitly requested.
6. After each completed change: verify with scripts/tests, review result, then commit/push repo changes when applicable.
7. Runtime-only Hermes scripts/config under ~/.hermes/scripts are local and not committed unless mirrored into the repo intentionally.
8. Routine no-risk/no-open-order WAIT status should stay silent; report only material changes, risks, or approval requests.
9. Language policy: MGT talks to Waipop in concise Thai; internal prompts/briefs to departments or specialists are English.

## Department task intake

### Trad
- [ ] Monitor XAUUSD automation quality: duplicate entries, WAIT_CONFIRMATION filtering, SL 500–800 point rule, stale data, BE/partial outcomes.
- [ ] Review Analyst recommendations every 15 minutes and propose only actionable changes.

### Dashboard
- [ ] Intake pending: no approved dashboard task yet.

### Backend
- [ ] Intake pending: no approved backend task yet.

### Data
- [ ] Phase 2D approved 2026-08-05: optimize live_logic_replay with evidence-only filters (session, direction, setup, 1h MTF trend alignment) and store best candidates before any production logic change.
- [ ] Phase 2C approved 2026-08-05: replay approximate current live Telegram entry logic over historical candles using `live_logic_replay`; evaluate score gate, duplicate guard, session, setup_type, ATR SL/RR TP before modifying live logic.
- [ ] Phase 2B approved 2026-08-05: run DB-backed historical candle backtests from `historical_candles`, store `backtest_runs`/`backtest_trades`, start with `ema_trend` and `bollinger_rejection` strategy families.
- [ ] Phase 2A approved 2026-08-05: collect TradingView historical XAUUSD/OANDA candles into DB (`historical_candles`, `historical_fetch_runs`) for later backtesting; start with 5m/15m/1h.
- [ ] Phase 1B approved 2026-08-05: persist analytics fields on new alerts only — `order_score`/`setup_score`, `setup_type`, `session_label`, and metadata JSON; do not change trading logic.
- [ ] Phase 1 approved 2026-08-05: build/generate Analyst evidence report from DB: session, direction, setup type, score band, MFE/MAE, expectancy/R, duplicate-zone behavior, and stale-data impact.
- [ ] Monitor `trade_signals`, `market_snapshots`, `trade_plan_outcomes`, and evaluation metrics.

### DevOps
- [ ] Phase 1 approved 2026-08-05: keep Analyst low-token/local; do not spam Telegram; only resume cron after report path is verified.
- [ ] Monitor cron/runtime reliability and commit/push hygiene.

### Other
- [ ] Intake pending: classify new work before execution.

## Approved / active work

- [ ] 2026-08-05: Phase 1 Data Analytics for MGT/Analyst approved by Waipop; first evidence report generated and verified.
  - Data: add/generate Analyst report metrics by session (Asia/London/NY/overlap), direction (BUY/SELL), setup type (rejection/breakout/continuation/pullback/scalp-watch), score band, MFE/MAE, expectancy/R, duplicate-zone behavior, and stale-data impact.
  - Report script: `/Users/waipop/.hermes/scripts/trad_phase1_analytics_report.py`
  - Latest report: `/Users/waipop/MainWTN/Hermes/trad/.hermes/phase1-analytics-report.md`
  - Next proposed improvement (needs Waipop approval before trading-logic/data-schema changes): persist `order_score`/`setup_score` and explicit `setup_type` when creating Order/Scalp Watch.
  - MGT: summarize findings in concise Thai only when material; do not auto-patch trading logic without Waipop approval.
  - DevOps: keep Analyst low-token/local and no Telegram spam; resume cron only if Waipop wants periodic report runs.

- [ ] 2026-08-05: Phase 1B Data Capture approved by Waipop; implemented and verified locally.
  - Scope: persist analytics fields for new Order/Scalp Watch alerts only: `order_score`/`setup_score`, `setup_type`, `session_label`, and metadata JSON.
  - Constraint: no trading logic/threshold changes in Phase 1B; evidence only.
  - Verification: runtime scripts compile, DB columns exist, dry-runs did not send alerts, and Phase 1 report shows field coverage (historical coverage remains 0 until new alerts close).

- [ ] 2026-08-05: Phase 2A Historical TradingView Candle Storage approved by Waipop; implemented and verified.
  - Scope: DB schema + collector for OANDA:XAUUSD historical candles in 5m/15m/1h.
  - Tables: `historical_candles`, `historical_fetch_runs`.
  - Collector: `scripts/collect_tradingview_history.py` using TradingView chart websocket.
  - Verification: collected 100 bars each for 5m/15m/1h into `/Users/waipop/.tradingview-mcp/trading_signals.sqlite3`; targeted tests passed.
  - Constraint: Phase 2A stores candles only; backtest engine/logic replay is Phase 2B.

- [ ] 2026-08-05: Phase 2B Historical DB Backtest approved by Waipop; implemented and verified.
  - Scope: read `historical_candles`, run deterministic strategy-family backtests, store `backtest_runs`/`backtest_trades`.
  - CLI: `scripts/run_historical_backtest.py`.
  - Strategies: `ema_trend`, `bollinger_rejection` with score gate, ATR SL, RR TP, max-hold bars.
  - Verification: targeted tests passed; real DB runs stored run #1 (5m ema_trend: 1 trade, WR 100%, ExpR 1.20) and run #2 (15m bollinger_rejection: 5 trades, WR 40%, ExpR -0.12).
  - Constraint: Phase 2B tests strategy families; exact live Telegram order-logic replay remains Phase 2C.

- [ ] 2026-08-05: Phase 2C Historical Live-Logic Replay approved by Waipop; implemented and verified.
  - Data expansion: collected 4-week target candles; DB now has 5m=6162 bars (~30.3 calendar days), 15m=2688 bars (~41.4 days), 1h=2688 bars (~166 days; more than requested, useful as MTF context).
  - Logic: `live_logic_replay` approximates current Telegram entry gates using EMA/RSI/Bollinger rejection/continuation, score gate, RSI hot/cold guard, and 45m duplicate-zone guard; no live trading side effects.
  - Verification: score_gate 70 run #3 produced 778 trades, WR 36.5%, ExpR -0.07; score_gate 85 run #4 produced 185 trades, WR 34.1%, ExpR -0.15, max loss streak 9.
  - MGT finding: current approximate rejection-heavy replay is negative expectancy over the stored sample; do not loosen live entry rules. Next optimization should test stricter MTF/session filters before changing production alerts.

- [ ] 2026-08-05: Phase 2D Filter Optimization approved by Waipop; implemented and verified.
  - Scope: evidence-only filter experiments for `live_logic_replay`; no production entry/order logic changed.
  - Added controls: `allowed_sessions`, `allowed_directions`, `allowed_setups`, `mtf_filter` (`off`, `with_trend`, `strict_with_trend`, `rejection_countertrend_only`) and 1h EMA20/EMA50 MTF alignment.
  - Optimizer: `scripts/optimize_live_logic_filters.py` tested 588 combinations on the 4-week-ish DB sample.
  - High-confidence candidate (min 100 trades, stored run #6): SELL only, sessions Asia+NY/late signal filter, 1h with-trend, score_gate 70; 162 trades, WR 39.5%, ExpR +0.07, avg MFE 7.20, avg MAE 7.29, max loss streak 6.
  - Small-sample candidate (stored run #5): SELL rejection only, Asia+NY/late, 1h with-trend, 23 trades, WR 47.8%, ExpR +0.18, max loss streak 4; promising but needs more data before production.
  - MGT finding: filters can turn replay positive, but margin is small; propose paper-mode/shadow validation and exact production-logic replay before changing Telegram alerts.

## Proposed / awaiting Waipop approval

- None.

## Completed / verified
- 2026-08-05: Approved MGT scalp improvement implemented: after same-zone Scalp Watch non-TP/CUT/SL, block repeated scalp alerts in that trigger band unless the new setup score is stronger (>=65 after BE/PARTIAL_BE, >=70 after repeated non-TP, >=75 after CUT/SL). Verified with dry-run guard for recent Scalp #41 CUT.
- 2026-08-05: Established Manager/Analyst workflow and task-list policy.
- 2026-08-05: Approved proposal implemented locally; repo side updated for market_snapshots persistence.
- 2026-08-05: Checked DB tables and outcome summary; verified latest signal was WAIT_CONFIRMATION and no open orders at review time.
- 2026-08-05: Manager Agent prompt updated to stay silent on routine no-risk/no-open-order status and report only material changes or approval requests.
- 2026-08-05: MGT scope expanded to accept/categorize Dashboard, Backend, Data, DevOps, and Other department tasks.
- 2026-08-05: Approved Trad proposals completed locally: tighter 45m duplicate-zone guard, 90m post-SL/CUT pause requiring TRADE+score>=85, and normalized management-alert cooldown to reduce PROTECT/MOVE_SL_BE spam.
- 2026-08-05 08:21 ICT: Waipop approved hard global auto-entry floor; deterministic Telegram entry alerts now require `decision=TRADE` and script/order score >=70 before sending.
