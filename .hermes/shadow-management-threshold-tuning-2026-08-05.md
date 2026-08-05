# Shadow Management Timing Threshold Tuning — production_entry_replay run #7

Generated: 2026-08-05T06:57:48.106552+00:00 UTC
DB: /Users/waipop/.tradingview-mcp/trading_signals.sqlite3
Mode: READ-ONLY aggregate what-if; does not mutate production logic/DB.

Baseline run #7: trades 686, wins 339, losses 306, WR 49.4%, ExpR 0.11

## What-if: convert SL to BE/PARTIAL_BE if MFE threshold was reached before final SL
Note: This uses stored trade-level MFE/MAE only, not intra-trade sequence, so it is an upper-bound paper estimate.
- MFE>=3: saved_loss_upper_bound 163 | losses 143 | BE 163 | WR unchanged 49.4% | ExpR_BE 0.35 | ExpR_partial≈0.41
- MFE>=4: saved_loss_upper_bound 126 | losses 180 | BE 126 | WR unchanged 49.4% | ExpR_BE 0.30 | ExpR_partial≈0.34
- MFE>=5: saved_loss_upper_bound 91 | losses 215 | BE 91 | WR unchanged 49.4% | ExpR_BE 0.24 | ExpR_partial≈0.28
- MFE>=6: saved_loss_upper_bound 56 | losses 250 | BE 56 | WR unchanged 49.4% | ExpR_BE 0.19 | ExpR_partial≈0.21
- MFE>=7: saved_loss_upper_bound 39 | losses 267 | BE 39 | WR unchanged 49.4% | ExpR_BE 0.17 | ExpR_partial≈0.18
- MFE>=8: saved_loss_upper_bound 22 | losses 284 | BE 22 | WR unchanged 49.4% | ExpR_BE 0.14 | ExpR_partial≈0.15

## Current live missed cluster check
- #30 BUY SL MFE=9.88 risk=8.00 TP1_progress=99.0%
- #31 BUY SL MFE=8.57 risk=8.80 TP1_progress=91.6%
- #32 BUY SL MFE=6.89 risk=8.80 TP1_progress=71.4%
- #33 BUY SL MFE=6.64 risk=8.00 TP1_progress=63.5%
- #34 BUY CUT MFE=7.22 risk=5.36 TP1_progress=54.3%

## Paper conclusion
- MFE>=5 is a useful shadow threshold because it catches all 5 live missed-protection cases and aligns with existing user preference/skill rule.
- Before production patch, run this monitor for more samples; if repeated, test a shadow rule: when MFE>=5 OR TP1 progress>=65%, persist TAKE_PARTIAL/MOVE_SL_BE even if reversal signal is weak/stale.
