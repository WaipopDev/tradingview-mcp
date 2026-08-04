"""AI alert helpers for trade signals that pass the deterministic gate."""
from __future__ import annotations

import json
from typing import Any, Mapping


def should_ask_ai_for_signal(signal: Mapping[str, Any] | None) -> bool:
    if not signal:
        return False
    gate = signal.get("ai_gate") or {}
    if not isinstance(gate, Mapping):
        return False
    return bool(gate.get("should_ask_ai")) and not bool(gate.get("cached_response"))


def build_ai_prompt(signal: Mapping[str, Any]) -> str:
    symbol = str(signal.get("symbol") or "XAUUSD").upper()
    exchange = str(signal.get("exchange") or "OANDA").upper()
    timeframe = str(signal.get("timeframe") or "15m")
    gate = signal.get("ai_gate") or {}
    fingerprint = gate.get("signal_fingerprint") if isinstance(gate, Mapping) else None
    compact_json = json.dumps(signal, ensure_ascii=False, sort_keys=True, default=str)
    return f"""You are Waipop's XAUUSD trading assistant for Telegram.

Use only the compact signal JSON below. Do not call tools, do not fetch TradingView/raw market data, and do not infer raw market data that is not present in the JSON.
Respond in concise Thai, maximum 6 lines, but keep trading actions as BUY/SELL only; do not use Long/Short.
Your answer must include: Instrument, Current price, Bias, Entry, SL, TP1/TP2/TP3, Decision, and Reason. Do not include disclaimers.
If the plan has an entry_zone, present it as an actionable entry alert immediately.
Append this fingerprint at the end: {fingerprint}

Instrument: {exchange}:{symbol}
Timeframe: {timeframe}
Signal JSON:
{compact_json}
"""


def build_telegram_subject(signal: Mapping[str, Any]) -> str:
    bias = str(signal.get("bias") or "WAIT").upper()
    score = signal.get("score")
    symbol = str(signal.get("symbol") or "XAUUSD").upper()
    return f"[Trad Alert] {symbol} {bias} score={score}"
