# SteevStyleGridEA

MT5 Expert Advisor สำหรับวาง `BUY STOP` และ `SELL STOP` เป็น Grid รอบราคาปัจจุบัน โดยค่าเริ่มต้นใช้โหมด Hedge ตามค่าที่ใช้งานจริง และไม่มี Martingale

> สถานะ: เวอร์ชันแรกสำหรับ MT5 Strategy Tester และบัญชี Demo ก่อนใช้งานจริง

## Files

```text
SteevStyleGridEA/
├── SteevStyleGridEA.mq5
├── README.md
├── presets/
│   ├── XAUUSD-Demo.set
│   └── XAUUSD-Reversal-Shadow.set
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
- `GRID_REVERSAL`: Video-style; ถือ position ได้สูงสุด 1 ไม้ และรักษา pending ฝั่งตรงข้ามไว้ 1 ไม้ เมื่อเกิด duplicate exposure จะ flatten ก่อนเริ่มรอบใหม่
- Fixed lot เท่านั้น ไม่มี Martingale
- ตั้งจำนวน levels ได้อิสระโดยไม่มี position/open-lot/pending-lot cap ใน EA
- ไม่มี TP/SL ต่อ order; ใช้ Basket Floating P/L เป็นเงื่อนไขปิดทั้งหมด
- Basket TP/SL เป็นเงินในสกุลบัญชี
- เมื่อ Basket TP ถึง `InpBasketTakeProfitMoney` (ค่าใช้งานจริง 5.0 เหรียญ) จะปิดไม้ทั้งหมดของ Symbol+Magic นี้; ถ้า `InpRestartImmediatelyAfterBasketTP=true` และปิด/ลบ pending สำเร็จครบ จะสร้าง Grid รอบใหม่ทันทีโดยไม่รอ cooldown
- เมื่อ Basket SL ถึง `InpBasketStopLossMoney` จะปิด position และ pending ของ Symbol+Magic ให้หมด; ถ้า `InpRestartImmediatelyAfterBasketSL=true` จะสร้าง Grid รอบใหม่ทันทีโดยไม่ตั้ง risk lock หากปิดยังไม่ครบจะ retry ก่อนเสมอ
- ไม่มี Daily Loss และ Equity Drawdown control ตาม configuration ที่ร้องขอ
- persistent risk lock ใช้เฉพาะเมื่อปิด `InpRestartImmediatelyAfterBasketSL`; เมื่อ lock อยู่จะ retry ลบ Pending และปิด Position ทุก tick/timer
- Max spread และ session filter
- Pending expiration, cooldown และ recenter Grid
- แยกคำสั่งด้วย Magic Number

## Logic หลัก

ตัวอย่างค่าเริ่มต้นบน XAUUSD:

```text
ราคา Ask + 200 points = BUY STOP ชั้นแรก
ราคา Bid - 200 points = SELL STOP ชั้นแรก
ระยะห่างชั้นถัดไป = 200 points
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

- `InpGridMode`: OCO, Hedge หรือ Reversal (2)
- `InpFixedLot`: lot ต่อ pending order
- `InpLevelsPerSide`: จำนวนชั้นแต่ละฝั่ง
- `InpInitialOffsetPoints`: ระยะชั้นแรกจาก Bid/Ask
- `InpGridSpacingPoints`: ระยะระหว่างชั้น
- `InpPendingExpiryHours`: อายุ pending
- `InpRecenterDistancePoints`: ระยะที่ราคาเคลื่อนจาก anchor ก่อนสร้าง Grid ใหม่
- `InpCooldownMinutes`: เวลารอก่อนสร้างรอบใหม่

### Exit calculation

- ไม่มี input TP/SL ต่อ order
- `InpBasketTakeProfitMoney`: กำไรรวมที่ใช้ปิดทุก position
- `InpBasketStopLossMoney`: ขาดทุนรวมที่ใช้ปิดทุก position
- Basket exit รวม floating profit + swap ของ position ที่ตรง Symbol+Magic

### Safety

- `InpBasketTakeProfitMoney`
- `InpRestartImmediatelyAfterBasketTP`
- `InpBasketStopLossMoney`
- `InpRestartImmediatelyAfterBasketSL`

- `InpMaxSpreadPoints`

## ข้อจำกัดเวอร์ชันแรก

- EA ไม่จำกัด position/open lots/pending lots; จำนวนจริงยังจำกัดด้วย margin และข้อจำกัดของ broker
- ยังไม่มี Economic Calendar news filter
- ยังไม่มี SMC/BOS/CHoCH gate; EA นี้เป็น Grid engine แยกจาก `trad`
- Fast market อาจเกิด slippage หรือ trigger หลายคำสั่ง; ผู้ใช้ต้องกำหนด levels/lot ให้เหมาะกับ margin เอง
- ผลลัพธ์จาก Basket TP/SL ต้องประเมินร่วมกับ Expectancy และ drawdown ไม่ใช้ win rate อย่างเดียว

## Validation workflow

1. Compile ใน MetaEditor ให้ได้ 0 errors
2. Strategy Tester: Every tick based on real ticks
3. ทดสอบอย่างน้อย 12 เดือน และหลาย market regimes
4. ทดสอบ spread สูงและ slippage
5. Forward test บัญชี Demo
6. ตรวจ max drawdown, profit factor, expectancy, max loss streak และ margin level
7. ห้ามนำไปเชื่อม production `trad` ก่อนมี shadow/backtest report

รายละเอียดอยู่ใน `docs/backtest-plan.md`
