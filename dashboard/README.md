# Trad Dashboard

Next.js dashboard สำหรับอ่าน compact trade signal จาก Python `tradingview_mcp` SQLite cache โดยไม่ต้องส่ง raw TradingView/OI output ให้ LLM

## Run

จาก repo root:

```bash
cd dashboard
npm install
npm run dev -- --port 3015
```

เปิด:

```text
http://localhost:3015
```

## Automation connector

หลังเพิ่ม connector แล้ว Telegram/Hermes สามารถเรียก MCP tool นี้เพื่อวิเคราะห์ + บันทึกลง dashboard ในครั้งเดียว:

```text
analyze_and_store_signal(symbol="XAUUSD", exchange="OANDA", timeframe="15m")
```

Flow:

```text
Telegram prompt -> analyze_and_store_signal -> TradingView analysis -> strategy score -> SQLite -> dashboard
```

ทุก 5 นาทีมี local cron job `trad-xauusd-collector-5m` เรียก script นี้เพื่ออัปเดต DB โดยไม่ใช้ LLM:

```text
~/.hermes/scripts/trad_collect_and_ai_alert_xauusd.sh
```

ลำดับงานใน script:

```text
collect_trad_signal.py --json
  -> update SQLite
  -> ถ้า ai_gate.should_ask_ai=true และไม่มี cache
  -> ai_alert_if_needed.py
  -> hermes chat สรุป compact JSON
  -> store AI response ลง ai_signal_responses
  -> hermes send ไป Telegram
```

AI gate logic:

- ไม่ถาม AI ถ้า `decision` ยังไม่ใช่ `TRADE`
- ถ้าเป็น `TRADE` และ score >= 70 พร้อม entry/SL/TP จะตั้ง `ai_gate.should_ask_ai = true`
- ถ้า AI เคยตอบ signal fingerprint เดิมแล้ว ให้ cache ใน `ai_signal_responses` และรอบถัดไปจะไม่ถาม AI ซ้ำ
- ใช้ MCP tool นี้เพื่อบันทึกคำตอบ AI กลับ DB:

```text
store_ai_signal_response(symbol, timeframe, signal_fingerprint, ai_response)
```

จากนั้น dashboard/API จะอ่านข้อมูลล่าสุดจาก DB เดียวกัน

## Data source

API route:

```text
/api/signals/latest?symbol=XAUUSD&timeframe=15m
```

Dashboard จะเรียก Python ผ่าน `uv run python` จาก repo root แล้วอ่าน MCP helper:

```python
from tradingview_mcp.server import latest_trade_signal
```

DB path ใช้ env นี้ถ้ามี:

```bash
TRADINGVIEW_MCP_DB_PATH=/path/to/trading_signals.sqlite3
```

ถ้าไม่ set จะใช้ default:

```text
~/.tradingview-mcp/trading_signals.sqlite3
```

## Seed demo data

จาก repo root:

```bash
TRADINGVIEW_MCP_DB_PATH=/tmp/trad-dashboard-demo.sqlite3 uv run python - <<'PY'
from tradingview_mcp.core.jobs.score_latest_signal import store_compact_trade_signal
store_compact_trade_signal({
    'symbol': 'XAUUSD',
    'exchange': 'OANDA',
    'timeframe': '15m',
    'price': 4078.2,
    'bias': 'SELL',
    'decision': 'TRADE',
    'score': 74,
    'confidence': 'High',
    'regime': 'range_mean_reversion',
    'sd_range': {'anchor': 4100, 'sd1_low': 4075, 'sd1_high': 4125},
    'oi_proxy': {'magnet': 4100, 'flow_bias': 'SELL_WEAK'},
    'volume': {'state': 'above_average', 'ratio': 1.8},
    'levels': {'support': [4075, 4062], 'resistance': [4090, 4100]},
    'plan': {'entry_zone': '4088-4093', 'sl': 4102, 'tp': [4075, 4062, 4050]},
    'reason_codes': ['MTF_SELL_ALIGNMENT', 'RR_OK'],
})
PY
```

แล้ว run dashboard ด้วย DB เดียวกัน:

```bash
TRADINGVIEW_MCP_DB_PATH=/tmp/trad-dashboard-demo.sqlite3 npm run dev -- --port 3015
```

## Verify

```bash
npm run lint
npm run build
```
