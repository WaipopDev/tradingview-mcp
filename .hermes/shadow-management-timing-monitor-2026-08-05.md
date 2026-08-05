# Shadow Management Timing Monitor — XAUUSD

Generated: 2026-08-05T06:56:59.031730+00:00 UTC
DB: /Users/waipop/.tradingview-mcp/trading_signals.sqlite3
Mode: READ-ONLY paper monitor; no production DB/code mutation.

## Current open-order shadow actions
- Open orders: 0
- No paper MOVE_SL_BE / TAKE_PARTIAL / PROTECT trigger on currently open orders.

## Closed-order missed-protection scan, last 50 closed outcomes
- Missed-protection cases: 5
- #30 telegram_entry_alert BUY result=SL MFE=9.88 MAE=0.00 risk≈8.00 TP1_progress=99.0% | MFE>=5 (9.88)
- #31 telegram_entry_alert BUY result=SL MFE=8.57 MAE=0.65 risk≈8.80 TP1_progress=91.6% | MFE>=5 (8.57)
- #32 telegram_entry_alert BUY result=SL MFE=6.89 MAE=2.33 risk≈8.80 TP1_progress=71.4% | MFE>=5 (6.89)
- #33 telegram_entry_alert BUY result=SL MFE=6.64 MAE=2.58 risk≈8.00 TP1_progress=63.5% | MFE>=5 (6.64)
- #34 telegram_entry_alert BUY result=CUT MFE=7.22 MAE=2.00 risk≈5.36 TP1_progress=54.3% | MFE>=5 (7.22)

## Paper recommendation
- Keep production unchanged. Next shadow test should tune management timing thresholds on the missed-protection cluster before any live logic patch.
