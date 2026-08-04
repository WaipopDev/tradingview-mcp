"""Persist compact trade-signal summaries into the local SQLite cache."""
from __future__ import annotations

import json
from typing import Any, Mapping

from tradingview_mcp.core.storage.database import PathLike
from tradingview_mcp.core.storage.repositories import TradeSignalRepository


def _json_dump(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def _parse_entry_zone(value: Any) -> tuple[float | None, float | None]:
    if value is None:
        return None, None
    if isinstance(value, (int, float)):
        numeric = float(value)
        return numeric, numeric
    text = str(value).strip()
    if not text:
        return None, None
    for separator in ("-", "–", "—"):
        if separator in text:
            left, right = text.split(separator, 1)
            try:
                return float(left.strip()), float(right.strip())
            except ValueError:
                return None, None
    try:
        numeric = float(text)
        return numeric, numeric
    except ValueError:
        return None, None


def store_compact_trade_signal(summary: Mapping[str, Any], db_path: PathLike | None = None) -> dict[str, Any]:
    """Store an AI/dashboard-ready compact signal and return the inserted latest row.

    This is a Phase-1 bridge: later collectors/signal engines can call this with
    deterministic computed summaries, while tests and manual jobs can seed the DB
    without involving the LLM or raw TradingView output.
    """
    plan = summary.get("plan") or {}
    tp_values = list(plan.get("tp") or []) if isinstance(plan, Mapping) else []
    entry_low, entry_high = _parse_entry_zone(plan.get("entry_zone") if isinstance(plan, Mapping) else None)

    record = {
        "symbol": str(summary.get("symbol") or "XAUUSD").upper(),
        "exchange": summary.get("exchange") or "OANDA",
        "instrument": summary.get("instrument") or f"{summary.get('exchange') or 'OANDA'}:{summary.get('symbol') or 'XAUUSD'}",
        "timeframe": summary.get("timeframe") or "15m",
        "price": summary.get("price"),
        "bias": str(summary.get("bias") or "WAIT").upper(),
        "decision": summary.get("decision") or "WAIT_CONFIRMATION",
        "entry_low": entry_low,
        "entry_high": entry_high,
        "sl": plan.get("sl") if isinstance(plan, Mapping) else None,
        "tp1": tp_values[0] if len(tp_values) > 0 else None,
        "tp2": tp_values[1] if len(tp_values) > 1 else None,
        "tp3": tp_values[2] if len(tp_values) > 2 else None,
        "confidence": summary.get("confidence"),
        "total_score": summary.get("score") or summary.get("total_score"),
        "regime": summary.get("regime"),
        "sd_range_json": _json_dump(summary.get("sd_range")),
        "oi_proxy_json": _json_dump(summary.get("oi_proxy")),
        "volume_json": _json_dump(summary.get("volume")),
        "technical_json": _json_dump(summary.get("technical")),
        "levels_json": _json_dump(summary.get("levels")),
        "score_breakdown_json": _json_dump(summary.get("score_breakdown")),
        "reason_codes_json": _json_dump(summary.get("reason_codes")),
        "ai_gate_json": _json_dump(summary.get("ai_gate")),
        "created_at": summary.get("created_at"),
    }

    repo = TradeSignalRepository(db_path)
    inserted_id = repo.insert_trade_signal(record)
    latest = repo.get_latest_trade_signal(record["symbol"], timeframe=record["timeframe"])
    return {"id": inserted_id, "latest": latest}
