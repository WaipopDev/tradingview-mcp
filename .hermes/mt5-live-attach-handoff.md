# MT5 SteevStyleGridEA live attach task

Execute this task now on the local macOS desktop. Do not ask for clarification.

## Goal
Use macOS Computer Use (Accessibility has now been granted) to attach the already compiled and installed `SteevStyleGridEA` v1.02 to the currently running MetaTrader 5 chart `GOLD,H1`, enable global AutoTrading and per-EA Allow Algo Trading, load the verified preset, and verify actual pending orders and logs.

## Current state
- MetaTrader 5 app is currently running.
- Active MT5 install/data root:
  `/Users/waipop/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5`
- EA source and EX5 are already installed under:
  `MQL5/Experts/SteevStyleGridEA/SteevStyleGridEA.mq5`
  `MQL5/Experts/SteevStyleGridEA/SteevStyleGridEA.ex5`
- Preset is installed at:
  `MQL5/Profiles/Presets/SteevStyleGridEA-GOLD-H1.set`
- Repository source:
  `/Users/waipop/MainWTN/Hermes/trad/mt5/SteevStyleGridEA`
- Build was verified by MetaEditor: 0 errors, 0 warnings.
- Final EX5 SHA-256:
  `d5013b25ed314a29d9c033d04ec59fefcccf0facc07ef17817639383ec0906f8`
- Current terminal account is connected, hedging mode, and reported zero positions/orders at the last startup.
- Current MQL5 Experts log has no new SteevStyleGridEA entries after restart, proving the EA is not attached.

## Required actions
1. Load the `macos-computer-use` and `metatrader-ea-development` skills.
2. Capture the MetaTrader 5 window with Computer Use before clicking.
3. If a startup/EA Properties dialog is open, inspect it and finish it safely. Otherwise:
   - activate/open a `GOLD,H1` chart;
   - use Navigator → Expert Advisors → `SteevStyleGridEA` and attach it to the chart.
4. In EA Properties:
   - ensure `Allow Algo Trading` is enabled;
   - load `SteevStyleGridEA-GOLD-H1.set` from Presets;
   - verify Symbol is GOLD and timeframe H1 before clicking OK;
   - do not change account, Magic Number, other charts, or unrelated orders.
5. Ensure the terminal global AutoTrading/Algo Trading button is enabled.
6. Verify through Experts/Journal and live Trade tab that the new EA actually initialized and placed the grid. Required proof should include new events equivalent to:
   - `Persistent risk lock cleared on init.`
   - `Persistent risk lock restored: OFF`
   - `SGRID initialized on GOLD. Mode=HEDGE, levels=5, lot=0.01`
   - `Grid placed ... BUY STOP=5, SELL STOP=5`
   - ten total SteevStyleGridEA pending orders for GOLD (5 BUY STOP and 5 SELL STOP), isolated by its Magic/comment.
7. If AutoTrading is disabled and order sends return retcode 10027, enable it and verify the grid is retried successfully.
8. If the broker rejects orders, report exact retcode/message and do not fabricate success.
9. Leave MT5 running when finished. Return a concise Thai result with exact verified evidence.

## Expected EA behavior/settings
- Version 1.02
- Mode HEDGE
- Lot 0.01
- Levels 5 per side (the EA now allows any positive level count; caps were removed)
- Initial offset 200 points
- Spacing 200 points
- SL 700 points
- TP 1200 points
- Basket TP 5 USD
- Basket SL 20 USD
- Restart immediately after Basket SL = true
- Daily Loss and Equity Drawdown controls removed
