# SteevStyleGridEA

MT5 Expert Advisor สำหรับวาง `BUY STOP` และ `SELL STOP` เป็น Grid รอบราคาปัจจุบัน โดยค่าเริ่มต้นใช้โหมด OCO และไม่มี Martingale

> สถานะ: เวอร์ชันแรกสำหรับ MT5 Strategy Tester และบัญชี Demo ก่อนใช้งานจริง

## Files

```text
SteevStyleGridEA/
├── SteevStyleGridEA.mq5
├── README.md
├── presets/
│   └── XAUUSD-Demo.set
├── docs/
│   └── backtest-plan.md
├── build/
│   ├── SteevStyleGridEA.ex5
│   └── compile-report.txt
└── tools/
    └── validate_ea.py
```

## Build status

Compile จริงด้วย MetaEditor 5 บนเครื่องนี้แล้ว:

```text
Result: 0 errors, 0 warnings
Artifact: build/SteevStyleGridEA.ex5
```

## ความสามารถ

- วาง BUY STOP และ SELL STOP หลายระดับ
- กำหนด initial offset, grid spacing และจำนวนชั้น
- `GRID_OCO`: เมื่อ BUY ถูกเปิด ลบ SELL STOP; เมื่อ SELL ถูกเปิด ลบ BUY STOP พร้อม reconcile/retry ทุก tick และหลัง restart
- `GRID_HEDGE`: คง Pending Orders ทั้งสองฝั่ง
- Fixed lot เท่านั้น ไม่มี Martingale
- ตรวจ potential exposure ทั้ง Grid ก่อนเริ่ม เพื่อไม่ให้จำนวน position/open lots/pending lots เกิน hard cap แม้หลายคำสั่ง trigger เร็ว
- SL/TP ต่อ order
- Break-even และ lock กำไร
- Partial close สำหรับบัญชี Hedging
- Trailing stop
- Basket TP/SL เป็นเงินในสกุลบัญชี
- Daily loss lock และ equity drawdown lock
- เก็บ daily baseline/risk lock ด้วย MT5 Global Variables; เมื่อ lock อยู่จะ retry ลบ Pending และปิด Position ทุก tick/timer จน exposure เป็นศูนย์ และไม่ปลด lock ตอน broker-day rollover หากยังมี exposure ค้าง
- Max spread และ session filter
- Pending expiration, cooldown และ recenter Grid
- แยกคำสั่งด้วย Magic Number

## Logic หลัก

ตัวอย่างค่าเริ่มต้นบน XAUUSD:

```text
ราคา Ask + 300 points = BUY STOP ชั้นแรก
ราคา Bid - 300 points = SELL STOP ชั้นแรก
ระยะห่างชั้นถัดไป = 300 points
จำนวน = 5 BUY + 5 SELL
Lot = 0.01 ต่อ order
```

เมื่อใช้ OCO:

```text
BUY ถูกเปิด  -> ลบ SELL STOP ที่เหลือ
SELL ถูกเปิด -> ลบ BUY STOP ที่เหลือ
EA restart   -> ตรวจ position ที่มีอยู่และลบ Pending ฝั่งตรงข้ามซ้ำจนสำเร็จ
```

Pending ฝั่งเดียวกันยังคงอยู่ระหว่างรอบเทรด แต่ entry/exit transaction จะติดตามรอบแม้เปิดและปิดระหว่าง polling; เมื่อ position ทั้งหมดปิดจะล้าง Pending ที่เหลือและเริ่ม cooldown

เพื่อความปลอดภัย หาก restart แล้วไม่พบ position แต่พบ Pending เดิมของ Magic Number นี้ EA จะถือว่าสถานะรอบเดิมไม่แน่นอน ลบ Pending ทั้งหมด และรอ cooldown ก่อนสร้างรอบใหม่

## ติดตั้งใน MetaTrader 5

1. เปิด MetaTrader 5
2. เปิด MetaEditor ด้วย `F4`
3. ใน Navigator เลือก `MQL5/Experts`
4. สร้างโฟลเดอร์ `SteevStyleGridEA`
5. Copy `SteevStyleGridEA.mq5` เข้าโฟลเดอร์ดังกล่าว
6. เปิดไฟล์ใน MetaEditor และกด `F7` เพื่อ Compile
7. ต้องได้ `0 errors`; ตรวจ warning ก่อนใช้
8. กลับ MT5 และ Refresh Expert Advisors

บน macOS สามารถเปิด data folder จาก MT5:

```text
File → Open Data Folder → MQL5 → Experts
```

## โหลด preset

ใน Strategy Tester หรือหน้า EA Properties:

```text
Inputs → Load → XAUUSD-Demo.set
```

ไฟล์ preset อยู่ที่:

```text
presets/XAUUSD-Demo.set
```

## ค่าที่ต้องตรวจตาม Broker

Broker แต่ละรายตีความ point/digits ของ XAUUSD ต่างกัน ให้ตรวจ:

- `SYMBOL_POINT`
- จำนวน digits
- Stops level
- Volume min/step
- Spread ปกติ

ตัวอย่าง หาก XAUUSD มี `_Point = 0.01`:

```text
300 points = 3.00 ราคา
700 points = 7.00 ราคา
```

หาก `_Point = 0.001` ตัวเลขเดียวกันจะเป็นระยะราคาที่เล็กกว่า 10 เท่า จึงต้องปรับ preset

## Input สำคัญ

### Grid

- `InpGridMode`: OCO หรือ Hedge
- `InpFixedLot`: lot ต่อ pending order
- `InpLevelsPerSide`: จำนวนชั้นแต่ละฝั่ง
- `InpInitialOffsetPoints`: ระยะชั้นแรกจาก Bid/Ask
- `InpGridSpacingPoints`: ระยะระหว่างชั้น
- `InpPendingExpiryHours`: อายุ pending
- `InpRecenterDistancePoints`: ระยะที่ราคาเคลื่อนจาก anchor ก่อนสร้าง Grid ใหม่
- `InpCooldownMinutes`: เวลารอก่อนสร้างรอบใหม่

### Protection

- `InpStopLossPoints`, `InpTakeProfitPoints`
- `InpBreakEvenTriggerPoints`, `InpBreakEvenLockPoints`
- `InpEnablePartialClose`, `InpPartialTriggerPoints`
- `InpTrailingStartPoints`, `InpTrailingDistancePoints`

### Safety

- `InpMaxOpenPositions`
- `InpMaxOpenLots`
- `InpMaxPendingLots`
- `InpBasketTakeProfitMoney`
- `InpBasketStopLossMoney`
- `InpMaxDailyLossPercent`
- `InpMaxEquityDrawdownPct`
- `InpMaxSpreadPoints`

## ข้อจำกัดเวอร์ชันแรก

- Partial close ทำเฉพาะบัญชี `ACCOUNT_MARGIN_MODE_RETAIL_HEDGING`; บัญชี Netting จะข้าม partial แต่ยังทำ BE/trailing
- ค่าเริ่มต้น 5+5 Pending ต้องใช้ `InpMaxOpenPositions=10` บนบัญชี Hedging; บัญชี Netting ใช้ hard cap ด้วย `InpMaxOpenLots`
- Daily loss/equity baseline และ risk lock เก็บใน MT5 Global Variables ตลอดวัน จึงไม่ถูก reset ด้วยการ restart EA
- ยังไม่มี Economic Calendar news filter
- ยังไม่มี SMC/BOS/CHoCH gate; EA นี้เป็น Grid engine แยกจาก `trad`
- Fast market อาจเกิด slippage หรือ trigger ได้หลายคำสั่งก่อน OCO ลบฝั่งตรงข้าม แต่ potential exposure รวมต้องผ่าน hard cap ก่อนวาง Grid
- Basket WR ที่สูงจาก partial close ต้องประเมินร่วมกับ ExpR และ drawdown ไม่ใช้ WR อย่างเดียว

## Validation workflow

1. Compile ใน MetaEditor ให้ได้ 0 errors
2. Strategy Tester: Every tick based on real ticks
3. ทดสอบอย่างน้อย 12 เดือน และหลาย market regimes
4. ทดสอบ spread สูงและ slippage
5. Forward test บัญชี Demo
6. ตรวจ max drawdown, profit factor, expectancy, max loss streak และ margin level
7. ห้ามนำไปเชื่อม production `trad` ก่อนมี shadow/backtest report

รายละเอียดอยู่ใน `docs/backtest-plan.md`
