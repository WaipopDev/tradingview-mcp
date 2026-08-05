# Historical SMC Feature Combination Analysis

Generated: 2026-08-05T09:03:21.491608+00:00 UTC
Backtest run: #7 OANDA:XAUUSD 15m production_entry_replay
Date range: 2026-06-24T19:30:00+00:00 → 2026-08-05T05:15:00+00:00
Mode: read-only feature/filter analysis; production entry logic unchanged.
Feature lag bars: 1 (0=same entry candle, 1=prior closed candle / safer anti-lookahead check)

## Baseline
- Trades: 686 | WR 49.4% | ExpR 0.112 | max loss streak 8 | MFE 8.33 | MAE 6.36
- Trades joined to SMC features: 683/686

## Direction/session baseline
- SELL Asia: trades 128 | WR 57.0% | ExpR 0.260 | maxLS 8
- SELL London/NY overlap: trades 53 | WR 50.9% | ExpR 0.215 | maxLS 6
- SELL NY/late: trades 53 | WR 41.5% | ExpR 0.201 | maxLS 4
- BUY Asia: trades 133 | WR 55.6% | ExpR 0.122 | maxLS 5
- BUY London/NY overlap: trades 95 | WR 46.3% | ExpR 0.114 | maxLS 6
- BUY London: trades 85 | WR 49.4% | ExpR 0.059 | maxLS 5
- SELL London: trades 72 | WR 43.1% | ExpR -0.074 | maxLS 7
- BUY NY/late: trades 67 | WR 38.8% | ExpR -0.079 | maxLS 12

## Top feature/filter simulations (min trades=100)
- require any: order_block+order_flow_proxy: trades 114 (16.6%) | WR 57.0% | ExpR 0.256 (Δ +0.144) | maxLS 6 | MFE 9.58 MAE 6.20
- require any: liquidity_sweep+order_block+order_flow_proxy: trades 114 (16.6%) | WR 57.0% | ExpR 0.256 (Δ +0.144) | maxLS 6 | MFE 9.58 MAE 6.20
- require any: order_block+price_action_confirm: trades 143 (20.8%) | WR 54.5% | ExpR 0.247 (Δ +0.135) | maxLS 7 | MFE 8.74 MAE 5.99
- require any: liquidity_sweep+order_block+price_action_confirm: trades 143 (20.8%) | WR 54.5% | ExpR 0.247 (Δ +0.135) | maxLS 7 | MFE 8.74 MAE 5.99
- require any: choch+order_block+price_action_confirm: trades 151 (22.0%) | WR 54.3% | ExpR 0.238 (Δ +0.126) | maxLS 8 | MFE 8.79 MAE 5.97
- require any: liquidity_sweep+choch+order_block+price_action_confirm: trades 151 (22.0%) | WR 54.3% | ExpR 0.238 (Δ +0.126) | maxLS 8 | MFE 8.79 MAE 5.97
- require any: choch+order_block+order_flow_proxy: trades 120 (17.5%) | WR 55.8% | ExpR 0.229 (Δ +0.117) | maxLS 7 | MFE 9.53 MAE 6.25
- require any: liquidity_sweep+choch+order_block+order_flow_proxy: trades 120 (17.5%) | WR 55.8% | ExpR 0.229 (Δ +0.117) | maxLS 7 | MFE 9.53 MAE 6.25
- require any: bos+order_block+order_flow_proxy: trades 134 (19.5%) | WR 54.5% | ExpR 0.226 (Δ +0.114) | maxLS 5 | MFE 9.50 MAE 6.14
- require any: liquidity_sweep+bos+order_block+order_flow_proxy: trades 134 (19.5%) | WR 54.5% | ExpR 0.226 (Δ +0.114) | maxLS 5 | MFE 9.50 MAE 6.14
- require any: choch+bos+order_block+order_flow_proxy: trades 134 (19.5%) | WR 54.5% | ExpR 0.226 (Δ +0.114) | maxLS 5 | MFE 9.50 MAE 6.14
- require any: bos+order_block: trades 102 (14.9%) | WR 53.9% | ExpR 0.220 (Δ +0.108) | maxLS 5 | MFE 9.10 MAE 6.16
- require any: liquidity_sweep+bos+order_block: trades 102 (14.9%) | WR 53.9% | ExpR 0.220 (Δ +0.108) | maxLS 5 | MFE 9.10 MAE 6.16
- require any: choch+bos+order_block: trades 102 (14.9%) | WR 53.9% | ExpR 0.220 (Δ +0.108) | maxLS 5 | MFE 9.10 MAE 6.16
- require any: liquidity_sweep+choch+bos+order_block: trades 102 (14.9%) | WR 53.9% | ExpR 0.220 (Δ +0.108) | maxLS 5 | MFE 9.10 MAE 6.16

## Individual feature support
- ema_trend=direction: trades 683 | WR 49.3% | ExpR 0.110
- liquidity_sweep=direction: trades 1 | WR 100.0% | ExpR 0.686
- choch=direction: trades 11 | WR 54.5% | ExpR 0.191
- bos=direction: trades 42 | WR 45.2% | ExpR 0.075
- fvg=direction: trades 54 | WR 40.7% | ExpR -0.086
- order_block=direction: trades 69 | WR 59.4% | ExpR 0.313
- price_action_confirm=direction: trades 108 | WR 51.9% | ExpR 0.195
- order_flow_proxy=direction: trades 82 | WR 57.3% | ExpR 0.276

## Practical reading
- Best paper filter: require any: order_block+order_flow_proxy with ExpR 0.256, but coverage 114/686. Treat as hypothesis, not production approval.
- Prefer filters that improve ExpR and reduce max loss streak without cutting sample size too aggressively.
- Next safe step: manually inspect top 2-3 filters and then run sequence-aware managed-exit replay before production entry filtering.
