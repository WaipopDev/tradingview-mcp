from __future__ import annotations

from tradingview_mcp.core.storage.database import initialize_database
from tradingview_mcp.core.storage.repositories import SignalAiResponseRepository, TradeSignalRepository


def _signal(score: int = 74) -> dict:
    return {
        "symbol": "XAUUSD",
        "exchange": "OANDA",
        "instrument": "OANDA:XAUUSD",
        "timeframe": "15m",
        "price": 4078.2,
        "bias": "SELL",
        "decision": "TRADE",
        "score": score,
        "regime": "trend_momentum",
        "score_breakdown": {"mtf_alignment": 25, "oi_volume_proxy": 10},
        "oi_proxy": {"label": "intraday_proxy", "real_open_interest_available": False},
        "plan": {"entry_zone": "4088-4093", "sl": 4102, "tp": [4075, 4062, 4050]},
    }


def test_signal_ai_response_cache_reuses_response_for_same_signal_fingerprint(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = SignalAiResponseRepository(db_path)
    signal = _signal()
    fingerprint = repo.fingerprint_signal(signal)

    repo.insert_ai_response(
        symbol="XAUUSD",
        timeframe="15m",
        signal_fingerprint=fingerprint,
        ai_response="SELL 4088-4093 SL 4102 TP 4075/4062/4050",
        source="telegram",
    )

    gate = repo.build_ai_gate(signal)

    assert gate["should_ask_ai"] is False
    assert gate["reason"] == "CACHED_AI_RESPONSE_REUSABLE"
    assert gate["signal_fingerprint"] == fingerprint
    assert gate["cached_response"] == "SELL 4088-4093 SL 4102 TP 4075/4062/4050"


def test_signal_alert_delivery_marker_prevents_duplicate_alerts(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = SignalAiResponseRepository(db_path)
    fingerprint = repo.fingerprint_signal(_signal())

    assert repo.has_alert_delivery("XAUUSD", "15m", fingerprint, "telegram:trad") is False

    first_id = repo.mark_alert_delivered("XAUUSD", "15m", fingerprint, "telegram:trad")
    second_id = repo.mark_alert_delivered("XAUUSD", "15m", fingerprint, "telegram:trad")

    assert first_id == second_id
    assert repo.has_alert_delivery("XAUUSD", "15m", fingerprint, "telegram:trad") is True
    assert repo.has_alert_delivery("XAUUSD", "15m", fingerprint, "telegram:other") is False


def test_signal_ai_response_cache_reuses_legacy_fingerprint_for_backward_compatibility(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = SignalAiResponseRepository(db_path)
    signal = _signal()
    legacy_fingerprint = repo.legacy_fingerprint_signal(signal)

    repo.insert_ai_response(
        symbol="XAUUSD",
        timeframe="15m",
        signal_fingerprint=legacy_fingerprint,
        ai_response="legacy cached response",
        source="telegram",
    )

    gate = repo.build_ai_gate(signal)

    assert gate["should_ask_ai"] is False
    assert gate["signal_fingerprint"] == repo.fingerprint_signal(signal)
    assert gate["cache_fingerprint"] == legacy_fingerprint
    assert gate["cached_response"] == "legacy cached response"


def test_signal_ai_gate_requests_ai_only_for_trade_without_cached_response(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = SignalAiResponseRepository(db_path)

    trade_gate = repo.build_ai_gate(_signal())
    wait_gate = repo.build_ai_gate({**_signal(score=45), "bias": "WAIT", "decision": "WAIT_CONFIRMATION", "plan": {"entry_zone": None, "sl": None, "tp": []}})

    assert trade_gate["should_ask_ai"] is True
    assert trade_gate["reason"] == "TRADE_SIGNAL_NEEDS_AI_SUMMARY"
    assert wait_gate["should_ask_ai"] is False
    assert wait_gate["reason"] == "NO_TRADE_CONDITION"


def test_signal_fingerprint_tracks_instrument_score_breakdown_and_oi_proxy_labels(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    repo = SignalAiResponseRepository(db_path)
    base = _signal()

    base_fingerprint = repo.fingerprint_signal(base)

    assert repo.fingerprint_signal({**base, "instrument": "FX_IDC:XAUUSD"}) != base_fingerprint
    assert repo.fingerprint_signal({**base, "score_breakdown": {"mtf_alignment": 12}}) != base_fingerprint
    assert repo.fingerprint_signal({**base, "oi_proxy": {"label": "real_oi", "real_open_interest_available": True}}) != base_fingerprint


def test_trade_signal_compact_payload_includes_ai_gate_when_saved(tmp_path):
    db_path = tmp_path / "signals.sqlite3"
    initialize_database(db_path)
    trade_repo = TradeSignalRepository(db_path)
    ai_repo = SignalAiResponseRepository(db_path)
    signal = _signal()
    gate = ai_repo.build_ai_gate(signal)

    trade_repo.insert_trade_signal(
        {
            "symbol": "XAUUSD",
            "exchange": "OANDA",
            "timeframe": "15m",
            "price": signal["price"],
            "bias": signal["bias"],
            "decision": signal["decision"],
            "entry_low": 4088,
            "entry_high": 4093,
            "sl": 4102,
            "tp1": 4075,
            "total_score": signal["score"],
            "ai_gate_json": gate,
        }
    )

    latest = trade_repo.get_latest_trade_signal("XAUUSD", "15m")

    assert latest is not None
    assert latest["ai_gate"]["should_ask_ai"] is True
    assert latest["ai_gate"]["signal_fingerprint"] == gate["signal_fingerprint"]
