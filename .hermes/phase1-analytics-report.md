# Phase 1 MGT/Analyst Evidence Report
Generated: 2026-08-05T04:21:38.052749+00:00 UTC
Scope: XAUUSD 15m, last 37 closed outcomes, scalp-watch alerts=1

## Overall
- n=37 win=21 loss=15 neutral=1 WR=56.8% MFE=8.50 MAE=3.22 ExpR=0.55
- Phase 1B field coverage: score=0/37, setup_type=0/37, session_label=0/37

## By direction
- BUY: n=36 win=21 loss=15 neutral=0 WR=58.3% MFE=8.47 MAE=3.25 ExpR=0.57
- SELL: n=1 win=0 loss=0 neutral=1 WR=0.0% MFE=9.62 MAE=1.96 ExpR=0.00

## By session
- London/NY overlap: n=33 win=20 loss=13 neutral=0 WR=60.6% MFE=8.88 MAE=3.11 ExpR=0.62
- London: n=2 win=1 loss=1 neutral=0 WR=50.0% MFE=5.42 MAE=5.23 ExpR=0.31
- Asia: n=1 win=0 loss=0 neutral=1 WR=0.0% MFE=9.62 MAE=1.96 ExpR=0.00
- NY/late: n=1 win=0 loss=1 neutral=0 WR=0.0% MFE=0.74 MAE=3.95 ExpR=-0.45

## By setup type
- rejection/mean-reversion: n=36 win=20 loss=15 neutral=1 WR=55.6% MFE=8.43 MAE=3.31 ExpR=0.52
- unknown: n=1 win=1 loss=0 neutral=0 WR=100.0% MFE=10.85 MAE=0.00 ExpR=1.81

## By score band
- <50: n=36 win=20 loss=15 neutral=1 WR=55.6% MFE=8.43 MAE=3.31 ExpR=0.52
- unknown: n=1 win=1 loss=0 neutral=0 WR=100.0% MFE=10.85 MAE=0.00 ExpR=1.81

## By regime
- range_mean_reversion: n=36 win=20 loss=15 neutral=1 WR=55.6% MFE=8.43 MAE=3.31 ExpR=0.52
- unknown: n=1 win=1 loss=0 neutral=0 WR=100.0% MFE=10.85 MAE=0.00 ExpR=1.81

## By result
- TP1: n=18 win=18 loss=0 neutral=0 WR=100.0% MFE=12.29 MAE=1.34 ExpR=1.40
- SL: n=13 win=0 loss=13 neutral=0 WR=0.0% MFE=2.49 MAE=6.31 ExpR=-0.73
- CUT: n=2 win=0 loss=2 neutral=0 WR=0.0% MFE=3.98 MAE=2.97 ExpR=-0.34
- TP2: n=2 win=2 loss=0 neutral=0 WR=100.0% MFE=16.15 MAE=2.50 ExpR=1.84
- BE: n=1 win=0 loss=0 neutral=1 WR=0.0% MFE=9.62 MAE=1.96 ExpR=0.00
- TP3: n=1 win=1 loss=0 neutral=0 WR=100.0% MFE=10.85 MAE=0.00 ExpR=1.81

## Duplicate-zone behavior
- near-duplicate same-direction zones within 45m: 26/37
  • Order #4 ใกล้ #3 BUY Δ6m result=TP1
  • Order #7 ใกล้ #5 BUY Δ6m result=TP1
  • Order #9 ใกล้ #8 BUY Δ4m result=TP1
  • Order #10 ใกล้ #6 BUY Δ16m result=TP1
  • Order #11 ใกล้ #10 BUY Δ4m result=TP1

## Stale-data impact
- orders with linked signal timestamp: 36/37
- avg order-vs-signal age: 0.1m
- >10m stale-linked orders: 0 | n=0 win=0 loss=0 neutral=0 WR=0.0% MFE=0.00 MAE=0.00 ExpR=0.00

## Top 3 MGT recommendations
1. data gap: SELL sample มี 1 ไม้ → ยังห้ามสรุปว่า SELL logic ดี/แย่; ต้องเก็บผลเพิ่มก่อน calibrate ฝั่ง SELL
2. data quality: Phase 1B fields addedแล้ว แต่ historical outcomes ยังไม่มี order_score/setup_score → รอ order ใหม่ปิดก่อน calibrate score band
3. setup taxonomy: Phase 1B fields addedแล้ว แต่ historical sample ยังไม่แยก setup_type → รอ sample ใหม่เพื่อแยก rejection/breakout/continuation/pullback

Note: evidence report only; no trading logic was modified.
