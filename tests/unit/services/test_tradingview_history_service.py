from __future__ import annotations

import json

from tradingview_mcp.core.services.tradingview_history_service import (
    _candles_from_series_payload,
    _parse_tv_messages,
    _tv_frame,
    ensure_history_schema,
    store_historical_candles,
)


def test_parse_tv_messages_extracts_framed_json():
    payload = {"m": "timescale_update", "p": ["cs", {"s1": {"s": []}}]}
    framed = _tv_frame(payload)

    assert _parse_tv_messages(framed) == [payload]


def test_candles_from_series_payload_and_store(tmp_path):
    payload = {
        "m": "timescale_update",
        "p": [
            "cs_test",
            {
                "s1": {
                    "s": [
                        {"i": 0, "v": [1760000000, 4100.1, 4102.2, 4099.9, 4101.5, 1234]},
                        {"i": 1, "v": [1760000300, 4101.5, 4103.0, 4100.0, 4102.0]},
                    ]
                }
            },
        ],
    }
    candles = _candles_from_series_payload(payload, "XAUUSD", "OANDA", "5m")

    assert len(candles) == 2
    assert candles[0].symbol == "XAUUSD"
    assert candles[0].exchange == "OANDA"
    assert candles[0].timeframe == "5m"
    assert candles[0].open == 4100.1
    assert candles[0].volume == 1234
    assert candles[1].volume is None

    db_path = tmp_path / "history.sqlite3"
    ensure_history_schema(db_path)
    assert store_historical_candles(candles, db_path) == 2
    # Upsert is counted as processed rows but must not duplicate DB rows.
    assert store_historical_candles(candles, db_path) == 2

    import sqlite3

    con = sqlite3.connect(db_path)
    count = con.execute("select count(*) from historical_candles").fetchone()[0]
    assert count == 2
