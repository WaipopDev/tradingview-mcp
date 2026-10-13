# Local MT5 readiness — 2026-10-11

ตรวจแบบ read-only บน Windows เวลา 2026-10-11T14:07:14 UTC; ไม่ส่ง order ไม่แก้ Algo Trading และไม่พิมพ์ข้อมูลระบุตัวบัญชี

## ผลตรวจจริง

- Python ของ repository `.venv`: 3.11.15; มี MetaTrader5 และ pytest
- `MetaTrader5.initialize()`: true; last_error `[1, "Success"]`
- Terminal: MetaTrader 5 build 6230, connected=true
- Terminal trade_allowed=false; tradeapi_disabled=false
- Account trade_mode=2 (บัญชีเงินจริง); trade_allowed=true; trade_expert=true
- Symbol ทอง spot ที่เห็นใน terminal คือ `GOLD`, visible=true; ไม่พบชื่อ `XAUUSD` ในรายชื่อ symbol ทองที่อ่านได้
- `GOLD24-7` เป็นอีก symbol ห้ามแทน `GOLD` โดยอัตโนมัติ
- GOLD tick time=1791590279, bid=4194.6, ask=4195.59; age ตอนตรวจประมาณ 137355 วินาที เป็นราคาเก่า ไม่ใช่ราคาปัจจุบัน
- อ่าน GOLD M15 แบบข้ามแท่งกำลังก่อตัว (`copy_rates_from_pos(..., 1, 260)`) ได้ 260 แท่ง; แท่งสุดท้าย time=1791588600, close=4195.38
- วันที่ตรวจเป็นวันอาทิตย์ แต่ข้อมูลนี้พิสูจน์ได้เพียง tick เก่า ไม่ยืนยันตารางเปิดตลาดของ broker

## สรุปความพร้อม

อ่านข้อมูล local MT5 และข้อมูลย้อนหลังได้แล้ว แต่ยังไม่พร้อมประกาศว่า auto trading ใช้งานจริงได้: Algo Trading ของ terminal ปิด, tick GOLD เก่า และยังไม่ได้พิสูจน์ execution/risk/recovery end-to-end ของระบบใหม่ บัญชีที่เชื่อมอยู่เป็นเงินจริง จึงไม่ควรเปิดระบบทดลองส่ง order

## สถานะระบบเดิม

- provider `src/tradingview_mcp/core/services/metatrader5_service.py` อ่าน local MT5 และคำนวณ indicators; ไม่ใช่ระบบส่ง order
- `mt5/TradSignalOCOEA/README.md` ระบุ V0.02 มี compile evidence แต่ V0.03–V0.06 ยังไม่มี compile/validation evidence ตามเอกสาร ไม่ได้ compile ใหม่ในการตรวจนี้
- `mt5/SteevStyleGridEA` เป็นกลยุทธ์ grid และไม่ใช่แกนกราฟเปล่าที่จะเริ่มใหม่
- งานที่แก้ค้างเดิมใน README.md, pyproject.toml, uv.lock, screener_service.py และไฟล์ local provider/tests ยังเก็บไว้ ไม่ลบทิ้ง

## การทดสอบ baseline ก่อนระบบใหม่

คำสั่ง `.venv/Scripts/python.exe -m pytest tests -q`

ผลจริง: 310 passed, 8 deselected in 6.75s

การทดสอบเฉพาะ local MT5 provider, file bridge และ quote storage: 10 passed in 0.54s

ผล unit tests ไม่ได้พิสูจน์ว่ากลยุทธ์มีกำไรหรือส่งคำสั่งซื้อขายจริงได้

## ทิศทางการสร้างใหม่

Branch: `feat/local-mt5-price-action`

แยกโปรเจกต์ minimal `trad_auto/` ไม่เรียก pipeline TradingView/AI/Telegram/grid เดิม ใช้ OHLC จาก local MT5 และยืนยันแท่งปิดก่อนประเมิน price action ระยะแรกเป็น analysis/replay เท่านั้น การส่ง order และ forward test บัญชี demo เป็นขั้นตอนแยกที่ยังไม่เปิดใช้งาน

## ตรวจรับระบบใหม่

- สร้าง standalone package ใน `trad_auto/` พร้อม README ภาษาไทย, CLI doctor/analyze/replay และ unit tests
- รันรวมจริง `PYTHONPATH=trad_auto/src .venv/Scripts/python.exe -m pytest tests trad_auto/tests -q`: 359 passed, 8 deselected in 7.99s (ระบบใหม่ 49 tests)
- รัน doctor และ analyze กับ `--symbol GOLD`: connected=true, fresh=false, data_ready=false, WAIT, reason=stale candles, exit=2; execution_enabled=false
- รัน replay กับ GOLD M15 260 แท่งและ H1: historical_data_ready=true, evaluated_prefixes=245, BUY=0, SELL=0, exit=0
- Replay เป็นการนับ setup เท่านั้น ไม่ใช่ผลกำไรหรือ win rate; ไม่มี historical spread/fill/exit model
- `git diff --check` ผ่าน โดยมีเพียงคำเตือน line-ending ของ uv.lock ที่แก้ค้างมาก่อน
- ไม่มีการส่งออร์เดอร์ เปิด Algo Trading ติดตั้ง EA หรือ commit/push
