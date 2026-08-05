# Historical SMC Feature Combination Analysis

Generated: 2026-08-05T09:01:25.070267+00:00 UTC
Backtest run: #7 OANDA:XAUUSD 15m production_entry_replay
Date range: 2026-06-24T19:30:00+00:00 → 2026-08-05T05:15:00+00:00
Mode: read-only feature/filter analysis; production entry logic unchanged.

## Baseline
- Trades: 686 | WR 49.4% | ExpR 0.112 | max loss streak 8 | MFE 8.33 | MAE 6.36
- Trades joined to SMC features: 686/686

## Direction/session baseline
- SELL Asia: trades 128 | WR 57.0% | ExpR 0.260 | maxLS 8
- SELL London/NY overlap: trades 53 | WR 50.9% | ExpR 0.215 | maxLS 6
- SELL NY/late: trades 53 | WR 41.5% | ExpR 0.201 | maxLS 4
- BUY Asia: trades 133 | WR 55.6% | ExpR 0.122 | maxLS 5
- BUY London/NY overlap: trades 95 | WR 46.3% | ExpR 0.114 | maxLS 6
- BUY London: trades 85 | WR 49.4% | ExpR 0.059 | maxLS 5
- SELL London: trades 72 | WR 43.1% | ExpR -0.074 | maxLS 7
- BUY NY/late: trades 67 | WR 38.8% | ExpR -0.079 | maxLS 12

## Top feature/filter simulations (min trades=30)
- require order_block=direction: trades 47 (6.9%) | WR 93.6% | ExpR 1.024 (Δ +0.912) | maxLS 1 | MFE 12.63 MAE 1.55
- require all: ema_trend+order_block: trades 47 (6.9%) | WR 93.6% | ExpR 1.024 (Δ +0.912) | maxLS 1 | MFE 12.63 MAE 1.55
- SMC supportive score >= 4: trades 37 (5.4%) | WR 94.6% | ExpR 1.008 (Δ +0.896) | maxLS 1 | MFE 13.86 MAE 1.91
- require any: choch+order_block: trades 59 (8.6%) | WR 93.2% | ExpR 1.000 (Δ +0.888) | maxLS 1 | MFE 13.14 MAE 1.83
- require any: bos+order_block: trades 96 (14.0%) | WR 91.7% | ExpR 0.986 (Δ +0.874) | maxLS 1 | MFE 13.53 MAE 1.95
- require any: choch+bos+order_block: trades 96 (14.0%) | WR 91.7% | ExpR 0.986 (Δ +0.874) | maxLS 1 | MFE 13.53 MAE 1.95
- require all: bos+order_flow_proxy: trades 36 (5.2%) | WR 94.4% | ExpR 0.983 (Δ +0.871) | maxLS 1 | MFE 15.90 MAE 2.18
- require all: ema_trend+bos+order_flow_proxy: trades 36 (5.2%) | WR 94.4% | ExpR 0.983 (Δ +0.871) | maxLS 1 | MFE 15.90 MAE 2.18
- require bos=direction: trades 64 (9.3%) | WR 90.6% | ExpR 0.947 (Δ +0.835) | maxLS 1 | MFE 14.00 MAE 2.15
- require all: ema_trend+bos: trades 64 (9.3%) | WR 90.6% | ExpR 0.947 (Δ +0.835) | maxLS 1 | MFE 14.00 MAE 2.15
- require any: choch+bos: trades 64 (9.3%) | WR 90.6% | ExpR 0.947 (Δ +0.835) | maxLS 1 | MFE 14.00 MAE 2.15
- SMC supportive score >= 3: trades 91 (13.3%) | WR 89.0% | ExpR 0.900 (Δ +0.788) | maxLS 2 | MFE 13.35 MAE 2.74
- require any: fvg+order_block: trades 87 (12.7%) | WR 87.4% | ExpR 0.894 (Δ +0.782) | maxLS 2 | MFE 12.34 MAE 2.41
- require any: bos+fvg+order_block: trades 118 (17.2%) | WR 87.3% | ExpR 0.885 (Δ +0.773) | maxLS 2 | MFE 13.08 MAE 2.55
- require any: choch+bos+fvg+order_block: trades 118 (17.2%) | WR 87.3% | ExpR 0.885 (Δ +0.773) | maxLS 2 | MFE 13.08 MAE 2.55
- require any: choch+fvg+order_block: trades 93 (13.6%) | WR 87.1% | ExpR 0.882 (Δ +0.770) | maxLS 2 | MFE 12.66 MAE 2.55
- require any: order_block+order_flow_proxy: trades 109 (15.9%) | WR 86.2% | ExpR 0.857 (Δ +0.745) | maxLS 2 | MFE 13.51 MAE 2.88
- require any: bos+order_block+order_flow_proxy: trades 130 (19.0%) | WR 85.4% | ExpR 0.853 (Δ +0.741) | maxLS 2 | MFE 13.17 MAE 2.82
- require any: choch+bos+order_block+order_flow_proxy: trades 130 (19.0%) | WR 85.4% | ExpR 0.853 (Δ +0.741) | maxLS 2 | MFE 13.17 MAE 2.82
- require any: liquidity_sweep+bos+order_block: trades 103 (15.0%) | WR 85.4% | ExpR 0.851 (Δ +0.739) | maxLS 2 | MFE 12.82 MAE 2.66
- require any: liquidity_sweep+choch+bos+order_block: trades 103 (15.0%) | WR 85.4% | ExpR 0.851 (Δ +0.739) | maxLS 2 | MFE 12.82 MAE 2.66
- require any: choch+order_block+order_flow_proxy: trades 115 (16.8%) | WR 86.1% | ExpR 0.850 (Δ +0.739) | maxLS 2 | MFE 13.39 MAE 2.88
- require any: bos+order_flow_proxy: trades 115 (16.8%) | WR 85.2% | ExpR 0.841 (Δ +0.729) | maxLS 2 | MFE 13.28 MAE 2.94
- require any: choch+bos+order_flow_proxy: trades 115 (16.8%) | WR 85.2% | ExpR 0.841 (Δ +0.729) | maxLS 2 | MFE 13.28 MAE 2.94
- require order_flow_proxy=direction: trades 87 (12.7%) | WR 85.1% | ExpR 0.822 (Δ +0.710) | maxLS 2 | MFE 13.84 MAE 3.20
- require all: ema_trend+order_flow_proxy: trades 87 (12.7%) | WR 85.1% | ExpR 0.822 (Δ +0.710) | maxLS 2 | MFE 13.84 MAE 3.20
- require any: bos+fvg: trades 86 (12.5%) | WR 84.9% | ExpR 0.818 (Δ +0.706) | maxLS 2 | MFE 13.27 MAE 2.92
- require any: choch+bos+fvg: trades 86 (12.5%) | WR 84.9% | ExpR 0.818 (Δ +0.706) | maxLS 2 | MFE 13.27 MAE 2.92
- require any: choch+order_flow_proxy: trades 93 (13.6%) | WR 84.9% | ExpR 0.816 (Δ +0.704) | maxLS 2 | MFE 13.67 MAE 3.19
- require any: fvg+order_block+order_flow_proxy: trades 135 (19.7%) | WR 83.0% | ExpR 0.797 (Δ +0.685) | maxLS 3 | MFE 13.06 MAE 3.22

## Individual feature support
- ema_trend=direction: trades 684 | WR 49.4% | ExpR 0.112
- liquidity_sweep=direction: trades 7 | WR 0.0% | ExpR -1.000
- choch=direction: trades 13 | WR 92.3% | ExpR 0.899
- bos=direction: trades 64 | WR 90.6% | ExpR 0.947
- fvg=direction: trades 40 | WR 80.0% | ExpR 0.742
- order_block=direction: trades 47 | WR 93.6% | ExpR 1.024
- price_action_confirm=direction: trades 97 | WR 62.9% | ExpR 0.372
- order_flow_proxy=direction: trades 87 | WR 85.1% | ExpR 0.822

## Practical reading
- Best paper filter: require order_block=direction with ExpR 1.024, but coverage 47/686. Treat as hypothesis, not production approval.
- Prefer filters that improve ExpR and reduce max loss streak without cutting sample size too aggressively.
- Next safe step: manually inspect top 2-3 filters and then run sequence-aware managed-exit replay before production entry filtering.
