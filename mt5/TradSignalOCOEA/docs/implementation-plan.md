# TradSignalOCOEA Implementation Plan

> **For Hermes:** Use subagent-driven-development discipline: test first, then implement and independently review.

**Goal:** Build a new MT5 XAUUSD execution model that acts only on a fresh, externally scored `trad` signal and holds at most one EA-owned position.

**Architecture:** `trad` remains the analytical layer (MTF/SMC/session/score/duplicate guards). The EA reads one CSV signal from MT5's Files sandbox, rejects malformed/stale/weak signals, and owns execution/risk cleanup only. It never averages down, martingales, or creates an unconditional grid.

**Tech stack:** MQL5, `CTrade`, MetaEditor 5, Python static validator.

**Evidence applied:** The current replay supports only a thin overall edge (+0.11R) and identifies Asia (+0.19R) and SELL (+0.16R) as stronger cohorts. The operator subsequently selected full-day BUY+SELL Shadow coverage, so defaults are `ALL` sessions and `BOTH` sides while retaining score >=70 and all fail-closed risk controls.

---

### Task 1: Define a fail-closed signal contract

**Files:**
- Create: `signal-example.csv`
- Create: `README.md`

Contract: exactly one CSV data row after a header:
`signal_id,created_utc,side,entry,sl,tp1,tp2,score,session,expiry_utc`

The EA accepts `BUY` or `SELL` from any signal session when defaults are used, requires score >=70, a non-expired UTC timestamp, valid directional geometry, and one signal ID only once.

### Task 2: Implement safe single-position OCO execution

**Files:**
- Create: `TradSignalOCOEA.mq5`

Inputs include Magic, signal file, score/session/side gates, fixed lot, max spread/slippage, expiry, daily loss/equity DD controls, and immediate OCO behavior. The EA supports one primary pending entry at a time; it can optionally place a protective opposite stop only after a primary entry, but V1 defaults this off to prevent unvalidated reversal churn. Every trading action checks `ResultRetcode`; owned exposure is Symbol+Magic scoped.

### Task 3: Verify deterministic requirements

**Files:**
- Create: `tools/validate_ea.py`
- Create: `tools/test_validate_ea.py`

Start with a failing test that requires required source safety markers, signal contract documentation, and then—after a real compile—artifact/report hash consistency.

### Task 4: Compile and validate

**Files:**
- Create: `build/TradSignalOCOEA.ex5`
- Create: `build/compile-report.txt`
- Create: `presets/XAUUSD-AllDay-Both-Shadow.set`
- Create: `docs/backtest-plan.md`

Use isolated MetaEditor compilation. Require log evidence of 0 errors/0 warnings, artifact existence, SHA-256 report, and static validation. Strategy Tester and Demo gates remain required before live use.
