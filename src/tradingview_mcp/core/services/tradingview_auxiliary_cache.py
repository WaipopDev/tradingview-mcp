"""In-memory, low-frequency TradingView auxiliary context cache.

This boundary intentionally does not perform network calls. Callers may populate
it from an auxiliary job on a slower cadence; MT5 price reads never depend on it.
"""
from __future__ import annotations

import time
from typing import Any

DEFAULT_TTL_SECONDS = 1800.0


class TradingViewAuxiliaryCache:
    def __init__(self, ttl_seconds: float = DEFAULT_TTL_SECONDS):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = float(ttl_seconds)
        self._entries: dict[str, tuple[float, dict[str, Any]]] = {}

    def put(self, symbol: str, payload: dict[str, Any], *, fetched_at: float | None = None) -> None:
        self._entries[symbol.strip().upper()] = (time.time() if fetched_at is None else float(fetched_at), dict(payload))

    def get(self, symbol: str, *, now: float | None = None) -> dict[str, Any] | None:
        entry = self._entries.get(symbol.strip().upper())
        if entry is None:
            return None
        fetched_at, payload = entry
        age = max(0.0, (time.time() if now is None else float(now)) - fetched_at)
        result = dict(payload)
        result.update({"age_seconds": age, "stale": age > self.ttl_seconds})
        return result

    def should_fetch(self, symbol: str, *, now: float | None = None) -> bool:
        entry = self._entries.get(symbol.strip().upper())
        if entry is None:
            return True
        now_value = time.time() if now is None else float(now)
        return now_value - entry[0] > self.ttl_seconds
