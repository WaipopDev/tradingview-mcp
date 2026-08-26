# MT5MarketDataBridge

Read-only MT5 custom indicator that exports broker-native `GOLD` quotes and technical context for Hermes/MGT. It contains no `CTrade`, order placement, position management, or account mutation.

## Output

Default path inside the live terminal data directory:

```text
MQL5/Files/MT5MarketDataBridge/GOLD.json
```

The snapshot is refreshed every second and contains:

- broker, symbol, Bid, Ask, spread, point, digits, broker tick timestamp
- M15, H1, H4, D1 current/previous OHLC and tick volume
- RSI(14), ATR(14), EMA 20/50/200, MACD(12,26,9), Bollinger(20,2), ADX(14)
- local support/resistance and average tick volume

Hermes reads it through `mt5_market_data_service.py`, which fails closed for malformed data, symbol mismatch, invalid quotes, missing timeframes, or stale ticks.

## Installation status

- Compiled as a **Custom Indicator**: `0 errors, 0 warnings`
- Source and EX5 copied to live `MQL5/Indicators/MT5MarketDataBridge/`
- Installed files are byte-matched with repository artifacts
- **Not attached yet**: installing the EX5 does not prove runtime output

## Attach safely

Attach `Indicators → MT5MarketDataBridge → MT5MarketDataBridge` to any live chart. As an indicator it can coexist with an EA and does not replace the chart EA. Keep `InpSymbol=GOLD`.

Runtime proof requires both:

```text
MT5BRIDGE initialized v1.00 symbol=GOLD
```

and a fresh valid `MQL5/Files/MT5MarketDataBridge/GOLD.json` whose tick age is below five seconds.

Do not switch MGT production from TradingView to MT5 until this proof and shadow comparison pass.
