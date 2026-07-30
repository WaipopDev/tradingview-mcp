# Trading Analysis Playbook สำหรับ Hermes + TradingView MCP

เอกสารนี้ใช้เป็นฐานข้อมูล/คู่มือสำหรับให้ Hermes วิเคราะห์กราฟราคา โดยเฉพาะ XAUUSD ที่ผู้ใช้ตั้งค่าให้ใช้อ้างอิงเป็น `OANDA:XAUUSD` ผ่าน TradingView MCP

> ข้อจำกัด: เอกสารนี้เป็นกรอบวิเคราะห์เชิงข้อมูล ไม่ใช่คำแนะนำการลงทุน ต้องยืนยันด้วยราคา realtime, timeframe หลายระดับ, risk/reward และแผนจัดการความเสี่ยงทุกครั้งก่อนตัดสินใจ

---

## 1. Default Instrument และ Data Source

### XAUUSD / Gold

ให้ใช้ค่าเริ่มต้นนี้เมื่อผู้ใช้ถามถึง gold, ทอง, หรือ XAUUSD:

- Instrument: `OANDA:XAUUSD`
- MCP tool หลัก: `coin_analysis`
- Params:
  - `symbol="XAUUSD"`
  - `exchange="OANDA"`
  - timeframe ตามคำถาม ถ้าไม่ระบุให้เริ่มที่ `15m` แล้วตรวจ `1h`, `4h`, `1D` เพิ่ม

หลีกเลี่ยงการใช้ `GC=F` เป็นค่าอ้างอิงหลัก เพราะ `GC=F` คือ Gold Futures ไม่ใช่ XAUUSD spot และราคาจะต่างจาก spot/broker feed ได้

### Timeframe มาตรฐาน

ใช้ multi-timeframe เสมอเมื่อวางแผน trade:

1. `1D` — macro bias / major swing / key liquidity
2. `4h` — trend structure / premium-discount zone
3. `1h` — setup zone / liquidity sweep / order block
4. `15m` — execution setup
5. `5m` — entry trigger เฉพาะกรณีต้องการจุดเข้าแม่นขึ้น

---

## 2. Minimum Analysis Frameworks ที่ต้องใช้ก่อนวางแผน

ให้วิเคราะห์อย่างน้อย 5 กรอบจากรายการนี้ทุกครั้ง และถ้าเป็น XAUUSD ให้เริ่มจากชุด Recommended 7 ข้อ

### Recommended 7 Frameworks

1. SMC / Smart Money Concept
2. Market Structure / Trend Bias
3. Liquidity Mapping
4. Supply-Demand / Order Block
5. Fair Value Gap / Imbalance
6. Multi-Timeframe Confirmation
7. Risk Plan / Entry-Stop-Target
8. OI / Open Interest / Intraday Positioning

---

## 3. SMC — Smart Money Concept

SMC ใช้ตีความพฤติกรรมราคาผ่าน liquidity, market structure และ institutional order flow

### 3.1 Market Structure

ต้องระบุให้ได้ว่า timeframe หลักอยู่ในโครงสร้างใด:

- Bullish structure: ทำ Higher High (HH) และ Higher Low (HL)
- Bearish structure: ทำ Lower Low (LL) และ Lower High (LH)
- Range / Consolidation: ไม่มี high/low ใหม่ชัดเจน ราคาแกว่งในกรอบ

คำที่ต้องตรวจ:

- BOS — Break of Structure: ราคาทะลุ swing สำคัญตามทิศทาง trend เดิม
- CHoCH — Change of Character: สัญญาณแรกที่โครงสร้างอาจเปลี่ยนทิศ
- MSS — Market Structure Shift: การเปลี่ยน bias ที่ชัดขึ้นหลัง CHoCH

Checklist:

- ระบุ swing high ล่าสุด
- ระบุ swing low ล่าสุด
- ระบุว่าราคาเพิ่ง BOS หรือ CHoCH หรือยัง
- ระบุ bias หลัก: bullish / bearish / range

### 3.2 Liquidity

Liquidity คือบริเวณที่มี stop orders จำนวนมาก มักอยู่รอบ high/low สำคัญ

ประเภทที่ต้องหา:

- Buy-side liquidity (BSL): เหนือ equal highs / swing highs / resistance
- Sell-side liquidity (SSL): ใต้ equal lows / swing lows / support
- Equal highs / Equal lows: จุดที่ราคาทำ high/low ใกล้กันหลายครั้ง
- Previous day high/low
- Asian session high/low สำหรับ XAUUSD intraday
- Weekly high/low สำหรับ swing plan

สัญญาณสำคัญ:

- Liquidity sweep: ราคาทะลุ high/low สำคัญแล้วกลับเข้ากรอบอย่างรวดเร็ว
- Stop hunt: sweep liquidity แล้วเกิด rejection candle หรือ displacement

### 3.3 Order Block

Order Block คือ candle zone ก่อนเกิด displacement/BOS สำคัญ ใช้เป็นโซนรอราคากลับมาทดสอบ

Bullish Order Block:

- bearish candle สุดท้ายก่อนราคา impulse ขึ้นแรง
- ควรตามด้วย BOS หรือ displacement ขึ้น
- ใช้เป็น demand zone สำหรับรอ BUY

Bearish Order Block:

- bullish candle สุดท้ายก่อนราคา impulse ลงแรง
- ควรตามด้วย BOS หรือ displacement ลง
- ใช้เป็น supply zone สำหรับรอ SELL

Validation:

- ต้องมี displacement ออกจาก zone
- ต้องมี inefficiency/FVG หรือ break structure สนับสนุน
- zone ที่ถูกแตะหลายครั้งแล้วคุณภาพลดลง

### 3.4 Fair Value Gap / Imbalance

FVG คือช่องว่างราคา 3-candle pattern ที่แสดง imbalance

Bullish FVG:

- candle 1 high ต่ำกว่า candle 3 low
- ราคา impulse ขึ้นแรงและทิ้ง imbalance
- ใช้เป็นโซนรอ retracement เข้า BUY ถ้า bias bullish

Bearish FVG:

- candle 1 low สูงกว่า candle 3 high
- ราคา impulse ลงแรงและทิ้ง imbalance
- ใช้เป็นโซนรอ retracement เข้า SELL ถ้า bias bearish

Rule:

- FVG ที่อยู่ใน premium/discount zone และ align กับ HTF bias มีน้ำหนักมากกว่า
- ถ้าราคาปิดเต็ม gap แล้วไม่เด้ง ให้ลดความสำคัญของ FVG นั้น

### 3.5 Premium / Discount

ใช้ Fibonacci 0.5 ของ swing ล่าสุดเพื่อดูว่าราคาอยู่โซนไหน:

- Premium: เหนือ 50% ของ range — เหมาะหา SELL ถ้า bias bearish
- Discount: ต่ำกว่า 50% ของ range — เหมาะหา BUY ถ้า bias bullish
- Equilibrium: ใกล้ 50% — ระวัง chop / wait for confirmation

---

## 4. Market Structure / Trend Bias

ใช้เพื่อสรุปทิศทางหลักของราคาแบบไม่ยึดติด SMC อย่างเดียว

ข้อมูลที่ต้องดู:

- ราคาอยู่เหนือ/ใต้ EMA 20, EMA 50, EMA 200
- slope ของ EMA
- ADX บอก trend strength
- RSI อยู่ใน bullish/bearish regime หรือไม่
- MACD crossover สนับสนุนทิศทางหรือขัดแย้ง

แนวทางสรุป:

- Bullish bias: price above EMA50/200 + HH/HL + RSI > 50
- Bearish bias: price below EMA50/200 + LL/LH + RSI < 50
- Neutral/range: EMA flat + RSI 40-60 + ADX ต่ำ

---

## 5. Liquidity Mapping

ก่อนเข้า trade ต้องวาดแผน liquidity เสมอ:

1. ใส่ high/low ของวันก่อนหน้า
2. ใส่ high/low ของ session ปัจจุบัน
3. หา equal highs / equal lows
4. หา swing high/low ล่าสุดใน 1h และ 4h
5. ระบุ target liquidity ที่ราคาอาจวิ่งไปเก็บ

คำถามที่ต้องตอบ:

- ตอนนี้ราคาอยู่ใกล้ buy-side หรือ sell-side liquidity มากกว่า?
- มีการ sweep liquidity แล้วหรือยัง?
- หลัง sweep มี rejection หรือ displacement หรือไม่?
- target ถัดไปคือ liquidity pool ไหน?

---

## 6. Supply-Demand / Support-Resistance

ใช้ร่วมกับ order block และ pivot levels

ต้องระบุ:

- Demand zone: พื้นที่ที่มีแรงซื้อชัดเจนและราคาเด้งแรง
- Supply zone: พื้นที่ที่มีแรงขายชัดเจนและราคาถูก reject
- Nearest support / resistance
- Pivot, R1/R2/R3, S1/S2/S3 ถ้ามีจาก MCP output

Zone คุณภาพสูงควรมี:

- impulse move ออกจาก zone
- volume หรือ volatility เพิ่มขึ้น
- เคยถูกทดสอบน้อยครั้ง
- align กับ HTF bias

---

## 7. Volume / Volatility Confirmation

ใช้ยืนยันว่า move มีแรงจริงหรือเป็น fakeout

ตัวชี้วัด:

- Volume ratio เทียบ average
- ATR percent of price
- Candle body ratio
- Wick rejection
- Bollinger Band Width squeeze/expansion

Signal:

- Breakout น่าเชื่อถือ: price break + volume สูง + candle close ชัด
- Fakeout: price wick ทะลุ level แต่ close กลับเข้า range + volume spike
- Low volatility squeeze: รอ expansion ก่อนเข้า ไม่ไล่ราคาใน range แคบ

---

## 7A. OI / Open Interest / Intraday Positioning

ใช้ OI เพื่อแยกให้ออกว่า move เกิดจาก “มีเงินใหม่เข้า” หรือแค่ SELL covering / BUY liquidation

### ความหมายหลัก

- Open Interest (OI): จำนวนสัญญาที่ยังเปิดค้างอยู่ในตลาด futures/options
- Volume: จำนวนสัญญาที่มีการซื้อขายในช่วงเวลานั้น
- Intraday OI: การตีความการเปลี่ยนแปลง positioning ระหว่างวัน ถ้าไม่มี OI real-time ให้ใช้ Volume + Price + V/OI ratio เป็น proxy

### ข้อจำกัดสำหรับ XAUUSD

- `OANDA:XAUUSD` เป็น spot/CFD feed จึงมักไม่มี OI จริงแบบ exchange-cleared
- ถ้าต้องใช้ OI สำหรับทอง ให้ใช้ข้อมูล proxy จากตลาดที่มี centralized exchange เช่น CME/COMEX Gold Futures (`GC`) หรือ Gold options
- ห้ามเอาราคา `GC=F` มาแทนราคา spot โดยตรง แต่ใช้ OI/volume จาก futures/options เพื่อดู positioning และ liquidity backdrop ได้

### Price + OI Interpretation Matrix

| Price | OI | ความหมาย | Bias |
|---|---|---|---|
| ขึ้น | เพิ่ม | มี BUY ใหม่เข้า / trend มีแรงหนุน | Bullish continuation |
| ขึ้น | ลด | SELL covering / move อาจอ่อนแรง | ระวัง fake rally |
| ลง | เพิ่ม | มี SELL ใหม่เข้า / bearish pressure | Bearish continuation |
| ลง | ลด | BUY liquidation / selling อาจเริ่มหมดแรง | ระวัง reversal |

### Intraday Positioning Checklist

ต้องตอบคำถามเหล่านี้ก่อนใช้ OI ประกอบแผน:

1. ราคา break level สำคัญพร้อม volume เพิ่มหรือไม่?
2. OI เพิ่มหรือลดเทียบกับรอบก่อนหน้า / previous session?
3. Move เกิดหลัง sweep liquidity หรือหลังข่าวแรงหรือไม่?
4. Options strike ไหนมี volume/open_interest สูงผิดปกติ?
5. Put/Call volume ratio เอียงไปทาง risk-off หรือ risk-on?
6. ถ้า OI ไม่มี realtime ให้ใช้ V/OI ratio เป็นสัญญาณว่ามี flow ใหม่เข้า strike นั้นหรือไม่

### V/OI Ratio

V/OI = volume วันนี้ / open interest เดิม

- V/OI > 1: volume วันนี้มากกว่า OI เดิม อาจเป็น flow ใหม่หรือ institutional positioning
- V/OI 0.5-1: มี activity สูง แต่ต้องดู bid/ask และ IV เพิ่ม
- V/OI ต่ำ: อาจเป็น noise ถ้า volume น้อย

ใช้ร่วมกับ:

- implied volatility (IV)
- strike moneyness เทียบ spot
- expiration ใกล้/ไกล
- put/call side
- price action บน OANDA:XAUUSD

### วิธีใช้กับ SMC

- ถ้าเกิด liquidity sweep แล้ว price reverse พร้อม volume spike และ V/OI สูง: เพิ่มน้ำหนัก reversal setup
- ถ้าเกิด BOS ตาม trend พร้อม volume สูง และ OI/futures positioning เพิ่ม: เพิ่มน้ำหนัก continuation setup
- ถ้าราคา break high แต่ OI ลด: ระวัง buy-side liquidity sweep / SELL covering rally
- ถ้าราคา break low แต่ OI ลด: ระวัง sell-side liquidity sweep / BUY liquidation flush

---

## 8. Momentum Indicators

ใช้ RSI, MACD, Stochastic เพื่อยืนยัน timing ไม่ใช่ใช้เป็นเหตุผลเดียวในการเข้า

### RSI

- RSI > 50: bullish regime
- RSI < 50: bearish regime
- RSI > 70: overbought แต่ไม่ใช่ SELL signal ทันทีถ้า trend แรง
- RSI < 30: oversold แต่ไม่ใช่ BUY signal ทันทีถ้า trend ลงแรง
- Divergence: ใช้เป็น warning ไม่ใช่ trigger เดี่ยว

### MACD

- Bullish crossover สนับสนุน BUY
- Bearish crossover สนับสนุน SELL
- Histogram ลดลงสวนทางราคา = momentum weakening

### Stochastic

- เหมาะกับ range มากกว่า trend แรง
- ใช้ดู timing ตอนราคากลับเข้า zone

---

## 9. Multi-Timeframe Confirmation

ห้ามใช้ timeframe เดียวในการวางแผน

Template:

- Daily bias: bullish / bearish / range เพราะอะไร
- 4H structure: BOS/CHoCH หรือ range
- 1H setup: liquidity + OB/FVG zone
- 15M execution: entry trigger และ invalidation

Alignment rule:

- Trade ตาม 4H/1H bias ถ้า 15M ให้ trigger ตรงกัน
- ถ้า 15M สวน HTF ให้ถือว่าเป็น scalp เท่านั้น และลด risk
- ถ้า Daily กับ 4H ขัดแย้ง ให้ลด conviction หรือรอ sweep/CHoCH ชัดเจน

---

## 10. Entry Model สำหรับวางแผน

### BUY Setup

เงื่อนไขที่ควรมีอย่างน้อย 4 ข้อ:

1. HTF bullish หรือ price อยู่ใน discount ของ bullish range
2. มี sell-side liquidity sweep
3. เกิด bullish CHoCH/MSS ใน LTF
4. ราคา retrace เข้า bullish OB/FVG/demand
5. RSI/MACD สนับสนุน momentum
6. มี stop loss ใต้ swing low หรือใต้ OB ชัดเจน
7. target ไปที่ BSL / previous high / resistance

### SELL Setup

เงื่อนไขที่ควรมีอย่างน้อย 4 ข้อ:

1. HTF bearish หรือ price อยู่ใน premium ของ bearish range
2. มี buy-side liquidity sweep
3. เกิด bearish CHoCH/MSS ใน LTF
4. ราคา retrace เข้า bearish OB/FVG/supply
5. RSI/MACD สนับสนุน downside momentum
6. stop loss เหนือ swing high หรือเหนือ OB ชัดเจน
7. target ไปที่ SSL / previous low / support

---

## 11. Risk Plan

ทุกแผนต้องมี:

- Bias: BUY / SELL / Wait
- Entry zone: ไม่ใช่ราคาเดียวถ้า spread/volatility สูง
- Invalidation: จุดที่ idea ผิด
- Stop loss: ราคาชัดเจน
- Take profit 1: liquidity ใกล้สุด
- Take profit 2: liquidity ถัดไป
- Risk/Reward: อย่างน้อย 1:2 ถ้าเป็น setup ปกติ
- Position sizing: เสี่ยงต่อไม้ไม่เกินค่าที่ผู้ใช้กำหนด ถ้าไม่กำหนดให้ระบุว่า “ยังไม่ได้กำหนด risk %”

Rule:

- ถ้า RR ต่ำกว่า 1:1.5 ให้แนะนำ wait
- ถ้าใกล้ข่าวแรง เช่น CPI, NFP, FOMC ให้ลด risk หรือรอข่าวผ่านก่อน
- ถ้า spread กว้างผิดปกติ ไม่ควรเข้า market order

---

## 12. Output Format ที่ Hermes ควรใช้เมื่อวิเคราะห์กราฟ

```text
Instrument: OANDA:XAUUSD
Timeframes: 1D / 4H / 1H / 15M
Current price: [จาก MCP]

1) Bias หลัก
- Daily: ...
- 4H: ...
- 1H: ...

2) SMC
- Structure: ...
- Liquidity: ...
- Sweep/BOS/CHoCH: ...
- OB/FVG: ...

3) Confirmation
- EMA/SMA: ...
- RSI/MACD/Stochastic: ...
- Volume/ATR/BBW: ...
- OI/Open Interest/Intraday positioning: ...

4) Trade Plan
- Plan A: BUY/SELL/Wait
- Entry zone: ...
- Stop loss: ...
- TP1: ...
- TP2: ...
- Invalidation: ...
- RR: ...

5) Decision
- Action: เข้าได้ / รอ confirmation / งดเทรด
- เหตุผลสั้น ๆ: ...
```

---

## 13. MCP Tool Usage Guide

### ราคาและ technical ราย timeframe

ใช้:

```text
mcp_tradingview_coin_analysis(symbol="XAUUSD", exchange="OANDA", timeframe="15m")
```

เรียกซ้ำสำหรับ `1h`, `4h`, `1D` เมื่อต้องการวางแผนจริง

### Multi-timeframe overview

ใช้:

```text
mcp_tradingview_multi_timeframe_analysis(symbol="XAUUSD", exchange="OANDA")
```

ถ้า tool map ไป `TVC:GOLD` ให้รายงานผู้ใช้ว่า MCP คืน source เป็นอะไร และอย่าปะปนกับ `GC=F`

### OI / Options / Intraday positioning

ใช้ tool ที่มีข้อมูล `open_interest` เมื่อมี symbol ที่รองรับ options:

```text
mcp_tradingview_stock_options_chain(symbol="SPY")
mcp_tradingview_stock_options_unusual_activity(symbol="SPY", top_n=10, min_volume=100, expiries=4)
```

สำหรับ XAUUSD spot ให้ระบุข้อจำกัดว่า OANDA feed ไม่มี OI จริง และใช้ CME/COMEX futures/options เป็น proxy เท่านั้น ถ้าไม่มี source OI ให้สรุปว่า “OI ยังไม่มีข้อมูลใน tool ปัจจุบัน” แล้ววิเคราะห์จาก price action, volume, ATR และ SMC แทน

### ข่าวและ sentiment

ใช้ได้เมื่อมี `MARKETAUX_API_TOKEN`:

```text
mcp_tradingview_financial_news(symbol="XAU", category="all")
mcp_tradingview_market_sentiment(symbol="XAU", category="all")
```

ถ้าไม่มี token ให้บอกว่า news/sentiment ยังไม่ได้ config และวิเคราะห์จาก price action/TA เป็นหลัก

---

## 14. Checklist ก่อนตอบผู้ใช้

- [ ] ใช้ `OANDA:XAUUSD` สำหรับ XAUUSD/gold spot
- [ ] ไม่ใช้ `GC=F` เว้นแต่ผู้ใช้ถาม Gold Futures โดยตรง
- [ ] ตรวจอย่างน้อย 5 frameworks
- [ ] มี SMC: structure, liquidity, OB/FVG, sweep/BOS/CHoCH
- [ ] มี multi-timeframe bias
- [ ] ตรวจ OI/Open Interest หรือระบุชัดเจนว่าไม่มี OI data สำหรับ source นั้น
- [ ] มี entry/SL/TP/invalidation ถ้าผู้ใช้ขอแผน
- [ ] ถ้าสัญญาณขัดแย้ง ให้ตอบ “รอ” ไม่ฝืนให้เข้า trade
- [ ] ระบุว่าไม่ใช่ financial advice

---

## 15. Quick Prompt สำหรับใช้งาน

```text
วิเคราะห์ OANDA:XAUUSD แบบ SMC + technical + OI/intraday positioning หลาย timeframe ใช้ 1D/4H/1H/15M สรุป bias, liquidity, BOS/CHoCH, OB/FVG, volume/ATR, OI availability, confirmation, entry zone, SL, TP1, TP2, invalidation และบอกว่าควรเข้า/รอ/งดเทรด
```
