from __future__ import annotations

from tradingview_mcp.core.services.tradingview_auxiliary_cache import TradingViewAuxiliaryCache


def test_tradingview_auxiliary_cache_uses_default_ttl_and_skips_fresh_refetch():
    cache = TradingViewAuxiliaryCache()
    cache.put("XAUUSD", {"source": "TradingView", "is_proxy": True}, fetched_at=100.0)

    fresh = cache.get("XAUUSD", now=500.0)
    expired = cache.get("XAUUSD", now=1_901.0)

    assert fresh == {"source": "TradingView", "is_proxy": True, "age_seconds": 400.0, "stale": False}
    assert expired == {"source": "TradingView", "is_proxy": True, "age_seconds": 1_801.0, "stale": True}
    assert cache.should_fetch("XAUUSD", now=500.0) is False
    assert cache.should_fetch("XAUUSD", now=1_901.0) is True
