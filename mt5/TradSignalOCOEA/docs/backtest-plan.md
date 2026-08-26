# Tester and demo gate plan

1. Compile `TradSignalOCOEA.mq5` in isolated MetaEditor 5; preserve its report and SHA-256 alongside the generated `.ex5` in `build/`. Do not claim compile success without this evidence.
2. Strategy Tester: use broker-matched XAUUSD symbol, Every tick based on real ticks, realistic commission/slippage, and the `XAUUSD-AllDay-Both-Tester` preset. Place each test signal in that terminal instance's `MQL5/Files/trad_signal.csv`.
3. Exercise accepted BUY and SELL score 70+ signals across the broker day; test rejected low-score/stale/expired/duplicate/malformed/multi-row signals, buy/sell limit and stop selection, spread guard, daily loss lock, equity-DD lock, and close retry after a forced trade rejection.
4. Re-run out-of-sample dates and verify no more than one Symbol+Magic position/pending exists. Compare results with the underlying `trad` evidence; no optimization or live deployment is approved by this package.
5. Require a separate demo period with journal review of all CTrade retcodes, lock events, and full-close confirmations before considering any live-risk review.
