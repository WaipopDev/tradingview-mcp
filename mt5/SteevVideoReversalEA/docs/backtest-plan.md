# Backtest Plan — SteevStyleGridEA

## เป้าหมาย

ตรวจว่า Grid มี edge หลังรวม spread, commission, slippage และการเปิดหลาย position โดยให้ Basket Floating P/L เป็นทางออกหลัก และไม่ประเมินจาก win rate เพียงอย่างเดียว

## Environment

- Platform: MetaTrader 5 Strategy Tester
- Symbol: Broker XAUUSD
- Model: Every tick based on real ticks
- Initial deposit: ให้ตรงบัญชีที่จะใช้
- Leverage: ให้ตรงบัญชี Demo/จริง
- Forward mode: 1/3 ของช่วงข้อมูล
- Base timeframe: M5 หรือ M15

## Data ranges

ทดสอบอย่างน้อย:

1. 12 เดือนล่าสุด
2. Trend regime
3. Range regime
4. High-volatility/news regime
5. ช่วง spread กว้างและ rollover

## Baseline

```text
Mode: HEDGE (ทดสอบ OCO แยกเป็น A/B)
Lot: 0.01
Levels: 5 ต่อฝั่ง
Offset: 200 points
Spacing: 200 points
Per-order SL/TP: ปิดใช้งาน (ส่งค่า 0.0)
Basket TP: 5.0 account currency
Basket SL: 20.0 account currency
```

## A/B matrix

### Grid mode

- OCO
- HEDGE

### Levels

- 3
- 5
- 8

### Spacing

- 200 points
- 300 points
- 500 points

### Exit calculation

- Basket TP/SL only
- Restart immediately after Basket TP/SL เมื่อ cleanup จน flat สำเร็จ
- ทดสอบ Basket TP/SL หลายระดับตามสกุลเงินบัญชี

### Session

- All day
- Asia
- London
- London/NY overlap

## Metrics ที่ต้องเก็บ

- Net profit
- Profit factor
- Expected payoff / expectancy
- Max equity drawdown %
- Max balance drawdown %
- Recovery factor
- Total trades
- Basket TP / Basket SL counts
- Max consecutive losses
- Average margin level
- Largest simultaneous exposure
- Pending trigger slippage
- Performance แยก BUY/SELL/session

## Pass criteria สำหรับ Demo forward test

ตัวเลขตั้งต้นสำหรับคัดรอบ ไม่ใช่ production approval:

```text
Profit factor >= 1.20
Expectancy > 0 หลัง commission
Max equity drawdown <= 10%
Max loss streak อยู่ใน risk budget
ไม่มี margin call / stop out
ผล forward ไม่เสียรูปจาก in-sample อย่างรุนแรง
```

## Failure conditions

หยุดทดสอบ/ไม่อนุมัติเมื่อ:

- Edge มาจากช่วงข้อมูลเดียว
- HEDGE เปิดสองฝั่งจน margin usage เกินระดับที่ยอมรับ
- OCO ลบ pending ไม่ทันใน fast market
- Profit มาจากการตั้ง Basket TP ต่ำเกินไป แต่ ExpR หลังหักต้นทุนติดลบ
- Drawdown หรือ margin usage เกินเกณฑ์
- Parameter เปลี่ยนเล็กน้อยแล้วผลพัง (overfit)

## Rollout

1. Static validation
2. MetaEditor compile 0 errors
3. Strategy Tester
4. Out-of-sample/forward test
5. Demo account อย่างน้อย 2–4 สัปดาห์
6. Shadow comparison กับ `trad`
7. จึงพิจารณา production แยกต่างหาก
