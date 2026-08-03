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
    return f"""คุณคือผู้ช่วยเทรด XAUUSD สำหรับ Telegram ของ Waipop

ใช้เฉพาะ compact signal JSON ด้านล่างเท่านั้น ห้ามดึงข้อมูลเพิ่ม ห้ามเดา raw data เพิ่ม
ตอบเป็นภาษาไทยสั้น กระชับ ใช้ BUY/SELL เท่านั้น ไม่ใช้ Long/Short
ต้องมี: Instrument, Current price, Bias, Entry, SL, TP1/TP2/TP3, Decision, Reason
ถ้า plan มี entry_zone ให้แจ้งเป็นจุดเข้า actionable ทันที
ท้ายข้อความใส่ fingerprint: {fingerprint}

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
