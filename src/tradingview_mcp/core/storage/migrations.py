"""SQLite schema for cached market snapshots and compact trade signals."""
from __future__ import annotations

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS market_snapshots (
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

CREATE INDEX IF NOT EXISTS idx_market_snapshots_symbol_tf_time
ON market_snapshots(symbol, timeframe, created_at DESC);

CREATE TABLE IF NOT EXISTS option_flow_snapshots (
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

CREATE TABLE IF NOT EXISTS oi_expected_ranges (
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

CREATE TABLE IF NOT EXISTS strategy_scores (
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

CREATE TABLE IF NOT EXISTS trade_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  exchange TEXT DEFAULT 'OANDA',
  instrument TEXT,
  timeframe TEXT DEFAULT '15m',
  price REAL,
  bias TEXT NOT NULL,
  decision TEXT NOT NULL,
  entry_low REAL,
  entry_high REAL,
  sl REAL,
  tp1 REAL,
  tp2 REAL,
  tp3 REAL,
  confidence TEXT,
  total_score INTEGER,
  regime TEXT,
  sd_range_json TEXT,
  oi_proxy_json TEXT,
  volume_json TEXT,
  technical_json TEXT,
  levels_json TEXT,
  score_breakdown_json TEXT,
  reason_codes_json TEXT,
  ai_gate_json TEXT,
  source_score_id INTEGER,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL,
  FOREIGN KEY(source_score_id) REFERENCES strategy_scores(id)
);

CREATE INDEX IF NOT EXISTS idx_trade_signals_symbol_tf_time
ON trade_signals(symbol, timeframe, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_signal_responses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  signal_fingerprint TEXT NOT NULL,
  ai_response TEXT NOT NULL,
  source TEXT,
  created_at TEXT NOT NULL,
  last_used_at TEXT NOT NULL,
  expires_at TEXT,
  UNIQUE(symbol, timeframe, signal_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_ai_signal_responses_lookup
ON ai_signal_responses(symbol, timeframe, signal_fingerprint);

CREATE TABLE IF NOT EXISTS ai_signal_alert_deliveries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  signal_fingerprint TEXT NOT NULL,
  target TEXT NOT NULL,
  delivered_at TEXT NOT NULL,
  UNIQUE(symbol, timeframe, signal_fingerprint, target)
);

CREATE INDEX IF NOT EXISTS idx_ai_signal_alert_deliveries_lookup
ON ai_signal_alert_deliveries(symbol, timeframe, signal_fingerprint, target);
"""

POST_SCHEMA_COLUMNS = {
    "trade_signals": {
        "instrument": "TEXT",
        "technical_json": "TEXT",
        "score_breakdown_json": "TEXT",
        "ai_gate_json": "TEXT",
    },
}
