#!/usr/bin/env python3
"""Send and track lightweight XAUUSD Scalp Watch alerts.

Scalp Watch is not a full Order # entry. It is a WAIT_CONFIRMATION trigger idea
for M5/M15 rejection setups. When sent, the watch is also persisted into
trade_plan_outcomes as source='telegram_scalp_watch' so MGT/Analyst can evaluate
whether the trigger later entered and hit TP/SL.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(os.getenv("TRAD_REPO_ROOT") or "/Users/waipop/MainWTN/Hermes/trad")
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from tradingview_mcp.core.services.screener_service import analyze_coin
except Exception:  # pragma: no cover - dry environments
    analyze_coin = None  # type: ignore[assignment]

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from trad_mtf_structure import analyze as mtf_analyze, allow_direction as mtf_allow_direction  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


SCALP_SCHEMA = """
CREATE TABLE IF NOT EXISTS telegram_scalp_watch_alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  direction TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
  fingerprint TEXT NOT NULL,
  target TEXT NOT NULL,
  source_signal_id INTEGER,
  price REAL,
  trigger_level REAL,
  delivered_at TEXT NOT NULL,
  setup_score REAL,
  setup_type TEXT,
  session_label TEXT,
  watch_metadata_json TEXT,
  outcome_id INTEGER,
  UNIQUE(symbol, timeframe, direction, fingerprint, target)
);
CREATE INDEX IF NOT EXISTS idx_scalp_watch_recent
ON telegram_scalp_watch_alerts(symbol, timeframe, direction, delivered_at DESC);

CREATE TABLE IF NOT EXISTS trade_plan_outcomes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_signal_id INTEGER,
  source TEXT NOT NULL DEFAULT 'manual',
  plan_key TEXT UNIQUE,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL DEFAULT '15m',
  direction TEXT NOT NULL CHECK(direction IN ('BUY','SELL')),
  entry_low REAL NOT NULL,
  entry_high REAL NOT NULL,
  sl REAL NOT NULL,
  tp1 REAL,
  tp2 REAL,
  tp3 REAL,
  status TEXT NOT NULL DEFAULT 'pending',
  result TEXT,
  entry_price REAL,
  entered_at TEXT,
  closed_at TEXT,
  current_price REAL,
  max_favorable REAL DEFAULT 0,
  max_adverse REAL DEFAULT 0,
  note TEXT,
  created_at TEXT NOT NULL,
  last_checked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_trade_plan_outcomes_status
ON trade_plan_outcomes(symbol, status, created_at DESC);
"""


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCALP_SCHEMA)
    cols = {r[1] for r in con.execute("PRAGMA table_info(telegram_scalp_watch_alerts)").fetchall()}
    for name, ddl in {
        "setup_score": "REAL",
        "setup_type": "TEXT",
        "session_label": "TEXT",
        "watch_metadata_json": "TEXT",
        "outcome_id": "INTEGER",
    }.items():
        if name not in cols:
            con.execute(f"ALTER TABLE telegram_scalp_watch_alerts ADD COLUMN {name} {ddl}")
    outcome_cols = {r[1] for r in con.execute("PRAGMA table_info(trade_plan_outcomes)").fetchall()}
    for name, ddl in {
        "order_score": "REAL",
        "setup_score": "REAL",
        "setup_type": "TEXT",
        "session_label": "TEXT",
        "order_metadata_json": "TEXT",
        "management_state": "TEXT",
        "managed_sl": "REAL",
        "protected_at": "TEXT",
        "partial_taken_at": "TEXT",
        "partial_price": "REAL",
        "partial_fraction": "REAL",
        "exit_reason": "TEXT",
    }.items():
        if name not in outcome_cols:
            con.execute(f"ALTER TABLE trade_plan_outcomes ADD COLUMN {name} {ddl}")
    return con


def parse_json(v: Any, default: Any) -> Any:
    if not v:
        return default
    try:
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return default


def to_float(v: Any) -> float | None:
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def fmt(n: float | None) -> str:
    return "-" if n is None else f"{float(n):.1f}".rstrip("0").rstrip(".")


def local_session_label(value: Any | None = None) -> str:
    try:
        if value:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = datetime.now(timezone.utc)
        hour_ict = (dt.astimezone(timezone.utc).hour + 7) % 24
    except Exception:
        return "unknown"
    if 6 <= hour_ict < 14:
        return "Asia"
    if 14 <= hour_ict < 19:
        return "London"
    if 19 <= hour_ict < 23:
        return "London/NY overlap"
    return "NY/late"


def classify_watch_type(watch: dict[str, Any]) -> str:
    reason_text = " ".join(map(str, watch.get("reasons") or [])).lower()
    if "reject" in reason_text or "ไส้" in reason_text:
        return "scalp-watch/rejection"
    if "break" in reason_text or "หลุด" in reason_text:
        return "scalp-watch/breakout"
    return "scalp-watch/confirmation"


def latest_signal(con: sqlite3.Connection, symbol: str, timeframe: str) -> sqlite3.Row | None:
    return con.execute(
        """
        SELECT * FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()


def signal_age_seconds(row: sqlite3.Row) -> float | None:
    raw = row["created_at"]
    try:
        created = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - created).total_seconds()
    except Exception:
        return None


def fetch_m5(symbol: str, exchange: str) -> dict[str, Any] | None:
    """Fetch a fresh M5 technical readout.

    Prefer in-process imports when the script runs under the trad uv env. If the
    script is run by the system Python, fall back to the existing uv collector
    and read the compact JSON's technical block.
    """
    if analyze_coin is not None:
        result = analyze_coin(symbol, exchange, "5m")
        if isinstance(result, dict) and not result.get("error"):
            return result
    try:
        proc = subprocess.run(
            [
                "/Users/waipop/.local/bin/uv",
                "run",
                "python",
                "scripts/collect_trad_signal.py",
                "--symbol",
                symbol,
                "--exchange",
                exchange,
                "--timeframe",
                "5m",
                "--json",
            ],
            cwd=str(REPO_ROOT),
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
    except Exception:
        return None
    if proc.returncode != 0 or not proc.stdout.strip():
        return None
    try:
        payload = json.loads(proc.stdout)
    except Exception:
        return None
    if payload.get("error"):
        return None
    technical = payload.get("technical")
    return technical if isinstance(technical, dict) else None


def candle_parts(tech: dict[str, Any]) -> dict[str, float | None]:
    pd = tech.get("price_data") or {}
    o, h, l, c = (to_float(pd.get(k)) for k in ("open", "high", "low", "close"))
    if None in (o, h, l, c):
        return {"open": o, "high": h, "low": l, "close": c, "range": None, "body_ratio": None, "upper_wick": None, "lower_wick": None}
    rng = max(0.01, h - l)  # type: ignore[operator]
    upper = (h - max(o, c)) / rng * 100  # type: ignore[arg-type,operator]
    lower = (min(o, c) - l) / rng * 100  # type: ignore[arg-type,operator]
    body = abs(c - o) / rng  # type: ignore[operator]
    return {"open": o, "high": h, "low": l, "close": c, "range": rng, "body_ratio": body, "upper_wick": upper, "lower_wick": lower}


def htf_data_available(struct: dict[str, Any]) -> bool:
    """Return True only when the dynamic gate has real H1/H4 evidence."""
    if str(struct.get("htf_bias") or "") in {"BULL", "BEAR"}:
        return True
    tfs = struct.get("tfs") if isinstance(struct.get("tfs"), dict) else {}
    for tf in ("1h", "4h"):
        row = tfs.get(tf) if isinstance(tfs.get(tf), dict) else {}
        if any(row.get(k) is not None for k in ("price", "ema20", "ema50", "ema200", "rsi")):
            return True
    return False


def build_watch(row: sqlite3.Row, m5: dict[str, Any]) -> tuple[dict[str, Any] | None, str]:
    decision = str(row["decision"] or "")
    if decision != "WAIT_CONFIRMATION":
        return None, f"งด scalp watch: decision={decision or '-'} ไม่ใช่ WAIT_CONFIRMATION"

    raw_bias = str(row["bias"] or "")
    if raw_bias != "WAIT":
        return None, f"งด scalp watch: bias={raw_bias or '-'} ไม่ใช่ WAIT"

    total_score = int(row["total_score"] or 0)
    if total_score < 40:
        return None, f"งด scalp watch: score {total_score}/100 ต่ำเกินไป"

    price = float(row["price"])
    sd = parse_json(row["sd_range_json"], {})
    t15 = parse_json(row["technical_json"], {})
    m5_parts = candle_parts(m5)
    m15_parts = candle_parts(t15)

    m5_rsi = m5.get("rsi") or {}
    m15_rsi = t15.get("rsi") or {}
    m5_sr = m5.get("support_resistance") or {}
    m15_sr = t15.get("support_resistance") or {}
    m5_ms = m5.get("market_structure") or {}
    m15_ms = t15.get("market_structure") or {}
    m5_sent = m5.get("market_sentiment") or {}
    m15_sent = t15.get("market_sentiment") or {}
    m5_bb = m5.get("bollinger_bands") or {}
    m15_bb = t15.get("bollinger_bands") or {}

    rsi5 = to_float(m5_rsi.get("value"))
    rsi15 = to_float(m15_rsi.get("value"))
    rsi5_dir = str(m5_rsi.get("direction") or "")
    rsi15_dir = str(m15_rsi.get("direction") or "")
    sd1_low = to_float(sd.get("sd1_low"))
    sd1_high = to_float(sd.get("sd1_high"))
    sd2_low = to_float(sd.get("sd2_low"))
    sd2_high = to_float(sd.get("sd2_high"))
    nearest_res = to_float(m15_sr.get("nearest_resistance") or m5_sr.get("nearest_resistance"))
    nearest_sup = to_float(m15_sr.get("nearest_support") or m5_sr.get("nearest_support"))
    bb_upper = to_float(m15_bb.get("upper") or m5_bb.get("upper"))
    bb_lower = to_float(m15_bb.get("lower") or m5_bb.get("lower"))
    m5_high = to_float(m5_parts.get("high"))
    m5_low = to_float(m5_parts.get("low"))
    m5_close = to_float(m5_parts.get("close"))
    m5_open = to_float(m5_parts.get("open"))
    upper_wick = to_float(m5_parts.get("upper_wick")) or 0.0
    lower_wick = to_float(m5_parts.get("lower_wick")) or 0.0

    near_top_refs = [x for x in [sd1_high, nearest_res, bb_upper] if x is not None]
    near_bottom_refs = [x for x in [sd1_low, nearest_sup, bb_lower] if x is not None]
    near_top = bool(near_top_refs and m5_high is not None and min(abs(m5_high - x) for x in near_top_refs) <= 3.0)
    near_bottom = bool(near_bottom_refs and m5_low is not None and min(abs(m5_low - x) for x in near_bottom_refs) <= 3.0)

    bearish_candle = m5_close is not None and m5_open is not None and m5_close < m5_open
    bullish_candle = m5_close is not None and m5_open is not None and m5_close > m5_open
    obv = str((m5.get("obv") or {}).get("direction") or "")
    m5_momentum = str(m5_sent.get("momentum") or "")
    m15_momentum = str(m15_sent.get("momentum") or "")
    m5_trend = str(m5_ms.get("trend") or "")
    m15_trend = str(m15_ms.get("trend") or "")

    sell_score = 0
    sell_reasons: list[str] = []
    if near_top:
        sell_score += 20; sell_reasons.append("ราคา reject ใกล้ SD1/BB/แนวต้านบน")
    if bearish_candle and upper_wick >= 20:
        sell_score += 20; sell_reasons.append(f"M5 แดง + ไส้บน {upper_wick:.0f}%")
    if rsi5 is not None and rsi5 >= 70 and "Fall" in rsi5_dir:
        sell_score += 20; sell_reasons.append(f"RSI M5 {rsi5:.1f} overbought แล้วหักลง")
    if rsi15 is not None and rsi15 >= 70 and "Fall" in rsi15_dir:
        sell_score += 10; sell_reasons.append(f"RSI M15 {rsi15:.1f} เริ่มลง")
    if obv == "distribution" or "Bear" in m5_momentum or "Bear" in m15_momentum:
        sell_score += 10; sell_reasons.append("มีแรง distribution/momentum bearish สั้น")

    buy_score = 0
    buy_reasons: list[str] = []
    if near_bottom:
        buy_score += 20; buy_reasons.append("ราคา reject ใกล้ SD1/BB/แนวรับล่าง")
    if bullish_candle and lower_wick >= 20:
        buy_score += 20; buy_reasons.append(f"M5 เขียว + ไส้ล่าง {lower_wick:.0f}%")
    if rsi5 is not None and rsi5 <= 45 and "Ris" in rsi5_dir:
        buy_score += 20; buy_reasons.append(f"RSI M5 {rsi5:.1f} ฟื้นจากโซนล่าง")
    if "Bull" in m5_trend and "Bull" in m15_trend:
        buy_score += 10; buy_reasons.append("โครงสร้าง M5/M15 ยัง bullish")
    if rsi15 is not None and rsi15 < 72:
        buy_score += 10; buy_reasons.append("RSI M15 ไม่ร้อนเกินไปสำหรับ pullback BUY")

    if sell_score >= 50 and sell_score >= buy_score + 10:
        # Dynamic higher-timeframe trend filter: if H1/H4 is bullish, a SELL scalp
        # is against the trend, so require a stronger rejection score (>=75).
        try:
            struct = mtf_analyze(str(row["symbol"] or "XAUUSD"), "OANDA")
            if not htf_data_available(struct):
                return None, "งด scalp SELL: ข้อมูล HTF ไม่พร้อม ไม่เปิดไม้โดยเดาเทรน"
            htf_bias = struct.get("htf_bias", "NEUTRAL")
        except Exception:
            return None, "งด scalp SELL: ดึงข้อมูล HTF ไม่สำเร็จ ไม่เปิดไม้โดยเดาเทรน"
        if htf_bias == "BULL" and sell_score < 75:
            return None, f"งด scalp SELL: เทรน HTF เป็น BULL (score {sell_score}/100 < 75 สวนเทรน)"
        if htf_bias == "BEAR" and sell_score < 75:
            pass  # SELL with the trend, keep base gate.
        trigger = min(x for x in [m5_low, m5_close, price] if x is not None)
        sl = (m5_high or price) + 3.0
        # cap SL to about 800 points from trigger
        sl = min(sl, trigger + 8.0)
        return {
            "direction": "SELL",
            "score": min(100, sell_score),
            "price": price,
            "trigger": trigger,
            "entry_text": f"รอ M5 ปิด/ยืนใต้ {fmt(trigger)} หรือหลุดต่ำกว่า low ล่าสุด",
            "sl": sl,
            "tp1": sd1_low or (price - 8),
            "tp2": sd2_low or (price - 16),
            "invalid": f"M5 กลับไปปิดเหนือ {fmt(m5_high)}",
            "reasons": sell_reasons,
            "m5_rsi": rsi5,
            "m15_rsi": rsi15,
            "source_signal_id": int(row["id"]),
            "total_score": total_score,
            "regime": row["regime"],
            "setup_type": "scalp-watch/rejection",
            "session_label": local_session_label(row["created_at"] if "created_at" in row.keys() else None),
        }, ""

    if buy_score >= 50 and buy_score >= sell_score + 10:
        # Dynamic higher-timeframe trend filter: if H1/H4 is bearish, a BUY scalp
        # is against the trend, so require a stronger rejection score (>=75).
        try:
            struct = mtf_analyze(str(row["symbol"] or "XAUUSD"), "OANDA")
            if not htf_data_available(struct):
                return None, "งด scalp BUY: ข้อมูล HTF ไม่พร้อม ไม่เปิดไม้โดยเดาเทรน"
            htf_bias = struct.get("htf_bias", "NEUTRAL")
        except Exception:
            return None, "งด scalp BUY: ดึงข้อมูล HTF ไม่สำเร็จ ไม่เปิดไม้โดยเดาเทรน"
        if htf_bias == "BEAR" and buy_score < 75:
            return None, f"งด scalp BUY: เทรน HTF เป็น BEAR (score {buy_score}/100 < 75 สวนเทรน)"
        if htf_bias == "BULL" and buy_score < 75:
            pass  # BUY with the trend, keep base gate.
        trigger = max(x for x in [m5_high, m5_close, price] if x is not None)
        sl = (m5_low or price) - 3.0
        sl = max(sl, trigger - 8.0)
        return {
            "direction": "BUY",
            "score": min(100, buy_score),
            "price": price,
            "trigger": trigger,
            "entry_text": f"รอ M5 ปิด/ยืนเหนือ {fmt(trigger)} หลัง reject",
            "sl": sl,
            "tp1": sd1_high or (price + 8),
            "tp2": sd2_high or (price + 16),
            "invalid": f"M5 หลุดกลับใต้ {fmt(m5_low)}",
            "reasons": buy_reasons,
            "m5_rsi": rsi5,
            "m15_rsi": rsi15,
            "source_signal_id": int(row["id"]),
            "total_score": total_score,
            "regime": row["regime"],
            "setup_type": "scalp-watch/rejection",
            "session_label": local_session_label(row["created_at"] if "created_at" in row.keys() else None),
        }, ""

    return None, f"งด scalp watch: reject ยังไม่ชัดพอ SELL {sell_score}/100 BUY {buy_score}/100"


def fingerprint(symbol: str, timeframe: str, watch: dict[str, Any]) -> str:
    # Bucket by $3 trigger zones + source signal group to avoid repeated spam while still alerting fresh structures.
    bucket = int(float(watch["trigger"]) // 3)
    return f"{symbol}:{timeframe}:{watch['direction']}:{bucket}:{int(watch['source_signal_id']) // 3}"


def recent_sent_reason(con: sqlite3.Connection, symbol: str, timeframe: str, direction: str, target: str, minutes: int) -> str | None:
    row = con.execute(
        """
        SELECT id, trigger_level, delivered_at FROM telegram_scalp_watch_alerts
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND direction=? AND target=?
        ORDER BY delivered_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe, direction, target),
    ).fetchone()
    if row is None:
        return None
    try:
        t = datetime.fromisoformat(str(row["delivered_at"]).replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        elapsed = (datetime.now(timezone.utc) - t).total_seconds() / 60
    except Exception:
        elapsed = 0
    if elapsed < minutes:
        return f"งด scalp watch ซ้ำ: เพิ่งส่ง {direction} Watch #{row['id']} เมื่อ {elapsed:.0f} นาทีที่แล้ว"
    return None


def already_sent(con: sqlite3.Connection, symbol: str, timeframe: str, direction: str, fp: str, target: str) -> bool:
    return con.execute(
        "SELECT 1 FROM telegram_scalp_watch_alerts WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND direction=? AND fingerprint=? AND target=? LIMIT 1",
        (symbol, timeframe, direction, fp, target),
    ).fetchone() is not None


def recent_scalp_zone_reason(con: sqlite3.Connection, symbol: str, timeframe: str, watch: dict[str, Any]) -> str | None:
    """Block repeated scalp-watch triggers in the same zone after non-TP results.

    Approved after Scalp #39/#40 reached PARTIAL_BE and a later same-zone #41
    CUT. Scalp Watch is allowed to be more permissive than full orders, but it
    should not keep re-selling/re-buying the same trigger band unless the new
    setup is materially stronger.
    """
    if not table_exists(con, "trade_plan_outcomes"):
        return None
    direction = str(watch["direction"])
    trigger = float(watch["trigger"])
    score = int(watch.get("score") or 0)
    rows = con.execute(
        """
        SELECT id, source, direction, entry_low, entry_high, status, result, created_at, closed_at, setup_score
        FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND direction=?
          AND source='telegram_scalp_watch'
        ORDER BY id DESC LIMIT 12
        """,
        (symbol, timeframe, direction),
    ).fetchall()
    now = datetime.now(timezone.utc)
    same_zone_recent: list[sqlite3.Row] = []
    for row in rows:
        raw_time = row["closed_at"] or row["created_at"]
        try:
            t = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        age_min = (now - t).total_seconds() / 60
        if age_min > 90:
            continue
        center = (float(row["entry_low"]) + float(row["entry_high"])) / 2
        if abs(center - trigger) <= 5.0:
            same_zone_recent.append(row)

    if not same_zone_recent:
        return None

    open_same = [r for r in same_zone_recent if str(r["status"]) in {"pending", "entered"}]
    if open_same:
        ids = ",".join(f"#{r['id']}" for r in open_same[:3])
        return f"งด scalp watch ซ้ำ: ยังมี scalp {direction} โซนเดียวกันเปิดอยู่ ({ids})"

    non_tp = [r for r in same_zone_recent if not str(r["result"] or "").startswith("TP")]
    last = same_zone_recent[0]
    last_result = str(last["result"] or "-")

    if last_result in {"CUT", "SL"} and score < 75:
        return f"งด scalp watch {direction}: โซนเดิมเพิ่ง {last_result} จาก Scalp #{last['id']} ต้องรอ setup score >=75 ตอนนี้ {score}/100"
    if len(non_tp) >= 2 and score < 70:
        ids = ",".join(f"#{r['id']}:{r['result'] or r['status']}" for r in non_tp[:3])
        return f"งด scalp watch {direction}: โซนเดิมมี non-TP ซ้ำใน 90 นาที ({ids}) ต้องรอ score >=70 ตอนนี้ {score}/100"
    if last_result in {"BE", "PARTIAL_BE"} and score < 65:
        return f"งด scalp watch {direction}: โซนเดิมเพิ่ง {last_result} จาก Scalp #{last['id']} รอ setup ใหม่แข็งกว่า score >=65 ตอนนี้ {score}/100"
    return None


def table_exists(con: sqlite3.Connection, name: str) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def message_for_watch(watch: dict[str, Any], watch_id: int) -> str:
    reasons = "; ".join(watch["reasons"][:3])
    return "\n".join([
        f"Scalp Watch #{watch_id} | XAUUSD {fmt(watch['price'])}",
        f"Direction: {watch['direction']} | Score: {int(watch['score'])}/100",
        "สถานะ: ยังไม่ใช่ Order หลัก — รอ trigger ก่อนเข้า",
        "",
        f"Trigger: {watch['entry_text']}",
        f"SL: {fmt(watch['sl'])}",
        f"TP: {fmt(watch['tp1'])} / {fmt(watch['tp2'])}",
        f"CUT/Invalid: {watch['invalid']}",
        "",
        f"RSI M5/M15: {fmt(watch.get('m5_rsi'))} / {fmt(watch.get('m15_rsi'))}",
        f"Reason: {reasons}",
        f"Engine: WAIT_CONFIRMATION score {int(watch['total_score'])}/100 ({watch.get('regime') or '-'})",
    ])


def ensure_outcome(con: sqlite3.Connection, symbol: str, timeframe: str, watch: dict[str, Any], fp: str) -> int:
    """Persist the scalp trigger as a trackable outcome row.

    Entry is represented as a zero-width trigger zone. The shared outcome tracker
    marks it entered when price crosses the trigger, then closes at TP/SL.
    """
    metadata = {
        "phase": "1B-scalp-tracking",
        "watch_fingerprint": fp,
        "trigger_level": watch.get("trigger"),
        "entry_text": watch.get("entry_text"),
        "invalid": watch.get("invalid"),
        "m5_rsi": watch.get("m5_rsi"),
        "m15_rsi": watch.get("m15_rsi"),
        "regime": watch.get("regime"),
        "reasons": watch.get("reasons"),
        "total_signal_score": watch.get("total_score"),
    }
    setup_type = watch.get("setup_type") or classify_watch_type(watch)
    plan_key = f"scalp_watch:{fp}"
    created_at = utc_now()
    con.execute(
        """
        INSERT OR IGNORE INTO trade_plan_outcomes
        (source_signal_id, source, plan_key, symbol, timeframe, direction,
         entry_low, entry_high, sl, tp1, tp2, tp3, note, created_at,
         order_score, setup_score, setup_type, session_label, order_metadata_json)
        VALUES (?, 'telegram_scalp_watch', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            watch.get("source_signal_id"),
            plan_key,
            symbol.upper(),
            timeframe,
            watch["direction"],
            float(watch["trigger"]),
            float(watch["trigger"]),
            watch.get("sl"),
            watch.get("tp1"),
            watch.get("tp2"),
            None,
            f"Scalp Watch trigger at {fmt(watch.get('trigger'))}; not full Order entry",
            created_at,
            None,
            watch.get("score"),
            setup_type,
            watch.get("session_label") or local_session_label(),
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ),
    )
    row = con.execute("SELECT id FROM trade_plan_outcomes WHERE plan_key=?", (plan_key,)).fetchone()
    return int(row["id"])


def mark_sent(con: sqlite3.Connection, symbol: str, timeframe: str, watch: dict[str, Any], fp: str, target: str) -> tuple[int, int]:
    metadata = {
        "phase": "1B-scalp-tracking",
        "m5_rsi": watch.get("m5_rsi"),
        "m15_rsi": watch.get("m15_rsi"),
        "regime": watch.get("regime"),
        "reasons": watch.get("reasons"),
        "total_signal_score": watch.get("total_score"),
    }
    setup_type = watch.get("setup_type") or classify_watch_type(watch)
    outcome_id = ensure_outcome(con, symbol, timeframe, watch, fp)
    con.execute(
        """
        INSERT OR IGNORE INTO telegram_scalp_watch_alerts
        (symbol, timeframe, direction, fingerprint, target, source_signal_id, price, trigger_level, delivered_at,
         setup_score, setup_type, session_label, watch_metadata_json, outcome_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            symbol,
            timeframe,
            watch["direction"],
            fp,
            target,
            watch["source_signal_id"],
            watch["price"],
            watch["trigger"],
            utc_now(),
            watch.get("score"),
            setup_type,
            watch.get("session_label") or local_session_label(),
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            outcome_id,
        ),
    )
    row = con.execute(
        "SELECT id, outcome_id FROM telegram_scalp_watch_alerts WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND direction=? AND fingerprint=? AND target=?",
        (symbol, timeframe, watch["direction"], fp, target),
    ).fetchone()
    return int(row["id"]), int(row["outcome_id"] or outcome_id)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET") or "telegram:8237892676")
    p.add_argument("--max-age-seconds", type=int, default=420)
    p.add_argument("--cooldown-minutes", type=int, default=15)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args(argv)

    with connect(Path(args.db_path).expanduser()) as con:
        row = latest_signal(con, args.symbol, args.timeframe)
        if row is None or row["price"] is None:
            if args.dry_run:
                print("งด scalp watch: ไม่มี latest signal")
            return 0
        age = signal_age_seconds(row)
        if age is not None and age > args.max_age_seconds:
            if args.dry_run:
                print(f"งด scalp watch: signal stale {age:.0f}s")
            return 0
        m5 = fetch_m5(args.symbol, args.exchange)
        if not m5:
            if args.dry_run:
                print("งด scalp watch: ดึง M5 ไม่สำเร็จ/TradingView upstream ว่าง")
            return 0
        watch, reason = build_watch(row, m5)
        if watch is None:
            if args.dry_run:
                print(reason)
            return 0
        fp = fingerprint(args.symbol, args.timeframe, watch)
        if not args.force:
            reason = recent_sent_reason(con, args.symbol, args.timeframe, watch["direction"], args.target, args.cooldown_minutes)
            if reason:
                if args.dry_run:
                    print(reason)
                return 0
            reason = recent_scalp_zone_reason(con, args.symbol, args.timeframe, watch)
            if reason:
                if args.dry_run:
                    print(reason)
                return 0
            if already_sent(con, args.symbol, args.timeframe, watch["direction"], fp, args.target):
                if args.dry_run:
                    print("งด scalp watch ซ้ำ: fingerprint เดิมส่งแล้ว")
                return 0
        preview_id = con.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM telegram_scalp_watch_alerts").fetchone()[0]
        if args.dry_run:
            print(message_for_watch(watch, int(preview_id)))
            return 0
        watch_id, outcome_id = mark_sent(con, args.symbol, args.timeframe, watch, fp, args.target)
        message = message_for_watch(watch, watch_id) + f"\nTrack: Outcome #{outcome_id}"
        sent = subprocess.run(
            ["hermes", "send", "--quiet", "--to", args.target, "--subject", f"XAUUSD Scalp Watch #{watch_id}", message],
            text=True,
            capture_output=True,
            check=False,
        )
        if sent.returncode != 0:
            print(sent.stderr.strip() or sent.stdout.strip(), flush=True)
            return sent.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
