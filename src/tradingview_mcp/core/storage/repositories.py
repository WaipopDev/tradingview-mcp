"""Repository helpers that return compact JSON-ready trading payloads."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from tradingview_mcp.core.storage.database import PathLike, connect_database, initialize_database


_JSON_FIELDS = {
    "sd_range_json": "sd_range",
    "oi_proxy_json": "oi_proxy",
    "volume_json": "volume",
    "levels_json": "levels",
    "reason_codes_json": "reason_codes",
    "ai_gate_json": "ai_gate",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_json(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _format_entry_zone(row: Mapping[str, Any]) -> str | None:
    low = row.get("entry_low")
    high = row.get("entry_high")
    if low is None and high is None:
        return None
    if low is None:
        return f"{high:g}"
    if high is None:
        return f"{low:g}"
    if float(low) == float(high):
        return f"{float(low):g}"
    return f"{float(low):g}-{float(high):g}"


def _compact_trade_signal(row: Mapping[str, Any]) -> dict[str, Any]:
    created_at = row.get("created_at")
    created_dt = _parse_dt(str(created_at) if created_at is not None else None)
    age = 0 if created_dt is None else max(0, int((_utc_now() - created_dt).total_seconds()))

    result: dict[str, Any] = {
        "symbol": row.get("symbol"),
        "exchange": row.get("exchange") or "OANDA",
        "timeframe": row.get("timeframe") or "15m",
        "price": row.get("price"),
        "data_age_seconds": age,
        "bias": row.get("bias"),
        "decision": row.get("decision"),
        "score": row.get("total_score"),
        "confidence": row.get("confidence"),
        "regime": row.get("regime"),
        "created_at": created_at,
    }

    for db_key, api_key in _JSON_FIELDS.items():
        default = [] if api_key == "reason_codes" else {}
        result[api_key] = _parse_json(row.get(db_key), default)

    tps = [row.get("tp1"), row.get("tp2"), row.get("tp3")]
    result["plan"] = {
        "entry_zone": _format_entry_zone(row),
        "sl": row.get("sl"),
        "tp": [tp for tp in tps if tp is not None],
    }
    return result


class TradeSignalRepository:
    """SQLite repository for compact trade signals."""

    def __init__(self, db_path: PathLike | None = None):
        self.db_path = Path(db_path).expanduser() if db_path is not None else initialize_database()
        initialize_database(self.db_path)

    def insert_trade_signal(self, signal: Mapping[str, Any]) -> int:
        fields = [
            "symbol", "exchange", "timeframe", "price", "bias", "decision",
            "entry_low", "entry_high", "sl", "tp1", "tp2", "tp3",
            "confidence", "total_score", "regime", "sd_range_json", "oi_proxy_json",
            "volume_json", "levels_json", "reason_codes_json", "ai_gate_json",
            "source_score_id", "status", "created_at",
        ]
        values = dict(signal)
        values.setdefault("exchange", "OANDA")
        values.setdefault("timeframe", "15m")
        values.setdefault("status", "active")
        for json_field in _JSON_FIELDS:
            if isinstance(values.get(json_field), (dict, list)):
                values[json_field] = json.dumps(values[json_field], ensure_ascii=False)
        if not values.get("created_at"):
            values["created_at"] = _utc_now().isoformat()
        placeholders = ", ".join([":" + field for field in fields])
        columns = ", ".join(fields)
        with connect_database(self.db_path) as conn:
            cursor = conn.execute(
                f"INSERT INTO trade_signals ({columns}) VALUES ({placeholders})",
                {field: values.get(field) for field in fields},
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a row id for inserted trade signal")
            return int(cursor.lastrowid)

    def get_latest_trade_signal(self, symbol: str, timeframe: str | None = None) -> dict[str, Any] | None:
        sql = "SELECT * FROM trade_signals WHERE UPPER(symbol) = UPPER(?) AND status = 'active'"
        params: list[Any] = [symbol]
        if timeframe:
            sql += " AND timeframe = ?"
            params.append(timeframe)
        sql += " ORDER BY created_at DESC, id DESC LIMIT 1"
        with connect_database(self.db_path) as conn:
            row = conn.execute(sql, params).fetchone()
        if row is None:
            return None
        return _compact_trade_signal(dict(row))


class SignalAiResponseRepository:
    """Cache AI summaries by deterministic signal fingerprint."""

    def __init__(self, db_path: PathLike | None = None):
        self.db_path = Path(db_path).expanduser() if db_path is not None else initialize_database()
        initialize_database(self.db_path)

    def fingerprint_signal(self, signal: Mapping[str, Any]) -> str:
        plan = signal.get("plan") or {}
        payload = {
            "symbol": signal.get("symbol"),
            "timeframe": signal.get("timeframe"),
            "bias": signal.get("bias"),
            "decision": signal.get("decision"),
            "score": signal.get("score") or signal.get("total_score"),
            "regime": signal.get("regime"),
            "entry_zone": plan.get("entry_zone") if isinstance(plan, Mapping) else None,
            "sl": plan.get("sl") if isinstance(plan, Mapping) else None,
            "tp": plan.get("tp") if isinstance(plan, Mapping) else None,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]

    def insert_ai_response(
        self,
        symbol: str,
        timeframe: str,
        signal_fingerprint: str,
        ai_response: str,
        source: str = "telegram",
        expires_at: str | None = None,
    ) -> int:
        now = _utc_now().isoformat()
        with connect_database(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO ai_signal_responses
                (symbol, timeframe, signal_fingerprint, ai_response, source, created_at, last_used_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, timeframe, signal_fingerprint) DO UPDATE SET
                    ai_response=excluded.ai_response,
                    source=excluded.source,
                    last_used_at=excluded.last_used_at,
                    expires_at=excluded.expires_at
                """,
                (symbol.upper(), timeframe, signal_fingerprint, ai_response, source, now, now, expires_at),
            )
            row = conn.execute(
                "SELECT id FROM ai_signal_responses WHERE symbol=? AND timeframe=? AND signal_fingerprint=?",
                (symbol.upper(), timeframe, signal_fingerprint),
            ).fetchone()
        return int(row[0])

    def get_cached_response(self, symbol: str, timeframe: str, signal_fingerprint: str) -> str | None:
        now = _utc_now().isoformat()
        with connect_database(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT ai_response FROM ai_signal_responses
                WHERE symbol=? AND timeframe=? AND signal_fingerprint=?
                  AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY created_at DESC LIMIT 1
                """,
                (symbol.upper(), timeframe, signal_fingerprint, now),
            ).fetchone()
            if row is not None:
                conn.execute(
                    "UPDATE ai_signal_responses SET last_used_at=? WHERE symbol=? AND timeframe=? AND signal_fingerprint=?",
                    (now, symbol.upper(), timeframe, signal_fingerprint),
                )
        return None if row is None else str(row[0])

    def build_ai_gate(self, signal: Mapping[str, Any]) -> dict[str, Any]:
        symbol = str(signal.get("symbol") or "XAUUSD").upper()
        timeframe = str(signal.get("timeframe") or "15m")
        fingerprint = self.fingerprint_signal(signal)
        cached = self.get_cached_response(symbol, timeframe, fingerprint)
        if cached:
            return {
                "should_ask_ai": False,
                "reason": "CACHED_AI_RESPONSE_REUSABLE",
                "signal_fingerprint": fingerprint,
                "cached_response": cached,
            }

        plan = signal.get("plan") or {}
        should = (
            str(signal.get("decision")) == "TRADE"
            and str(signal.get("bias")) in {"BUY", "SELL"}
            and bool(plan.get("entry_zone") if isinstance(plan, Mapping) else None)
            and int(signal.get("score") or signal.get("total_score") or 0) >= 70
        )
        return {
            "should_ask_ai": bool(should),
            "reason": "TRADE_SIGNAL_NEEDS_AI_SUMMARY" if should else "NO_TRADE_CONDITION",
            "signal_fingerprint": fingerprint,
            "cached_response": None,
        }
