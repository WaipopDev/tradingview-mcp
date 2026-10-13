# trad_auto — อ่านกราฟเปล่าจาก MT5 ในเครื่อง

โครงการใหม่แยกจากระบบเดิม ใช้ Python + official `MetaTrader5` อ่านราคา ไม่มี TradingView, indicator, AI, Telegram, grid หรือ martingale

**ส่งออร์เดอร์ได้เฉพาะการเรียก `execute-demo` ทีละครั้งบนบัญชีเดโม**; `doctor`, `analyze`, `replay` ยังคงไม่ส่งออร์เดอร์ บัญชีเงินจริงถูกบล็อกในโค้ด ไม่รันอัตโนมัติและไม่ติดตั้ง EA. BUY/SELL จาก `analyze` เป็นแผนเท่านั้น; `execute-demo` ต้องได้สัญญาณสดและตรวจบัญชีเดโม, quote, spread, stop, position, broker order_check ก่อนส่ง ผลลัพธ์ไม่รับประกันกำไร

การเรียกเองเมื่อ MT5 บัญชีเดโมเปิดอยู่ (ใช้ชื่อ symbol ที่ broker มีจริง):

```bash
export PYTHONPATH=trad_auto/src
.venv/Scripts/python.exe -m trad_auto execute-demo --symbol GOLD --timeframe M5
```

คำสั่งนี้อาจส่งคำสั่ง BUY/SELL จริงในบัญชีเดโมถ้ามี setup; อย่ารันเพื่อเพียงทดสอบการเชื่อมต่อ ให้ใช้ `doctor` แทน. ใช้ lot ขั้นต่ำของ broker พร้อม SL/TP และ RR คำนวณใหม่จากราคา quote; ยังไม่มีเพดานขาดทุนต่อวันหรือการจำกัดความเสี่ยงเป็นเปอร์เซ็นต์ จึงต้องตรวจ broker minimum lot ก่อนใช้งาน. หากมี position อยู่แล้วใน symbol เดียวกันจะไม่เปิดซ้ำ

**Live (เงินจริง):** `execute-live` เป็นคำสั่งเรียกครั้งเดียวแยกจาก demo ต้องระบุ `--daily-loss-limit-usd 30` และ `--broker-utc-offset-hours 3` อย่างชัดเจนเมื่อ broker ใช้เวลา UTC+3; ไม่อนุมาน offset จาก tick (tick เก่าทำให้เข้าใจผิดได้). ใช้ 0.01 lot เท่านั้น พร้อม SL/TP. แปลง timestamp แท่งและ tick เป็น UTC ก่อนตรวจ freshness; ตรวจแท่งปัจจุบัน index 0 ว่าสอดคล้องกับนาฬิกา UTC ภายใน timeframe และตรวจซ้ำก่อนส่ง. ประเมิน P/L จาก deals ทั้งบัญชีตั้งแต่ 00:00 UTC โดยส่งช่วงเวลา UTC ที่บวก offset ให้ broker, ความเสี่ยงตำแหน่งเปิดทุก symbol และคำสั่งใหม่ถึง SL; ตรวจ login+server เดิมก่อนส่ง. ค่า offset ไม่ทำให้ tick เก่าหรืออนาคตผ่านได้. ไม่มี scheduler. **อย่ารันคำสั่งนี้เพื่อทดสอบ** เพราะอาจส่งเงินจริงหากข้อมูลสดและมี setup; ใช้ `doctor` ตรวจแบบ read-only แทน. Broker อาจเปลี่ยน offset ตามฤดูกาล จึงต้องตรวจใหม่และระบุเองเสมอ.

```bash
.venv/Scripts/python.exe -m trad_auto doctor --symbol GOLD --timeframe M5 --broker-utc-offset-hours 3
# execute-live ต้องใส่ --broker-utc-offset-hours 3 และ --daily-loss-limit-usd 30; ห้ามใช้เพื่อทดสอบ
```

SQLite เริ่มต้น `~/.trad_auto/orders.sqlite3` (เปลี่ยนด้วย `--db-path`), บันทึก signal แบบ unique เป็น `pending` ก่อนส่ง และเปลี่ยนเป็น `filled` หลังยืนยัน deal จาก MT5 พร้อม ticket/ราคาที่ fill. หากผลส่งไม่ชัดเจนคง `pending` และบล็อกสัญญาณใหม่จนตรวจ terminal กับ DB ด้วยตนเอง; ห้ามลบ DB หรือส่งซ้ำอัตโนมัติ. ไม่มีการปิด/แก้ไขออร์เดอร์ และไม่ได้ติดตามการปิดหรือ P/L

บันทึกออร์เดอร์ที่กดเอง (ไม่ส่งคำสั่งซื้อขาย): `.venv/Scripts/python.exe -m trad_auto sync-manual` จะอ่านประวัติ MT5 เข้า `manual_orders`/`manual_deals` ใน DB เดียวกัน; ครั้งแรกใช้เวลา UTC ปัจจุบันเป็นจุดเริ่มต้น เว้นแต่ระบุ `--since-utc 2026-10-12T06:07:36Z`. จุดเริ่มต้นเก็บแยกตามบัญชีและการซิงก์ซ้ำไม่สร้างรายการซ้ำ. รับเฉพาะ reason=client/mobile/web และ magic=0; การปิดด้วย SL/TP หรือ EA จะไม่อยู่ในกลุ่มนี้. MT5 เครื่องนี้มีเวลา broker นำหน้าเวลาระบบ: ซิงก์อ่านส่วนต่างเวลา tick ของ GOLD และเก็บ offset ใน DB; หาก offset เปลี่ยนมากกว่า 120 วินาทีจะหยุดเพื่อตรวจสอบแทนการเดา


## เริ่มจาก repo นี้ (Windows Git Bash)

เปิด MT5 และเชื่อมต่อด้วยตนเองก่อน แอปไม่อ่าน/พิมพ์รหัสผ่าน เลขบัญชี ยอดเงิน หรือชื่อผู้ใช้ ไม่เปลี่ยน Market Watch หรือการตั้งค่า terminal

```bash
cd D:/Hermes/tradingview-mcp
export PYTHONPATH=trad_auto/src
.venv/Scripts/python.exe -m trad_auto doctor --symbol GOLD
.venv/Scripts/python.exe -m trad_auto analyze --symbol GOLD --timeframe M5 --rr 1
.venv/Scripts/python.exe -m trad_auto replay --symbol GOLD --timeframe M5 --rr 1 --bars 260
.venv/Scripts/python.exe -m pytest trad_auto/tests -q
```

`GOLD` เป็นชื่อที่ผู้ดูแลตรวจพบใน broker ของเครื่องนี้ ต้องระบุอย่างชัดเจนตามตัวอย่าง ไม่ใช้ `GOLD24-7` แทน เพราะเป็นคนละ instrument ค่าเริ่มต้นในโปรแกรมยังเป็น **XAUUSD แบบตรงตัว** ตามข้อกำหนด ถ้าไม่มีชื่อนี้จะหยุด ไม่ค้นหา alias ให้เงียบ ๆ ต้องเลือก symbol ที่ visible อยู่แล้วใน Market Watch ด้วยตนเอง

### ติดตั้งแยกอิสระ (ไม่พึ่ง repo เดิม)

ต้องใช้ Windows และ Python 3.11–3.13 ที่รองรับ wheel ของ MetaTrader5 ตัวอย่าง Git Bash:

```bash
cd D:/Hermes/tradingview-mcp/trad_auto
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -e '.[mt5,test]'
.venv/Scripts/python.exe -m trad_auto doctor --symbol GOLD
.venv/Scripts/trad-auto.exe analyze --symbol GOLD
.venv/Scripts/python.exe -m pytest tests -q
```

Pure core ไม่มี dependency ภายนอก ทดสอบด้วย injected provider ได้โดยไม่เปิด MT5 และไม่ลง MetaTrader5; ติดตั้ง `.[test]` แทน `.[mt5,test]` สำหรับงานนี้

## คำสั่งและผล JSON

- `doctor`: แยก `connected` (เชื่อมต่อ terminal), `fresh` (อายุ tick และแท่ง TF หลัก), `data_ready` (OHLC/quote/H1 ผ่านครบ) ออกจาก `terminal_trade_allowed` และ `execution_enabled` อย่างชัดเจน Connected ไม่ได้แปลว่าราคาใหม่หรือพร้อมเทรด
- `analyze`: BUY/SELL/WAIT พร้อมเหตุผล; แผนที่ผ่านมี entry/stop/target/rr และเวลา BOS เป็น Unix UTC
- `replay`: นับ setup ในข้อมูลย้อนหลังจริงที่อ่านจาก MT5 ไม่ส่งออร์เดอร์ ไม่คำนวณกำไร win rate หรือ drawdown; แยก `historical_data_ready` จาก `data_ready` ปัจจุบัน
- Exit code `0`: วิเคราะห์/ตรวจสอบได้ (WAIT เพราะยังไม่เกิด pattern ก็เป็น 0), `2`: config/provider/คุณภาพข้อมูลไม่ผ่าน และคืน WAIT การใช้ `--help` แสดงข้อความช่วยเหลือตามปกติ ส่วนผลการทำงาน/ข้อผิดพลาดเป็น JSON บรรทัดเดียว

ค่าเริ่มต้นสำหรับ scalping: `--symbol XAUUSD --timeframe M5 --bars 260 --pivot 2 --rr 1 --max-spread 1 --max-tick-age 120 --retest-bars 4`

เริ่มจาก M5 + ตัวกรอง H1 และ RR 1:1 ตามระยะราคา: ระยะ entry ถึง TP เท่ากับระยะ entry ถึง SL ทั้ง BUY และ SELL ยังไม่ใช่ RR สุทธิหลัง spread/commission/slippage และไม่รับประกันว่าจะปิดได้รวดเร็วหรือมีกำไร ไม่มี time-based exit ในรุ่นนี้ เปลี่ยน TF/RR ได้อย่างชัดเจนผ่าน `--timeframe` และ `--rr`

รองรับ M5/M15/M30/H1; ใช้ H1 เป็น alignment filter อัตโนมัติสำหรับ TF ต่ำกว่า H1 ถ้า H1 หาย/ผิดรูป/เก่า ให้ WAIT ห้าม fallback เงียบ ๆ ปิดด้วย `--no-htf` อย่างชัดเจน เช่น:

```bash
.venv/Scripts/python.exe -m trad_auto analyze --symbol GOLD --no-htf --max-spread 0.5
.venv/Scripts/python.exe -m trad_auto replay --symbol GOLD --no-htf --bars 1000
```

`max-spread` เป็นหน่วยราคา (ask−bid) ไม่ใช่ point/pip ต้องกำหนดตาม instrument; ค่าเริ่มต้นไม่ใช่คำแนะนำที่เหมาะกับทุก broker

## กติกา OHLC ที่ทำซ้ำได้

1. อ่าน `copy_rates_from_pos(..., 1, ...)` เพื่อข้าม index 0 และกรองเฉพาะแท่งที่เวลาเปิด+ระยะ TF ไม่เกินเวลาปัจจุบัน ไม่มี forming bar
2. Pivot high/low ต้องสูง/ต่ำกว่าเพื่อนบ้านทั้งซ้ายและขวา `pivot` แท่งอย่างเคร่งครัด (เสมอกันไม่นับ) ยืนยันได้ที่ `index+pivot` เท่านั้น
3. High สองจุดล่าสุดสูงขึ้น = HH ต่ำลง = LH; Low สูงขึ้น = HL ต่ำลง = LL. HH+HL = bullish, LH+LL = bearish; เท่ากัน/ไม่พอ/ผสมกัน = range
4. BOS ต้องมี trend ตามข้อ 3 **จากข้อมูลก่อนแท่ง BOS เท่านั้น** และ close ข้าม pivot high ล่าสุดขึ้น (BUY) หรือ pivot low ล่าสุดลง (SELL); close ก่อนหน้าต้องยังอยู่ฝั่งเดิม
5. หลัง BOS ต้อง retest ภายใน 1–4 แท่ง (ค่าเริ่มต้น) แท่งล่าสุดต้องคร่อมระดับ BOS และปิดกลับด้าน trend, body เป็น bullish สำหรับ BUY / bearish สำหรับ SELL, wick ด้าน rejection ยาวอย่างน้อยเท่า body ทุก close ระหว่าง BOS กับ retest ต้องไม่ปิดทะลุกลับฝั่งผิด
6. ถ้าใช้ H1, trend H1 ณ เวลาที่วิเคราะห์ต้องตรงทิศทาง ไม่มีสัญญาณถ้า H1 เป็น range
7. Entry สมมติ = close ของแท่ง rejection ที่ปิดแล้ว **ไม่ใช่ราคาที่รับประกันว่าจะซื้อขายได้** Stop = low ต่ำสุดตั้งแต่ BOS ถึง rejection (BUY), high สูงสุด (SELL). Target = entry ± RR×ระยะ stop; RR เริ่ม 1 (1:1 ก่อนต้นทุน). ไม่มีการปัดตาม tick size หรือ broker stop distance เพราะไม่ได้สร้างคำสั่งเทรด

## Fail closed / ข้อจำกัด

- OHLC ต้อง finite, >0, low≤open/close≤high; timestamp ต้องเรียงและไม่ซ้ำ ไม่จัดเรียง/ซ่อมข้อมูลเสียให้เงียบ ๆ
- ต้องมีอย่างน้อย `2*pivot+6` แท่ง; แท่งล่าสุดปิดมาไม่เกินหนึ่ง TF, tick อายุไม่เกิน 120 วินาทีและไม่อยู่อนาคต; bid/ask ต้องสมเหตุสมผลและ spread ไม่เกินค่าที่กำหนด ข้อมูลเสีย/เก่า/ตลาดปิด ⇒ WAIT ไม่ลดเกณฑ์ให้ผ่าน
- ไม่มี exchange calendar: ช่องว่างของ session/วันหยุดในข้อมูลย้อนหลังยังคงอยู่และ pivot นับตามแท่งที่มี ไม่อนุมานแท่งที่หาย ไม่ใช่การรับรองว่าประวัติครบทุกแท่ง
- Replay ใช้ prefix ทีละแท่ง และ H1 ที่ปิดแล้ว ณ เวลา prefix เท่านั้น ไม่มีข้อมูลอนาคตไปยืนยัน pivot ก่อนเวลา นับ setup แรกต่อ `(direction, BOS time)` ไม่รวม retest ซ้ำของ BOS เดิม
- Replay ตรวจรูปแบบ OHLC แต่เทียบความสดกับนาฬิกาย้อนหลัง ไม่บังคับราคาเก่าต้องสดวันนี้ จึงใช้งานศึกษาวันหยุดได้ ระบุ `spread_checked: false` และ `profitability_evaluated: false` เสมอ เพราะไม่มี historical bid/ask, fill, slippage, fees, exit sequence หรือ execution model
- ประวัติที่ได้ขึ้นกับ cache/Max bars ของ MT5; `--bars` คือจำนวนที่ร้องขอ ผล JSON รายงานจำนวนที่ได้รับจริง ไม่ดาวน์โหลดข้อมูลปลอมมาเสริม
- `doctor/analyze/replay` ไม่อ่านบัญชี; `execute-demo` อ่านประเภทบัญชีและสถานะสิทธิ์ก่อนส่งและตรวจซ้ำก่อนส่งจริง แต่ไม่พิมพ์เลขบัญชี ไม่เปลี่ยน AutoTrading และไม่เลือก symbol ให้อัตโนมัติ; `initialize()` เชื่อมต่อ terminal ตามการค้นหามาตรฐานของ MetaTrader5 และ `shutdown()` ปิดเฉพาะการเชื่อมต่อ Python หลังจบคำสั่ง

## โครงสร้างและการทดสอบ

`src/trad_auto/core.py` = pure OHLC + validation + replay; `provider.py` = official MT5 read-only adapter; `cli.py` = JSON CLI/clock/provider injection; `tests/` = unit และ CLI subprocess tests

พัฒนาด้วย RED→GREEN เป็นชุดความสามารถและรันจริง ครอบคลุม bullish/bearish/flat, malformed/stale/spread, pivots และ replay ไม่มองอนาคต, H1 fail closed, symbol ตรงตัว, forming bars, provider failure/cleanup, config และ JSON CLI errors เทสต์ใช้ข้อมูลสังเคราะห์ที่ระบุชัด ไม่อ้างว่าเป็นผลตลาดจริง
