#!/usr/bin/env python3
"""Fallback price-only outcome evaluator for XAUUSD.

When the main 15m collector is stale because TradingView scanner returns empty
JSON, this script first tries the lighter TradingView single-symbol 5m path, and
then a non-TradingView Yahoo GC=F futures proxy adjusted by a recent basis.
The proxy is used only for TP/SL order tracking, not for new entries.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/Users/waipop/MainWTN/Hermes/trad")
sys.path.insert(0, str(REPO / "src"))

from tradingview_mcp.core.services.screener_service import analyze_coin  # noqa: E402


def db_path() -> Path:
    return Path(
        os.getenv("TRADINGVIEW_MCP_DB_PATH")
        or os.getenv("TRAD_SIGNAL_DB_PATH")
        or Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"
    ).expanduser()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(s):
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def ensure_basis_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS external_price_basis (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          source TEXT NOT NULL,
          tv_price REAL NOT NULL,
          external_price REAL NOT NULL,
          basis REAL NOT NULL,
          created_at TEXT NOT NULL
        )
        """
    )
    con.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_external_price_basis_symbol_source_time
        ON external_price_basis(symbol, source, created_at DESC)
        """
    )


def get_tv_price(symbol: str, exchange: str, timeframe: str) -> tuple[float, str]:
    data = analyze_coin(symbol, exchange, timeframe)
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(str(data.get("error")))
    price = (((data or {}).get("price_data") or {}).get("current_price"))
    if price is None:
        raise RuntimeError("fallback TV price missing")
    return float(price), "tradingview_single_symbol"


def get_yahoo_gc_price() -> tuple[float, str]:
    url = "https://query1.finance.yahoo.com/v8/finance/chart/GC=F?range=1d&interval=1m"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        payload = json.loads(r.read().decode("utf-8"))
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        raise RuntimeError("Yahoo GC=F payload missing result")
    meta = result.get("meta") or {}
    price = meta.get("regularMarketPrice")
    if price is None:
        quote = (((result.get("indicators") or {}).get("quote") or [{}])[0])
        closes = [v for v in (quote.get("close") or []) if v is not None]
        price = closes[-1] if closes else None
    if price is None:
        raise RuntimeError("Yahoo GC=F price missing")
    return float(price), "yahoo_gc_f_basis_proxy"


def refresh_external_basis(con: sqlite3.Connection, symbol: str, tv_price: float) -> None:
    """Store TV spot-vs-GC futures basis while TV data is fresh."""
    try:
        ext_price, source = get_yahoo_gc_price()
    except Exception:
        return
    con.execute(
        """
        INSERT INTO external_price_basis (symbol, source, tv_price, external_price, basis, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (symbol.upper(), source, tv_price, ext_price, tv_price - ext_price, now()),
    )
    con.commit()


def latest_basis(con: sqlite3.Connection, symbol: str, max_age_seconds: int) -> tuple[float, str] | None:
    row = con.execute(
        """
        SELECT source, basis, created_at FROM external_price_basis
        WHERE UPPER(symbol)=UPPER(?) ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol,),
    ).fetchone()
    if not row:
        return None
    dt = parse_dt(row["created_at"])
    if not dt or (datetime.now(timezone.utc) - dt).total_seconds() > max_age_seconds:
        return None
    return float(row["basis"]), str(row["source"])


def get_external_basis_price(con: sqlite3.Connection, symbol: str, max_basis_age_seconds: int) -> tuple[float, str]:
    basis_row = latest_basis(con, symbol, max_basis_age_seconds)
    if not basis_row:
        raise RuntimeError("no recent external GC=F basis available")
    basis, source = basis_row
    ext_price, _ = get_yahoo_gc_price()
    return ext_price + basis, source


def close_result(direction: str, price: float, entry: float, effective_sl: float, row: sqlite3.Row) -> str | None:
    managed_sl = row["managed_sl"] if "managed_sl" in row.keys() else None
    partial_taken = ("partial_taken_at" in row.keys()) and row["partial_taken_at"] is not None
    tp1, tp2, tp3 = row["tp1"], row["tp2"], row["tp3"]
    if direction == "BUY":
        if price <= effective_sl:
            if managed_sl is not None and abs(effective_sl - entry) <= 0.05:
                return "PARTIAL_BE" if partial_taken else "BE"
            return "TRAIL_SL" if managed_sl is not None else "SL"
        if tp3 is not None and price >= float(tp3):
            return "TP3"
        if tp2 is not None and price >= float(tp2):
            return "TP2"
        if tp1 is not None and price >= float(tp1):
            return "TP1"
    else:
        if price >= effective_sl:
            if managed_sl is not None and abs(effective_sl - entry) <= 0.05:
                return "PARTIAL_BE" if partial_taken else "BE"
            return "TRAIL_SL" if managed_sl is not None else "SL"
        if tp3 is not None and price <= float(tp3):
            return "TP3"
        if tp2 is not None and price <= float(tp2):
            return "TP2"
        if tp1 is not None and price <= float(tp1):
            return "TP1"
    return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--exchange", default="OANDA")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--fallback-timeframe", default="5m")
    p.add_argument("--max-age-seconds", type=int, default=120)
    p.add_argument("--max-basis-age-seconds", type=int, default=6 * 60 * 60)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    con = sqlite3.connect(Path(args.db_path).expanduser())
    con.row_factory = sqlite3.Row
    ensure_basis_table(con)

    open_rows = con.execute(
        "select * from trade_plan_outcomes where upper(symbol)=upper(?) and timeframe=? and status in ('pending','entered')",
        (args.symbol, args.timeframe),
    ).fetchall()
    latest = con.execute(
        "select price,created_at from trade_signals where upper(symbol)=upper(?) and timeframe=? order by id desc limit 1",
        (args.symbol, args.timeframe),
    ).fetchone()
    age = 999999
    if latest:
        dt = parse_dt(latest["created_at"])
        if dt:
            age = int((datetime.now(timezone.utc) - dt).total_seconds())

    # When the main TradingView collector is fresh, maintain a non-TV basis for future stale windows.
    if latest and latest["price"] is not None and age < args.max_age_seconds:
        refresh_external_basis(con, args.symbol, float(latest["price"]))
        return 0
    if not open_rows:
        return 0

    errors: list[str] = []
    try:
        price, source = get_tv_price(args.symbol, args.exchange, args.fallback_timeframe)
    except Exception as exc:
        errors.append(f"tv_single_symbol={exc}")
        try:
            price, source = get_external_basis_price(con, args.symbol, args.max_basis_age_seconds)
        except Exception as ext_exc:
            errors.append(f"external_basis={ext_exc}")
            if args.dry_run:
                print("fallback_error=" + " | ".join(errors))
            return 0

    ts = now()
    closed = []
    updated = 0
    for r in open_rows:
        direction = str(r["direction"])
        entry = float(r["entry_price"] or (r["entry_high"] if direction == "BUY" else r["entry_low"]))
        prev_mfe = float(r["max_favorable"] or 0)
        prev_mae = float(r["max_adverse"] or 0)
        favorable = (price - entry) if direction == "BUY" else (entry - price)
        adverse = (entry - price) if direction == "BUY" else (price - entry)
        mfe = max(prev_mfe, favorable)
        mae = max(prev_mae, adverse)
        managed_sl = r["managed_sl"] if "managed_sl" in r.keys() else None
        effective_sl = float(managed_sl) if managed_sl is not None else float(r["sl"])
        result = close_result(direction, price, entry, effective_sl, r)
        if args.dry_run:
            print({"id": r["id"], "fallback_price": round(price, 2), "source": source, "result": result, "mfe": round(mfe, 2), "mae": round(mae, 2)})
            continue
        if result:
            con.execute(
                "update trade_plan_outcomes set status='closed', result=?, current_price=?, max_favorable=?, max_adverse=?, closed_at=coalesce(closed_at,?), last_checked_at=?, exit_reason=coalesce(exit_reason, ?) where id=? and status in ('pending','entered')",
                (result, price, mfe, mae, ts, ts, f"price fallback source={source}", r["id"]),
            )
            closed.append((r["id"], result))
        else:
            con.execute(
                "update trade_plan_outcomes set current_price=?, max_favorable=?, max_adverse=?, last_checked_at=? where id=? and status in ('pending','entered')",
                (price, mfe, mae, ts, r["id"]),
            )
            updated += 1
    con.commit()
    if closed or updated:
        print(f"fallback_price={price:.2f} source={source} closed={closed} updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
