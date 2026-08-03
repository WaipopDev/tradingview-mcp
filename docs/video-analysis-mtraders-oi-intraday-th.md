# วิเคราะห์วิดีโอ MTraders: Intraday Open Interest

Video: https://www.youtube.com/watch?v=YLDOWKONnZk
Title: 🔴ราคา OI น่ะมีอยู่จริง วิเคราะห์ Intraday OpenInterest
Channel: MTraders
Duration: 17:59

หมายเหตุ: สรุปจาก transcript อัตโนมัติของ YouTube ซึ่งมีคำเพี้ยนหลายจุด แต่ใจความหลักอ่านได้ชัดเจนพอสำหรับแปลงเป็นแนวคิดใน trad

## แก่นของวิธีวิเคราะห์

ผู้พูดใช้ข้อมูล Options / Open Interest เป็นกรอบ intraday range และ magnet zone โดยไม่ได้ดู OI เป็นสัญญาณทิศทางเดี่ยว ๆ แต่ใช้ร่วมกับ:

1. Basis ระหว่าง futures กับ spot/real-time price
2. OI concentration / strike ที่ตลาดสนใจ
3. Implied volatility / expected move
4. 1 SD / 2 SD range
5. Price action direction ระหว่างวัน
6. Block / half-block สำหรับ SL หรือ invalidation

## ตัวเลขสำคัญที่พูดถึงในวิดีโอ

- Futures series V real-time ประมาณ 4,080
- Basis ที่ใช้ประมาณ 25 เหรียญ ไม่ใช่ 50-58 เหรียญแบบเดิม
- OI สนใจโซน 4,125
- Magnet หลักอยู่แถว 4,100
- Volatility real-time ประมาณ 14.4
- Expected move ประมาณซ้าย 25 / ขวา 25 เหรียญ หรือราว 25-30 เหรียญต่อฝั่ง
- Anchor price ตอน 05:00 ประมาณ 4,099 futures
- 1 SD range: ใช้ anchor price ± expected move
- มุมมองช่วงท้าย: ถ้า volatility ไม่เพิ่ม ตลาดน่าจะวิ่งกินโซน 4,100 และ range แคบ

## Logic ที่ตีความได้

### 1. Basis adjustment

ก่อนใช้ OI / futures zone ต้องแปลงให้ตรงกับราคาที่เทรดจริง

ตัวอย่างจากวิดีโอ:

- Futures real-time ~4,080
- Basis ~25
- ดังนั้นราคาอ้างอิง/zone ต้อง shift ด้วย basis ที่ถูกต้อง

ข้อควรใช้ใน trad:

- ถ้า instrument เป็น XAUUSD spot/CFD แต่ proxy OI มาจาก futures/options ต้องมี `basis_adjustment`
- ห้ามใช้ basis ค้างจากวันก่อน เช่น 50+ ถ้าปัจจุบันเหลือ 25

### 2. OI magnet

เขาดู strike/zone ที่ OI สนใจมาก เช่น 4,100 / 4,125 แล้วตีความเป็น magnet หรือ zone ที่ราคามีโอกาสถูกดึงไปหา โดยเฉพาะวัน expiry หรือ intraday options flow เด่น

ข้อควรใช้ใน trad:

- สร้าง field `oi_magnet_zone`
- ถ้าราคาปัจจุบันอยู่ใกล้ magnet และ volatility ต่ำ ให้ลดความมั่นใจของ breakout
- ถ้าราคา sweep ออกนอก 1 SD แล้วกลับเข้า magnet ให้ favor mean reversion

### 3. Expected move จาก IV/OI

เขาใช้ implied volatility / OI settlement คาดว่าตลาดมี expected move ประมาณ 25-30 เหรียญต่อฝั่ง และตีกรอบ 1 SD ว่าตลาดมีโอกาสอยู่ในกรอบประมาณ 70%

ข้อควรใช้ใน trad:

- เพิ่ม `expected_move = anchor_price * iv_daily_proxy`
- ถ้าไม่มี IV โดยตรง ใช้ options chain หรือ ATR เป็น fallback
- สร้าง range:
  - `sd1_low = anchor - expected_move`
  - `sd1_high = anchor + expected_move`
  - `sd2_low/high` สำหรับ extreme / invalidation

### 4. Anchor time

เขาใช้เวลาประมาณ 05:00 เป็น anchor สำหรับราคาเปิด/ฐานของวัน แล้ววาง SD range จากตรงนั้น ไม่ได้นับจากราคาปิดวันก่อน

ข้อควรใช้ใน trad:

- เพิ่ม parameter `anchor_time`, default สำหรับ XAUUSD อาจใช้ Asian/session open หรือเวลาที่ user กำหนด
- ถ้ามี gap ตอนเปิด ให้ใช้ราคาเปิดจริงเป็น anchor ไม่ใช่ close เดิม

### 5. Probability zone ไม่ใช่สัญญาณเดี่ยว

เขาบอกชัดว่าต้องดูทิศทางกราฟด้วย เช่น ถ้ากราฟวิ่งลงมาถึง zone หนึ่ง probability จะเปลี่ยน ถ้าราคากลับขึ้น probability เดิมอาจใช้ไม่ได้

ข้อควรใช้ใน trad:

- OI/SD score ต้อง combine กับ market structure / momentum
- ห้ามให้ BUY/SELL จาก OI อย่างเดียว
- ถ้า price action ขัดกับ OI probability ให้ `WAIT_CONFIRMATION`

## Mapping เข้ากับ strategy_regime_score

เพิ่มเป็น `flow_context` หรือ future service ใหม่ชื่อ `oi_expected_range_score`

### Inputs ที่ต้องการ

```text
symbol
spot_price
proxy_underlying_price
basis
anchor_price
iv_or_expected_move
oi_magnet_zone
oi_bias_direction: BUY/SELL/WAIT
oi_confidence: Low/Medium/High
expiry_context: true/false
```

### Outputs ที่ควรได้

```text
basis_adjustment
expected_move
sd1_low
sd1_high
sd2_low
sd2_high
magnet_zone
range_state: inside_sd1 / near_upper_sd1 / near_lower_sd1 / outside_sd1 / outside_sd2
flow_direction: BUY / SELL / WAIT
confidence
notes
```

## Rule ที่ควรเพิ่มใน trad

1. ถ้า price อยู่ใน SD1 และใกล้ magnet + volatility ต่ำ → regime = range_mean_reversion / magnet
2. ถ้า price แตะ SD1 edge แล้ว rejection กลับเข้า range → favor mean reversion
3. ถ้า price breakout ออกนอก SD1 พร้อม volume/ATR expansion → favor trend_momentum / breakout
4. ถ้า OI proxy ขัดกับ MTF technical → decision = WAIT_CONFIRMATION
5. ถ้า basis stale หรือไม่รู้ basis → ลด proxy score เหลือ neutral ไม่เดา
6. วัน expiry / settlement ให้ OI magnet มีน้ำหนักมากกว่าวันปกติ

## ข้อจำกัดข้อมูลใน trad ปัจจุบัน

- Spot XAUUSD ไม่มี centralized OI
- TradingView MCP ปัจจุบันมี futures snapshot แต่ยังไม่มี historical intraday OI/strike OI แบบที่ผู้พูดใช้
- GLD options V/OI ใช้เป็น proxy ได้ แต่ไม่เท่ากับ XAUUSD futures/options โดยตรง
- ต้องมี data source เพิ่มสำหรับ:
  - COMEX gold options OI by strike
  - futures basis realtime
  - intraday IV / expected move
  - expiry calendar

## Implementation status ใน trad

Implemented แล้ว:

- Pure service: `src/tradingview_mcp/core/services/oi_expected_range_service.py`
- Function: `score_oi_expected_range(...)`
- MCP tool: `oi_expected_range_score`
- Tests: `tests/unit/services/test_oi_expected_range_service.py`

Tool นี้ไม่ fetch OI เอง แต่รับค่า manual/proxy จากผู้ใช้หรือ upstream data แล้วคำนวณ:

- basis-adjusted proxy
- expected move
- SD1 / SD2 range
- range_state
- regime_hint
- `flow_context` ที่ feed เข้า `strategy_regime_score` ได้

Input หลัก:

- `current_price`
- `anchor_price`
- `expected_move` หรือ `iv_daily_pct`
- `oi_magnet_zone`
- `basis`
- `proxy_underlying_price`
- `price_action_state`
- `volatility_state`
- `volume_state`
- `expiry_context`

การเชื่อมกับ `strategy_regime_score`:

- proxy confirms → เพิ่มคะแนน flow
- proxy conflicts → WAIT_CONFIRMATION
- stale/no basis → neutral/low-confidence score

## สรุปสั้น

วิธีของวิดีโอนี้เหมาะนำเข้า trad ในฐานะ `OI expected range / magnet module` ไม่ใช่ strategy เดี่ยว ใช้เติมช่องว่าง OI/proxy ใน XAUUSD intraday โดยเฉพาะการตีกรอบ 1 SD จาก options expected move แล้วใช้ร่วมกับ MTF, SMC, volume, ATR และ risk plan
