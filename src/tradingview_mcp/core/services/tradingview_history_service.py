"""TradingView historical candle fetch + SQLite storage.

Uses TradingView's chart websocket protocol directly (no browser, no paid API).
This is best-effort and should be rate-limited; TradingView can throttle or
change the protocol. Data is stored locally for MGT/Analyst backtests.
"""
from __future__ import annotations

import base64
import json
import os
import random
import socket
import ssl
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from tradingview_mcp.core.storage.database import PathLike, connect_database, initialize_database

_TV_HOST = "data.tradingview.com"
_TV_PATH = "/socket.io/websocket"
_TF_MAP = {
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "45m": "45",
    "1h": "60",
    "2h": "120",
    "4h": "240",
    "1d": "D",
}


@dataclass(frozen=True)
class HistoricalCandle:
    symbol: str
    exchange: str
    timeframe: str
    ts: int
    datetime_utc: str
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    source: str = "TradingView chart websocket"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_history_schema(db_path: PathLike | None = None) -> Path:
    db_path_obj = initialize_database(db_path)
    with connect_database(db_path_obj) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS historical_candles (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT NOT NULL,
              exchange TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              ts INTEGER NOT NULL,
              datetime_utc TEXT NOT NULL,
              open REAL NOT NULL,
              high REAL NOT NULL,
              low REAL NOT NULL,
              close REAL NOT NULL,
              volume REAL,
              source TEXT NOT NULL DEFAULT 'TradingView chart websocket',
              fetched_at TEXT NOT NULL,
              raw_json TEXT,
              UNIQUE(symbol, exchange, timeframe, ts)
            );
            CREATE INDEX IF NOT EXISTS idx_historical_candles_lookup
            ON historical_candles(symbol, exchange, timeframe, ts);

            CREATE TABLE IF NOT EXISTS historical_fetch_runs (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              symbol TEXT NOT NULL,
              exchange TEXT NOT NULL,
              timeframe TEXT NOT NULL,
              requested_bars INTEGER NOT NULL,
              stored_bars INTEGER NOT NULL,
              source TEXT NOT NULL,
              status TEXT NOT NULL,
              error TEXT,
              started_at TEXT NOT NULL,
              finished_at TEXT NOT NULL
            );
            """
        )
    return db_path_obj


def _tv_frame(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, separators=(",", ":"))
    return f"~m~{len(body)}~m~{body}"


def _session(prefix: str) -> str:
    return f"{prefix}_{random.randrange(10**11, 10**12 - 1)}"


def _encode_symbol(exchange: str, symbol: str) -> str:
    full = f"{exchange.upper()}:{symbol.upper()}"
    return json.dumps({"symbol": full, "adjustment": "splits", "session": "regular"}, separators=(",", ":"))


def _parse_tv_messages(text: str) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    i = 0
    while i < len(text):
        if text.startswith("~m~", i):
            j = text.find("~m~", i + 3)
            if j == -1:
                break
            try:
                n = int(text[i + 3 : j])
            except ValueError:
                break
            start = j + 3
            raw = text[start : start + n]
            i = start + n
        else:
            raw = text[i:]
            i = len(text)
        raw = raw.strip()
        if not raw or raw.startswith("~h~"):
            continue
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            messages.append(obj)
    return messages


def _candles_from_series_payload(payload: dict[str, Any], symbol: str, exchange: str, timeframe: str) -> list[HistoricalCandle]:
    series = (((payload.get("p") or [None, {}])[1] or {}).get("s1") or {})
    rows = series.get("s") or []
    candles: list[HistoricalCandle] = []
    for row in rows:
        vals = row.get("v") if isinstance(row, dict) else None
        if not isinstance(vals, list) or len(vals) < 5:
            continue
        try:
            ts = int(vals[0])
            o, h, l, c = (float(vals[1]), float(vals[2]), float(vals[3]), float(vals[4]))
            vol = None if len(vals) < 6 or vals[5] is None else float(vals[5])
        except (TypeError, ValueError):
            continue
        candles.append(
            HistoricalCandle(
                symbol=symbol.upper(),
                exchange=exchange.upper(),
                timeframe=timeframe,
                ts=ts,
                datetime_utc=datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                open=o,
                high=h,
                low=l,
                close=c,
                volume=vol,
            )
        )
    candles.sort(key=lambda c: c.ts)
    return candles


class _SimpleWebSocket:
    """Minimal client for text frames from TradingView's websocket endpoint."""

    def __init__(self, host: str = _TV_HOST, path: str = _TV_PATH, timeout: float = 20.0):
        self.host = host
        self.path = path
        self.timeout = timeout
        raw = socket.create_connection((host, 443), timeout=timeout)
        self.sock = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        # Use short read timeouts so callers can keep waiting until their
        # overall deadline instead of failing on a single quiet interval.
        self.sock.settimeout(min(5.0, timeout))
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Origin: https://www.tradingview.com\r\n"
            "User-Agent: tradingview-mcp history collector\r\n"
            "\r\n"
        )
        self.sock.sendall(req.encode("ascii"))
        resp = self.sock.recv(4096)
        if b" 101 " not in resp.split(b"\r\n", 1)[0]:
            raise RuntimeError(f"TradingView websocket handshake failed: {resp[:160]!r}")

    def close(self) -> None:
        try:
            self.sock.close()
        except Exception:
            pass

    def send_text(self, text: str) -> None:
        data = text.encode("utf-8")
        header = bytearray([0x81])
        n = len(data)
        if n < 126:
            header.append(0x80 | n)
        elif n < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", n))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", n))
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def recv_text(self) -> str:
        try:
            first = self._recv_exact(2)
        except socket.timeout:
            return ""
        opcode = first[0] & 0x0F
        length = first[1] & 0x7F
        masked = bool(first[1] & 0x80)
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length) if length else b""
        if masked:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        if opcode == 8:
            raise EOFError("TradingView websocket closed")
        if opcode == 9:  # ping -> pong
            self._send_control(0x8A, payload)
            return ""
        if opcode != 1:
            return ""
        return payload.decode("utf-8", errors="replace")

    def _send_control(self, first_byte: int, payload: bytes) -> None:
        mask = os.urandom(4)
        header = bytes([first_byte, 0x80 | len(payload)])
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(header + mask + masked)

    def _recv_exact(self, n: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < n:
            chunk = self.sock.recv(n - len(chunks))
            if not chunk:
                raise EOFError("socket closed")
            chunks.extend(chunk)
        return bytes(chunks)


def fetch_tradingview_candles(symbol: str, exchange: str = "OANDA", timeframe: str = "15m", bars: int = 500, timeout: float = 30.0) -> list[HistoricalCandle]:
    if timeframe not in _TF_MAP:
        raise ValueError(f"Unsupported timeframe {timeframe!r}; choose {sorted(_TF_MAP)}")
    bars = max(1, min(int(bars), 5000))
    chart_session = _session("cs")
    quote_session = _session("qs")
    ws = _SimpleWebSocket(timeout=timeout)
    try:
        commands = [
            {"m": "set_auth_token", "p": ["unauthorized_user_token"]},
            {"m": "chart_create_session", "p": [chart_session, ""]},
            {"m": "quote_create_session", "p": [quote_session]},
            {"m": "quote_set_fields", "p": [quote_session, "ch", "chp", "current_session", "description", "local_description", "language", "exchange", "fractional", "is_tradable", "lp", "lp_time", "minmov", "minmove2", "original_name", "pricescale", "pro_name", "short_name", "type", "update_mode", "volume", "currency_code"]},
            {"m": "quote_add_symbols", "p": [quote_session, f"{exchange.upper()}:{symbol.upper()}", {"flags": ["force_permission"]}]},
            {"m": "resolve_symbol", "p": [chart_session, "symbol_1", f"={_encode_symbol(exchange, symbol)}"]},
            {"m": "create_series", "p": [chart_session, "s1", "s1", "symbol_1", _TF_MAP[timeframe], bars, ""]},
        ]
        for command in commands:
            ws.send_text(_tv_frame(command))
            time.sleep(0.05)
        deadline = time.time() + timeout
        last_error: str | None = None
        while time.time() < deadline:
            text = ws.recv_text()
            if not text:
                continue
            for message in _parse_tv_messages(text):
                method = message.get("m")
                if method == "critical_error":
                    last_error = str(message.get("p"))
                if method == "timescale_update":
                    candles = _candles_from_series_payload(message, symbol, exchange, timeframe)
                    if candles:
                        return candles
        raise TimeoutError(last_error or "Timed out waiting for TradingView timescale_update")
    finally:
        ws.close()


def store_historical_candles(candles: Iterable[HistoricalCandle], db_path: PathLike | None = None) -> int:
    db_path_obj = ensure_history_schema(db_path)
    fetched_at = utc_now_iso()
    count = 0
    with connect_database(db_path_obj) as conn:
        for candle in candles:
            conn.execute(
                """
                INSERT INTO historical_candles
                (symbol, exchange, timeframe, ts, datetime_utc, open, high, low, close, volume, source, fetched_at, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, exchange, timeframe, ts) DO UPDATE SET
                  open=excluded.open,
                  high=excluded.high,
                  low=excluded.low,
                  close=excluded.close,
                  volume=excluded.volume,
                  source=excluded.source,
                  fetched_at=excluded.fetched_at,
                  raw_json=excluded.raw_json
                """,
                (
                    candle.symbol,
                    candle.exchange,
                    candle.timeframe,
                    candle.ts,
                    candle.datetime_utc,
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume,
                    candle.source,
                    fetched_at,
                    json.dumps(candle.__dict__, ensure_ascii=False, sort_keys=True),
                ),
            )
            count += 1
    return count


def collect_and_store_historical_candles(symbol: str = "XAUUSD", exchange: str = "OANDA", timeframe: str = "15m", bars: int = 500, db_path: PathLike | None = None, timeout: float = 30.0) -> dict[str, Any]:
    db_path_obj = ensure_history_schema(db_path)
    started = utc_now_iso()
    status = "ok"
    error = None
    stored = 0
    source = "TradingView chart websocket"
    try:
        candles = fetch_tradingview_candles(symbol=symbol, exchange=exchange, timeframe=timeframe, bars=bars, timeout=timeout)
        stored = store_historical_candles(candles, db_path_obj)
    except Exception as exc:
        status = "error"
        error = str(exc)
    finished = utc_now_iso()
    with connect_database(db_path_obj) as conn:
        conn.execute(
            """
            INSERT INTO historical_fetch_runs
            (symbol, exchange, timeframe, requested_bars, stored_bars, source, status, error, started_at, finished_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (symbol.upper(), exchange.upper(), timeframe, int(bars), stored, source, status, error, started, finished),
        )
    if error:
        return {"status": status, "error": error, "stored_bars": stored, "symbol": symbol.upper(), "exchange": exchange.upper(), "timeframe": timeframe}
    return {"status": status, "stored_bars": stored, "symbol": symbol.upper(), "exchange": exchange.upper(), "timeframe": timeframe, "db_path": str(db_path_obj)}
