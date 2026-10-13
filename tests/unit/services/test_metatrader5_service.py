from __future__ import annotations

from types import SimpleNamespace

import pytest

from tradingview_mcp.core.services import metatrader5_service as mt5_service


class FakeMT5:
    TIMEFRAME_M15 = 15
    TIMEFRAME_H1 = 60
    TIMEFRAME_D1 = 1440
    COPY_TICKS_INFO = 0

    def __init__(self, rates):
        self.rates = rates
        self.initialized = False

    def initialize(self, *args, **kwargs):
        self.initialized = True
        return True

    def shutdown(self):
        self.initialized = False

    def symbol_select(self, symbol, enabled):
        return symbol == "XAUUSD"

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        assert symbol == "XAUUSD"
        assert timeframe == self.TIMEFRAME_M15
        assert start == 0
        return self.rates[-count:]

    def last_error(self):
        return (1, "Success")


def _rates():
    return [
        {"time": i, "open": 100 + i, "high": 102 + i, "low": 99 + i, "close": 101 + i, "tick_volume": 1000 + i}
        for i in range(60)
    ]


def test_mt5_rates_are_normalized_to_indicator_payload(monkeypatch):
    fake = FakeMT5(_rates())
    monkeypatch.setattr(mt5_service, "_mt5", fake)

    payload = mt5_service.fetch_indicator_payload("XAUUSD", "15m", bars=60)

    assert payload["symbol"] == "XAUUSD"
    assert payload["source"] == "MetaTrader5"
    assert payload["timeframe"] == "15m"
    assert payload["close"] == 160.0
    assert payload["open"] == 159.0
    assert payload["volume"] == 1059.0
    assert payload["SMA20"] is not None
    assert payload["EMA50"] is not None
    assert payload["RSI"] == 100.0
    assert payload["BB.upper"] is not None
    assert payload["ATR"] is not None


def test_mt5_rejects_unsupported_timeframe(monkeypatch):
    monkeypatch.setattr(mt5_service, "_mt5", FakeMT5(_rates()))
    with pytest.raises(ValueError, match="Unsupported MT5 timeframe"):
        mt5_service.fetch_indicator_payload("XAUUSD", "2m")


def test_mt5_reports_symbol_selection_failure(monkeypatch):
    fake = FakeMT5(_rates())
    fake.symbol_select = lambda symbol, enabled: False
    monkeypatch.setattr(mt5_service, "_mt5", fake)

    with pytest.raises(mt5_service.MetaTrader5DataError, match="cannot select symbol"):
        mt5_service.fetch_indicator_payload("MISSING", "15m")


def test_analyze_coin_routes_to_mt5_when_selected(monkeypatch):
    from tradingview_mcp.core.services import screener_service

    monkeypatch.setenv("TRADINGVIEW_MCP_DATA_PROVIDER", "mt5")
    monkeypatch.setattr(
        mt5_service,
        "analyze_symbol",
        lambda symbol, exchange, timeframe: {
            "symbol": symbol,
            "exchange": exchange,
            "timeframe": timeframe,
            "source": "MetaTrader5",
        },
    )

    result = screener_service.analyze_coin("XAUUSD", "MT5", "15m")

    assert result["source"] == "MetaTrader5"
    assert result["symbol"] == "XAUUSD"
