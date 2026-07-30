# OI / Intraday / Open Interest Data Guide สำหรับ trad

เอกสารนี้กำหนดวิธีใช้ข้อมูล OI, Intraday flow และ Open Interest ในการวิเคราะห์กราฟด้วย Hermes + TradingView MCP

> ใช้เป็นข้อมูลประกอบการวิเคราะห์ ไม่ใช่คำแนะนำการลงทุน

---

## 1. นิยามที่ต้องใช้

### Open Interest (OI)

Open Interest คือจำนวน futures/options contracts ที่ยังเปิดค้างอยู่และยังไม่ถูกปิดหรือส่งมอบ

ใช้ดูว่า move มี “position ใหม่” เข้ามาหรือไม่ ไม่ใช่ดูแค่มีการซื้อขายเยอะอย่างเดียว

### Volume

Volume คือจำนวนสัญญาที่ซื้อขายในช่วงเวลานั้น อาจเกิดจากเปิด position ใหม่หรือปิด position เก่าก็ได้

### Intraday Flow

Intraday Flow คือการตีความแรงซื้อขายระหว่างวันจาก:

- price movement
- volume spike
- session high/low
- liquidity sweep
- options volume/open_interest ratio
- futures volume/open interest ถ้ามี source รองรับ

---

## 2. ข้อจำกัดสำคัญสำหรับ XAUUSD

ค่า default ของผู้ใช้คือ:

```text
OANDA:XAUUSD
```

แต่ OANDA:XAUUSD เป็น spot/CFD price feed จึงไม่มี centralized Open Interest จริงเหมือน CME futures/options

ดังนั้นเวลาใช้ OI กับ XAUUSD ให้แยก 2 ชั้น:

1. ราคาเข้าออก / technical / SMC
   - ใช้ `OANDA:XAUUSD`

2. OI / institutional positioning proxy
   - ใช้ CME/COMEX Gold futures/options ถ้ามีข้อมูล
   - ใช้ futures/options flow เป็น backdrop เท่านั้น
   - ห้ามเอาราคา futures (`GC=F`, `GC1!`) มาแทน spot entry โดยตรง

---

## 3. Price + OI Matrix

| ราคา | OI | ตีความ | ใช้กับแผน |
|---|---|---|---|
| ขึ้น | เพิ่ม | BUY ใหม่เข้า / trend แข็งแรง | มอง BUY continuation ถ้า SMC สนับสนุน |
| ขึ้น | ลด | SELL covering | ระวังขึ้นหลอก / buy-side sweep |
| ลง | เพิ่ม | SELL ใหม่เข้า | มอง SELL continuation ถ้า structure bearish |
| ลง | ลด | BUY liquidation | ระวังลงล้างพอร์ตแล้วกลับตัว |

---

## 4. Intraday OI / Flow Checklist

ก่อนวางแผน intraday ให้ตรวจ:

- ราคาตอนนี้อยู่เหนือ/ใต้ previous day high/low หรือไม่
- เกิด sweep Asian high/low หรือ London/NY session high/low หรือไม่
- มี volume spike ตอน sweep หรือ breakout หรือไม่
- ถ้ามี options data: strike ไหนมี V/OI สูงผิดปกติ
- Put/Call volume ratio เอียงทาง call หรือ put
- IV เพิ่มขึ้นพร้อม price move หรือไม่
- ถ้า OI unavailable ให้บอกชัดเจนว่าไม่มี OI data และใช้ volume/price action เป็น proxy

---

## 5. V/OI Ratio สำหรับ Options

V/OI = today volume / open interest

ความหมาย:

- `> 1.0` — volume วันนี้มากกว่า OI เดิม อาจมี flow ใหม่เข้า
- `0.5 - 1.0` — activity สูง ต้องดู bid/ask, IV, moneyness
- `< 0.5` — ปกติ/น้ำหนักต่ำ เว้นแต่ strike สำคัญมาก

ต้องดูร่วมกับ:

- side: call หรือ put
- strike เทียบ spot
- expiry ใกล้หรือไกล
- volume absolute สูงพอหรือไม่
- bid/ask spread กว้างเกินไปหรือไม่
- implied volatility สูงผิดปกติหรือไม่

---

## 6. MCP Tools ที่ใช้ได้ใน trad ตอนนี้

### 6.1 Options Chain — มี open_interest

ใช้กับ US stock/ETF options ที่ Yahoo รองรับ เช่น SPY, QQQ, GLD, AAPL, NVDA

```text
mcp_tradingview_stock_options_chain(symbol="GLD")
```

ข้อมูลที่ได้:

- strike
- call/put
- last price
- bid/ask
- volume
- open_interest
- implied_volatility
- expiration

### 6.2 Unusual Options Activity — ใช้ V/OI

```text
mcp_tradingview_stock_options_unusual_activity(symbol="GLD", top_n=10, min_volume=100, expiries=4)
```

ใช้ดู:

- volume/open_interest ratio
- put/call volume ratio
- strike ที่มี positioning ใหม่
- moneyness เทียบ spot

สำหรับทอง ถ้าไม่มี futures options data โดยตรงใน tool ให้ใช้ `GLD` options เป็น proxy เสริมเท่านั้น และต้องบอกผู้ใช้ว่าไม่ใช่ XAUUSD โดยตรง

### 6.3 Futures Snapshot — ใช้ volume แต่ไม่ใช่ OI

```text
mcp_tradingview_futures_category_snapshot(category="metals")
```

ข้อมูลที่ได้:

- COMEX:GC1! Gold Futures
- close/open/high/low
- volume
- change

ข้อจำกัด:

- tool นี้ไม่ได้คืน open_interest
- ใช้เป็น futures volume/price backdrop ได้ แต่ไม่ใช่ OI

### 6.4 XAUUSD Technical / Intraday

```text
mcp_tradingview_coin_analysis(symbol="XAUUSD", exchange="OANDA", timeframe="15m")
```

ใช้สำหรับ:

- spot price
- intraday candle context
- RSI/MACD/SMA/EMA
- Bollinger Band Width
- ATR
- support/resistance
- market structure เบื้องต้น

---

## 7. วิธีผสม OI เข้ากับ SMC

### Bullish Reversal Setup

น้ำหนักเพิ่มเมื่อ:

- OANDA:XAUUSD sweep sell-side liquidity
- 15M/5M เกิด bullish CHoCH
- ราคา reclaim demand หรือ bullish FVG
- GLD/options proxy มี call V/OI สูง หรือ put activity ลดลง
- futures gold volume เพิ่มตอน reversal

### Bearish Reversal Setup

น้ำหนักเพิ่มเมื่อ:

- OANDA:XAUUSD sweep buy-side liquidity
- 15M/5M เกิด bearish CHoCH
- ราคา reject supply หรือ bearish FVG
- GLD/options proxy มี put V/OI สูง หรือ call activity เป็น SELL covering
- futures gold volume เพิ่มตอน rejection

### Continuation Setup

น้ำหนักเพิ่มเมื่อ:

- HTF มี BOS ตามทิศ trend
- retrace เข้า OB/FVG แล้วไม่หลุด invalidation
- volume เพิ่มตอน break
- OI/proxy flow ไปทางเดียวกับราคา

---

## 8. Output Block ที่ต้องเพิ่มในการวิเคราะห์

เวลาวิเคราะห์ XAUUSD หรือสินทรัพย์ที่ผู้ใช้ขอ OI ให้เพิ่มหัวข้อนี้:

```text
OI / Intraday Positioning
- OI source: available / unavailable / proxy
- Source used: OANDA spot / COMEX futures / GLD options / other
- OI read: increasing / decreasing / unavailable
- Volume read: rising / normal / weak
- V/OI unusual strikes: ...
- Interpretation: new BUY positions / new SELL positions / SELL covering / BUY liquidation / unclear
- Confidence impact: เพิ่มน้ำหนัก / ลดน้ำหนัก / ยังไม่ใช้ตัดสินใจ
```

---

## 9. Decision Rule

- ถ้า price action + SMC + OI/proxy ไปทางเดียวกัน: confidence สูงขึ้น
- ถ้า price action ขึ้นแต่ OI ลด: ระวัง SELL covering หรือ sweep
- ถ้า price action ลงแต่ OI ลด: ระวัง BUY liquidation ใกล้จบ move
- ถ้า OI unavailable: ห้ามเดา ให้บอกว่า OI ไม่มีข้อมูล แล้วใช้ framework อื่นแทน
- ถ้าข้อมูล proxy ขัดแย้งกับ OANDA:XAUUSD: ให้ OANDA:XAUUSD เป็นหลักสำหรับ entry แต่ลด conviction

---

## 10. Quick Prompt

```text
วิเคราะห์ OANDA:XAUUSD โดยรวม SMC + intraday + OI/Open Interest ถ้า OI ของ spot ไม่มี ให้ใช้ COMEX/GLD options เป็น proxy และบอกข้อจำกัด สรุป bias, liquidity, OB/FVG, volume, OI interpretation, entry, SL, TP, invalidation
```
