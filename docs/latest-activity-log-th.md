# บันทึกกิจกรรมล่าสุด — Trad Dashboard Automation

วันที่บันทึก: 2026-08-03 23:39:30 +07
Repo: `/Users/waipop/MainWTN/Hermes/trad`
Remote: `https://github.com/WaipopDev/tradingview-mcp.git`
Branch: `main`
สถานะ Git ตอนบันทึก: clean, synced with `origin/main`

## Commit ล่าสุด

```text
d60fb2a feat: add Thai dashboard and SD OI proxy
5cc0e2a feat: add token-efficient trad dashboard automation
b04d929 feat: add OI expected range scoring tool
```

## งานที่ทำล่าสุด

1. เพิ่มระบบ Trad Dashboard automation แบบ token-efficient
   - เก็บ compact trade signal ลง SQLite
   - Dashboard อ่านจาก DB แทนการให้ AI ดึงข้อมูล raw ซ้ำ
   - เพิ่ม MCP tools:
     - `analyze_and_store_signal`
     - `latest_trade_signal`
     - `store_ai_signal_response`

2. เพิ่ม cron collector ทุก 5 นาที
   - Job: `trad-xauusd-collector-5m`
   - Schedule: `every 5m`
   - Script: `trad_collect_and_ai_alert_xauusd.sh`
   - Mode: `no_agent=true`
   - ทำงานเงียบเมื่อไม่มีสัญญาณเข้าเงื่อนไข

3. เพิ่ม AI gate + AI response cache
   - ถ้า `decision != TRADE` ไม่ถาม AI
   - ถ้า score ต่ำกว่า threshold ไม่ถาม AI
   - ถ้าไม่มี entry/SL/TP ไม่ถาม AI
   - ถ้า signal fingerprint เดิมมีคำตอบ AI แล้ว ใช้ cache ไม่ถามซ้ำ
   - ถ้าเข้าเงื่อนไขจริง ค่อยให้ cron เรียก AI แล้วส่ง Telegram

4. เพิ่ม Telegram entry alert automation
   - เมื่อ `ai_gate.should_ask_ai=true` และไม่มี cache:
     - เรียก Hermes AI จาก compact JSON
     - บันทึกคำตอบ AI ลง DB
     - ส่งข้อความเข้า Telegram target
   - ป้องกันการส่งซ้ำด้วย signal fingerprint

5. เพิ่ม SD Range
   - คำนวณจาก current price + ATR
   - เก็บค่า:
     - anchor price
     - expected move points
     - SD1 low/high
     - SD2 low/high
     - range state

6. เพิ่ม OI / intraday proxy
   - สำหรับ OANDA:XAUUSD ไม่มี centralized Open Interest จริง
   - จึงเก็บเป็น proxy ชัดเจนว่า `real_open_interest_available=false`
   - ใช้ ATR + support/resistance เป็น intraday magnet/flow proxy
   - ส่ง `flow_context` เข้า strategy regime score

7. แปล Trad Dashboard เป็นภาษาไทย
   - Dashboard title, labels, buttons, reason codes และ AI gate labels เป็นไทย
   - ยังเก็บคำสำคัญ BUY/SELL เป็นอังกฤษตาม preference การเทรด

8. ปรับ prompt ที่ถาม AI เป็นภาษาอังกฤษ
   - Prompt instruction เป็นอังกฤษ
   - สั่งให้ AI ตอบ Telegram เป็นไทยแบบสั้น กระชับ
   - จำกัดให้ใช้เฉพาะ compact signal JSON และห้ามดึงข้อมูลเพิ่ม

## Verification ล่าสุดก่อน commit/push

Python tests:

```text
uv run pytest tests/unit -q
258 passed in 4.26s
```

Dashboard:

```text
npm run lint && npm run build
ผ่าน
```

## ไฟล์สำคัญที่เกี่ยวข้อง

```text
src/tradingview_mcp/core/jobs/analyze_and_store_signal.py
src/tradingview_mcp/core/jobs/ai_signal_alert.py
src/tradingview_mcp/core/services/sd_oi_proxy_service.py
src/tradingview_mcp/core/storage/repositories.py
scripts/collect_trad_signal.py
scripts/ai_alert_if_needed.py
dashboard/src/app/page.tsx
dashboard/src/components/SignalCard.tsx
dashboard/src/components/SignalDetails.tsx
```

## หมายเหตุ

- งานล่าสุดถูก commit/push แล้วที่ `d60fb2a`
- Cron/local Hermes scripts อยู่ใน `~/.hermes/scripts/` และเป็น local config ไม่ได้อยู่ใน git repo
- ถ้าจะทำต่อ แนะนำ phase ถัดไป: เพิ่ม historical signal table view, performance review, หรือ real proxy data จาก GLD options / COMEX metals snapshot
