from __future__ import annotations

from tradingview_mcp.core.jobs.ai_signal_alert import build_ai_prompt, should_ask_ai_for_signal


def _trade_signal() -> dict:
    return {
        "symbol": "XAUUSD",
        "exchange": "OANDA",
        "timeframe": "15m",
        "price": 4078.2,
        "bias": "SELL",
        "decision": "TRADE",
        "score": 74,
        "regime": "trend_momentum",
        "plan": {"entry_zone": "4088-4093", "sl": 4102, "tp": [4075, 4062, 4050]},
        "ai_gate": {"should_ask_ai": True, "signal_fingerprint": "fp123", "cached_response": None},
    }


def test_should_ask_ai_for_signal_only_when_gate_true_without_cache():
    assert should_ask_ai_for_signal(_trade_signal()) is True
    assert should_ask_ai_for_signal({**_trade_signal(), "ai_gate": {"should_ask_ai": False}}) is False
    assert should_ask_ai_for_signal({**_trade_signal(), "ai_gate": {"should_ask_ai": True, "cached_response": "old"}}) is False


def test_build_ai_prompt_is_english_but_requests_concise_thai_answer():
    prompt = build_ai_prompt(_trade_signal())

    assert "OANDA:XAUUSD" in prompt
    assert "SELL" in prompt
    assert "4088-4093" in prompt
    assert "Do not fetch additional data" in prompt
    assert "Respond in concise Thai" in prompt
    assert "ห้ามดึงข้อมูลเพิ่ม" not in prompt
    assert "fp123" in prompt
