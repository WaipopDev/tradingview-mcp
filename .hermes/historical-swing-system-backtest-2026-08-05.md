# Historical Swing System Backtest Report

Generated: 2026-08-05
Instrument: OANDA:XAUUSD 15m
Mode: shadow/historical swing system; production entry logic unchanged.
Baseline production_entry_replay run #7: trades 686, WR 49.4%, ExpR +0.112, max loss streak 8.

## Detector output
- Candles: 2,688
- Swing pivots: 397
- Swing setups detected: 528 (BUY 232 / SELL 296)

## Backtest variants
| Variant | Trades | WR | ExpR | Wins | Losses | Time exits | Max LS | Avg MFE | Avg MAE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| score55_partial3 | 235 | 83.8% | 0.069 | 197 | 33 | 5 | 3 | 6.28 | 7.79 |
| score55_partial5 | 235 | 71.1% | -0.048 | 167 | 60 | 8 | 6 | 7.90 | 10.30 |
| score65_partial3 | 118 | 88.1% | 0.129 | 104 | 11 | 3 | 2 | 7.05 | 7.63 |
| score65_partial5 | 118 | 78.0% | 0.068 | 92 | 21 | 5 | 2 | 9.04 | 10.48 |
| score75_partial3 | 50 | 90.0% | 0.168 | 45 | 4 | 1 | 1 | 7.34 | 7.21 |
| score75_partial5 | 50 | 78.0% | 0.048 | 39 | 9 | 2 | 2 | 8.66 | 10.59 |
| score65_no_partial | 118 | 16.9% | -0.071 | 20 | 48 | 50 | 15 | 17.55 | 18.61 |
| score65_partial3_overlap | 46 | 89.1% | 0.151 | 41 | 3 | 2 | 1 | 8.41 | 8.16 |
| score65_partial3_asia_overlap | 92 | 88.0% | 0.136 | 81 | 8 | 3 | 1 | 7.28 | 7.84 |

## Key reading
- Swing setup without partial/BE protection is negative: score65_no_partial ExpR -0.071, max loss streak 15.
- Best all-session parameter so far: score65_partial3 — trades 118, WR 88.1%, ExpR +0.129, maxLS 2. It beats baseline ExpR +0.112 slightly and reduces loss streak sharply, but most wins are partial/BE-style locks, not full TP.
- score65_partial5 is safer relative to current production management threshold but ExpR only +0.068, below baseline; use as Swing Watch, not replacement.
- London/NY overlap with partial3 looks strongest but sample is only 46 trades; needs more data before session hard-filter.
- The swing system is useful as a filter/watch layer: detect HL/LH + SMC confluence, then manage early. It is not ready to replace production entries yet.

## Next validation needed before production
1. Add BUY/SELL split report and inspect setups where swing signal conflicts with production entry.
2. Tune TP model: current TP is too far; full TP hit is low, edge comes mostly from partial.
3. Run on more history / multiple market regimes, not just 2026-06-24 → 2026-08-05.
4. Only after that, add Swing Watch alerts first, not auto-entry.
