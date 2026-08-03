# Trad Token-Efficient AI + Dashboard Plan

> **For Hermes:** ถ้าจะ implement ให้ใช้ `writing-plans` + TDD และแตกเป็น phase สั้น ๆ ก่อนลงมือ

**Goal:** ลด token ในการวิเคราะห์เทรด โดยย้ายงานดึงข้อมูล/คำนวณ/score ไปอยู่ใน deterministic Python services + SQLite แล้วให้ AI อ่านเฉพาะ compact summary เพื่อสรุปแผน BUY/SELL สั้น ๆ

**Architecture:** Python `tradingview_mcp` ยังเป็นแกนหลักสำหรับ MCP/data/service logic ส่วน Dashboard ทำเป็น Next.js app แยกชั้น UI โดยอ่านข้อมูลจาก SQLite/API ที่ Python เขียนไว้ ไม่ควรแปลง MCP server ทั้งหมดเป็น Next.js เพราะ MCP tools, collectors, tradingview-ta/screener dependencies และ Hermes MCP config ตอนนี้อยู่บน Python แล้ว

**Tech Stack:** Python MCP server, SQLite, scheduled collector/job, optional FastAPI/internal HTTP API, Next.js App Router dashboard, TypeScript, Tailwind/shadcn optional

---

## คำตัดสินเชิงออกแบบ

ใช้แนวทาง Hybrid:

1. Code/Python เป็นตัวดึงข้อมูลและคำนวณก่อน
2. เก็บ snapshot + feature + signal ลง SQLite
3. AI อ่านเฉพาะ compact JSON ล่าสุด
4. AI ทำหน้าที่สรุปภาษามนุษย์/แผนเข้าไม้ ไม่ใช่วิเคราะห์ raw data ทั้งหมด

เหตุผล:

- ประหยัด token มากกว่าให้ AI เรียก TradingView/OI/options output ยาว ๆ ทุกครั้ง
- Logic เช่น SD range, OI magnet, volume ratio, regime score ควร deterministic และ test ได้
- มีข้อมูลย้อนหลังสำหรับ backtest/รีวิวสัญญาณ
- ทำ alert Telegram ได้ง่ายขึ้น
- Dashboard อ่าน state ล่าสุดได้โดยไม่ต้องเรียก LLM

---

## คำตอบเรื่อง Next.js

### เพิ่ม Dashboard ด้วย Next.js ได้ไหม?

ได้ และควรทำเป็น app แยกจาก Python MCP server เช่น:

```text
trad/
  dashboard/                 # Next.js app
  src/tradingview_mcp/       # Python MCP/data/scoring engine เดิม
```

Dashboard ใช้สำหรับ:

- ดูราคา/score ล่าสุด
- ดู OI/volume proxy
- ดู SD1/SD2 range
- ดู entry/SL/TP ล่าสุด
- ดูประวัติ signal
- ตั้งค่า threshold เช่น score >= 70, RR >= 1.5

### `src/tradingview_mcp/` ที่เป็น Python ทำเป็น Next.js ได้ไหม?

ทำได้บางส่วน แต่ไม่แนะนำให้แปลงทั้งหมด

ควรแบ่งแบบนี้:

- Python อยู่ต่อ:
  - MCP server
  - TradingView MCP tools
  - `strategy_regime_score`
  - `oi_expected_range_score`
  - collectors
  - feature/signal engine
  - SQLite writer

- Next.js ทำเฉพาะ:
  - UI dashboard
  - chart/table/card
  - API routes แบบอ่าน DB ได้ ถ้าใช้ Node SQLite
  - หรือ fetch จาก Python API

ไม่ควรย้ายทั้งหมดไป Next.js เพราะ:

- Hermes MCP config ตอนนี้ชี้ Python entrypoint `tradingview-mcp`
- dependency หลักเป็น Python: `tradingview-ta`, `tradingview-screener`, MCP SDK Python
- MCP server ที่มีอยู่ test ผ่านแล้ว
- การแปลงเป็น Next.js จะเสี่ยงแตกและเสียเวลาโดยไม่จำเป็น

---

## Target Architecture

```text
Telegram / CLI User
        |
        v
Hermes AI
        |
        | calls compact MCP tool only
        v
latest_trade_signal(symbol="XAUUSD")
        |
        v
SQLite latest signal / features
        ^
        |
Scheduled Collector Jobs
        |
        +--> OANDA:XAUUSD 5m/15m/1h/4h
        +--> GLD options proxy
        +--> Metals futures volume proxy
        +--> Strategy/OI/SD feature engine

Next.js Dashboard
        |
        +--> read SQLite directly OR fetch Python API
        +--> display latest signal/history
```

---

## Data Flow

### Scheduled collection loop

ทุก 1-5 นาที:

1. ดึง XAUUSD 5m/15m จาก TradingView MCP/service
2. ดึง 1h/4h ตามรอบที่ช้ากว่า เช่น 5-15 นาที
3. ดึง GLD options/unusual activity ตามรอบ เช่น 5-15 นาที
4. ดึง metals futures snapshot ตามรอบ เช่น 5-15 นาที
5. คำนวณ feature:
   - SD1/SD2
   - OI magnet
   - basis-adjusted proxy
   - volume ratio
   - ATR/BBW/RSI/EMA/MACD state
   - MTF alignment
   - SMC proxy แบบง่าย
6. คำนวณ signal:
   - BUY / SELL / WAIT
   - entry zone
   - SL
   - TP1/TP2/TP3
   - confidence
   - reason codes
7. บันทึก SQLite

### User asks trade plan

1. Hermes เรียก `latest_trade_signal(symbol="XAUUSD")`
2. Tool คืน compact JSON ไม่ใช่ raw output ยาว
3. AI สรุปเป็นรูปแบบสั้น:

```text
XAUUSD 4078
Bias: SELL
Entry: 4088-4093
SL: 4102
TP: 4075 / 4062 / 4050
Action: รอเด้งเข้าโซน ไม่ไล่ขายกลางทาง
```

---

## Proposed File Structure

```text
src/tradingview_mcp/
  core/
    storage/
      __init__.py
      database.py
      migrations.py
      repositories.py

    collectors/
      __init__.py
      market_collector.py
      options_flow_collector.py
      futures_collector.py

    services/
      feature_engine.py
      signal_engine.py
      oi_expected_range_service.py       # exists
      strategy_regime_service.py         # exists

    jobs/
      __init__.py
      collect_market_snapshot.py
      score_latest_signal.py

  server.py                              # add latest_trade_signal MCP tool

dashboard/
  package.json
  src/app/
    page.tsx
    signals/page.tsx
    api/signals/latest/route.ts
  src/components/
    SignalCard.tsx
    ScoreBreakdown.tsx
    SdRangeChart.tsx
    SignalHistoryTable.tsx
  src/lib/
    db.ts or api.ts
```

---

## SQLite Schema Draft

```sql
CREATE TABLE market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  exchange TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  price REAL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  rsi REAL,
  atr REAL,
  bbw REAL,
  ema20 REAL,
  ema50 REAL,
  ema200 REAL,
  macd REAL,
  raw_json TEXT,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_market_snapshots_symbol_tf_time
ON market_snapshots(symbol, timeframe, created_at DESC);

CREATE TABLE option_flow_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proxy_symbol TEXT NOT NULL,
  underlying_price REAL,
  total_call_volume REAL,
  total_put_volume REAL,
  put_call_ratio REAL,
  top_call_strikes_json TEXT,
  top_put_strikes_json TEXT,
  unusual_activity_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE oi_expected_ranges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  current_price REAL NOT NULL,
  anchor_price REAL NOT NULL,
  expected_move REAL,
  sd1_low REAL,
  sd1_high REAL,
  sd2_low REAL,
  sd2_high REAL,
  magnet_zone REAL,
  range_state TEXT,
  flow_bias TEXT,
  confidence TEXT,
  raw_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE strategy_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  bias TEXT NOT NULL,
  decision TEXT NOT NULL,
  total_score INTEGER,
  regime TEXT,
  score_breakdown_json TEXT,
  levels_json TEXT,
  raw_json TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE trade_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  bias TEXT NOT NULL,
  decision TEXT NOT NULL,
  entry_low REAL,
  entry_high REAL,
  sl REAL,
  tp1 REAL,
  tp2 REAL,
  tp3 REAL,
  confidence TEXT,
  reason_codes_json TEXT,
  source_score_id INTEGER,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL
);
```

---

## Compact JSON for AI

MCP tool `latest_trade_signal` should return this shape:

```json
{
  "symbol": "XAUUSD",
  "exchange": "OANDA",
  "price": 4078.2,
  "data_age_seconds": 45,
  "bias": "SELL",
  "decision": "TRADE",
  "score": 74,
  "confidence": "High",
  "regime": "range_mean_reversion",
  "sd_range": {
    "anchor": 4100,
    "sd1_low": 4075,
    "sd1_high": 4125,
    "sd2_low": 4050,
    "sd2_high": 4150,
    "state": "near_lower_sd1"
  },
  "oi_proxy": {
    "magnet": 4100,
    "flow_bias": "SELL_WEAK",
    "confidence": "Medium"
  },
  "volume": {
    "state": "above_average",
    "ratio": 1.8
  },
  "levels": {
    "support": [4075, 4062],
    "resistance": [4090, 4100]
  },
  "plan": {
    "entry_zone": "4088-4093",
    "sl": 4102,
    "tp": [4075, 4062, 4050],
    "invalidation": "ปิด 15m เหนือ 4102"
  },
  "reason_codes": [
    "MTF_SELL_ALIGNMENT",
    "PRICE_REJECTED_RESISTANCE",
    "VOLUME_ABOVE_AVERAGE",
    "RR_OK"
  ]
}
```

---

## Signal Logic Draft

```text
if data_age_seconds > max_age:
    decision = STALE_DATA

elif total_score >= 70 and rr >= 1.5 and volume_confirmed:
    decision = TRADE

elif 55 <= total_score < 70:
    decision = WAIT_CONFIRMATION

else:
    decision = NO_TRADE
```

BUY setup:

```text
Prefer BUY when:
- MTF is bullish or 15m CHoCH/BOS up
- price near demand/support/lower SD
- OI/flow does not strongly conflict
- volume confirms rejection or breakout
```

SELL setup:

```text
Prefer SELL when:
- MTF is bearish or 15m CHoCH/BOS down
- price near supply/resistance/upper SD
- OI/flow does not strongly conflict
- volume confirms rejection or breakdown
```

Conflict rule:

```text
If OI/SD says BUY but MTF/SMC says SELL:
    downgrade to WAIT_CONFIRMATION

If signal is at middle of range with no RR:
    downgrade to NO_TRADE
```

---

## Implementation Phases

### Phase 1: SQLite + latest signal skeleton

Goal: มี DB และ MCP tool อ่าน latest signal ได้ แม้ยังเป็น mocked/minimal data จาก score ปัจจุบัน

Tasks:

1. Create storage package
   - `src/tradingview_mcp/core/storage/database.py`
   - `src/tradingview_mcp/core/storage/migrations.py`
   - `src/tradingview_mcp/core/storage/repositories.py`

2. Add unit tests for DB init and insert/read latest signal
   - `tests/unit/storage/test_repositories.py`

3. Add `latest_trade_signal` tool to `server.py`
4. Add `analyze_and_store_signal` automation connector so Telegram/Hermes can refresh analysis and persist the dashboard signal in one call

5. Test:

```bash
uv run pytest tests/unit -q
```

---

### Phase 2: Market snapshot collector

Goal: ดึง XAUUSD analysis แล้วเก็บ snapshot

Tasks:

1. Add `market_collector.py`
2. Normalize output from `analyze_coin`
3. Insert `market_snapshots`
4. Add job script `collect_market_snapshot.py`
5. Test collector with monkeypatched data

---

### Phase 3: OI/options proxy collector

Goal: เก็บ GLD options/unusual activity และ futures volume proxy

Tasks:

1. Add `options_flow_collector.py`
2. Add `futures_collector.py`
3. Store proxy snapshots
4. Add tests with fixture data

Rule: ห้าม invent OI ถ้าไม่มี source ให้เก็บเป็น proxy/null พร้อม source label

---

### Phase 4: Feature + Signal engine

Goal: คำนวณ SD/OI/range/entry/SL/TP ด้วย code

Tasks:

1. Add `feature_engine.py`
2. Add `signal_engine.py`
3. Reuse existing:
   - `oi_expected_range_service.py`
   - `strategy_regime_service.py`
4. Generate `trade_signals`
5. Add tests for BUY/SELL/WAIT scenarios

---

### Phase 5: Dashboard Next.js

Goal: UI ดู latest signal/history โดยไม่ต้องใช้ LLM

Recommended path:

```text
dashboard/
```

Pages:

- `/` latest XAUUSD signal
- `/signals` signal history
- `/settings` thresholds later

Data access options:

Option A: Next.js reads SQLite directly
- ง่ายสำหรับ local dashboard
- ต้องใช้ package เช่น `better-sqlite3`
- ระวัง DB lock ถ้า Python เขียนบ่อย

Option B: Python exposes read-only API, Next.js fetches API
- แนะนำกว่าในระยะยาว
- Python เป็นเจ้าของ DB คนเดียว
- Next.js ไม่ต้องแตะ DB โดยตรง

Recommendation: เริ่ม Option A ได้ถ้าต้องการเร็ว แต่โครงสร้างที่ดีคือ Option B

---

### Phase 6: Alerts

Goal: แจ้ง Telegram เมื่อเข้าเงื่อนไข

Rules:

- score >= 70
- decision = TRADE
- price in entry zone
- RR >= 1.5
- data not stale
- no duplicate alert in cooldown window

---

## Verification Commands

Python:

```bash
uv run pytest tests/unit -q
```

Dashboard:

```bash
cd dashboard
npm run lint
npm run build
```

Manual MCP check:

```text
เรียก latest_trade_signal(symbol="XAUUSD") แล้วต้องได้ compact JSON ไม่เกินจำเป็น
```

---

## Recommended Starting Point

เริ่มจาก Phase 1 ก่อน:

`SQLite storage + latest_trade_signal`

เพราะเป็น foundation ที่ทำให้:

- AI ประหยัด token ทันที
- Dashboard มี data source
- Collector/Signal/Alert ต่อเพิ่มได้ทีละชั้น

