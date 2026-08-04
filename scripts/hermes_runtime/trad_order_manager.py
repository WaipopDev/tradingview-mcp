#!/usr/bin/env python3
"""Manage open XAUUSD orders: hold/cut/breakeven/partial TP advice.

Runs after each collector tick. It does not mutate orders; it sends a Telegram
management alert only when the recommendation changes materially.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db_path_from_env() -> Path:
    configured = os.getenv("TRADINGVIEW_MCP_DB_PATH") or os.getenv("TRAD_SIGNAL_DB_PATH")
    return Path(configured).expanduser() if configured else Path.home() / ".tradingview-mcp" / "trading_signals.sqlite3"


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS telegram_order_management_alerts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          outcome_id INTEGER NOT NULL,
          fingerprint TEXT NOT NULL,
          target TEXT NOT NULL,
          delivered_at TEXT NOT NULL,
          UNIQUE(outcome_id, fingerprint, target)
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS trade_plan_outcomes (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT NOT NULL,
          timeframe TEXT NOT NULL DEFAULT '15m',
          direction TEXT NOT NULL,
          entry_low REAL NOT NULL,
          entry_high REAL NOT NULL,
          sl REAL NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending',
          created_at TEXT NOT NULL
        )
        """
    )
    cols = {r[1] for r in con.execute("PRAGMA table_info(trade_plan_outcomes)")}
    additions = {
        "management_state": "TEXT",
        "managed_sl": "REAL",
        "protected_at": "TEXT",
        "partial_taken_at": "TEXT",
        "partial_price": "REAL",
        "partial_fraction": "REAL",
        "exit_reason": "TEXT",
    }
    for name, ddl in additions.items():
        if name not in cols:
            con.execute(f"ALTER TABLE trade_plan_outcomes ADD COLUMN {name} {ddl}")
    return con


def fmt(n: float | None) -> str:
    return "-" if n is None else f"{float(n):.1f}".rstrip("0").rstrip(".")


def parse_json(v: Any, default: Any) -> Any:
    if not v:
        return default
    try:
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return default


def latest_signal(con: sqlite3.Connection, symbol: str, timeframe: str) -> sqlite3.Row | None:
    return con.execute(
        """
        SELECT * FROM trade_signals
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=?
        ORDER BY created_at DESC, id DESC LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()


def open_orders(con: sqlite3.Connection, symbol: str, timeframe: str):
    return con.execute(
        """
        SELECT * FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status IN ('pending','entered')
        ORDER BY id ASC
        """,
        (symbol, timeframe),
    ).fetchall()


def direction_points(direction: str, entry: float, price: float) -> float:
    return price - entry if direction == "BUY" else entry - price


def evaluate_order(row: sqlite3.Row, latest: sqlite3.Row) -> dict[str, Any]:
    price = float(latest["price"])
    tech = parse_json(latest["technical_json"], {})
    rsi = tech.get("rsi") or {}
    macd = tech.get("macd") or {}
    ema = tech.get("ema") if isinstance(tech.get("ema"), dict) else {}
    sentiment = tech.get("market_sentiment") or {}
    structure = tech.get("market_structure") or {}

    direction = str(row["direction"])
    entry_low = float(row["entry_low"])
    entry_high = float(row["entry_high"])
    sl = float(row["sl"])
    tp1 = row["tp1"]
    tp2 = row["tp2"]
    entry_ref = float(row["entry_price"] or (entry_high if direction == "BUY" else entry_low))
    risk = abs(entry_ref - sl) or 0.01
    profit = direction_points(direction, entry_ref, price)
    r_multiple = profit / risk
    mfe = float(row["max_favorable"] or 0)
    mae = float(row["max_adverse"] or 0)
    management_state = row["management_state"] if "management_state" in row.keys() else None
    partial_taken_at = row["partial_taken_at"] if "partial_taken_at" in row.keys() else None
    rsi_val = rsi.get("value")
    rsi_dir = str(rsi.get("direction") or "")
    macd_cross = str(macd.get("crossover") or "")
    momentum = str(sentiment.get("momentum") or "")
    trend = str(structure.get("trend") or "")
    ema20 = ema.get("ema20")
    ema20 = float(ema20) if ema20 is not None else None

    aligned = False
    reversal = False
    if direction == "BUY":
        aligned = (ema20 is None or price >= ema20) and "Bear" not in momentum and "Bear" not in trend
        reversal = (rsi_val is not None and float(rsi_val) >= 66 and "Fall" in rsi_dir) or "Bear" in macd_cross or (ema20 is not None and price < ema20)
    else:
        aligned = (ema20 is None or price <= ema20) and "Bull" not in momentum and "Bull" not in trend
        reversal = (rsi_val is not None and float(rsi_val) <= 34 and "Ris" in rsi_dir) or "Bull" in macd_cross or (ema20 is not None and price > ema20)

    # Score current order quality 0–100.
    score = 50
    score += 20 if aligned else -15
    if r_multiple >= 1.0:
        score += 20
    elif r_multiple >= 0.5:
        score += 10
    elif r_multiple < -0.35:
        score -= 20
    if reversal:
        score -= 20
    if mfe >= risk and reversal:
        score -= 10
    score = max(0, min(100, int(round(score))))

    suggested_sl = None
    cut_trigger = entry_low if direction == "BUY" else entry_high
    zone_broken = price < entry_low if direction == "BUY" else price > entry_high
    action = "HOLD"
    reason = "แรงยังพอไปต่อ ให้ถือต่อ"

    near_tp1 = False
    tp1_progress = 0.0
    if tp1 is not None:
        tp1f = float(tp1)
        tp1_distance = abs(tp1f - entry_ref) or 0.01
        tp1_progress = max(0.0, min(1.5, mfe / tp1_distance))
        near_tp1 = (direction == "BUY" and price >= tp1f - 1.0) or (direction == "SELL" and price <= tp1f + 1.0)

    if zone_broken and (not aligned or score < 40):
        action = "CUT_NOW"
        reason = (
            f"ราคาออกนอกโซนเข้าแล้ว ({'ต่ำกว่า' if direction == 'BUY' else 'สูงกว่า'} {fmt(cut_trigger)}) "
            "และสัญญาณไม่หนุน ควรคัทก่อนถึง Hard SL"
        )
    elif profit <= -0.5 * risk and not aligned:
        action = "CUT_NOW"
        reason = "ราคาเสียทางเกินครึ่งความเสี่ยง และ momentum ไม่หนุน ควรคัทก่อนถึง Hard SL"
    elif partial_taken_at is None and (mfe >= 5.0 or tp1_progress >= 0.65 or near_tp1) and reversal:
        action = "TAKE_PARTIAL"
        suggested_sl = entry_ref
        reason = "MFE >= 5 หรือไปได้เกิน 65% ของ TP1 แล้วเริ่มย้อนกลับ แนะนำแบ่งปิดและเลื่อน SL หน้าทุน"
    elif partial_taken_at is None and profit >= 0.6 * risk and reversal:
        action = "TAKE_PARTIAL"
        suggested_sl = entry_ref
        reason = "กำไรยังไม่ถึง TP แต่เริ่มย้อนกลับ แนะนำแบ่งเก็บบางส่วน"
    elif management_state != "BE_PROTECTED" and profit >= 0.5 * risk:
        action = "MOVE_SL_BE"
        suggested_sl = entry_ref
        reason = "กำไรเกินครึ่งความเสี่ยง เลื่อน SL มาหน้าทุนเพื่อลดความเสี่ยง"
    elif not aligned and profit <= 0:
        action = "PROTECT"
        reason = (
            f"ไม้เริ่มไม่สวย ให้ป้องกันความเสี่ยง; จุดคัทก่อน SL คือ "
            f"{'M5/ราคาล่าสุดปิดต่ำกว่า' if direction == 'BUY' else 'M5/ราคาล่าสุดปิดสูงกว่า'} {fmt(cut_trigger)}"
        )

    return {
        "id": row["id"],
        "direction": direction,
        "price": price,
        "entry_low": entry_low,
        "entry_high": entry_high,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "score": score,
        "action": action,
        "reason": reason,
        "suggested_sl": suggested_sl,
        "cut_trigger": cut_trigger,
        "hard_sl": sl,
        "profit": profit,
        "r_multiple": r_multiple,
        "mfe": mfe,
        "mae": mae,
        "rsi": rsi_val,
        "ema20": ema20,
        "management_state": management_state,
        "partial_taken_at": partial_taken_at,
    }


def fingerprint(e: dict[str, Any]) -> str:
    """Stable management fingerprint: do not alert every price/score bucket.

    CUT_NOW is terminal and should pass immediately. Other actions are keyed by
    action + persisted management state so PROTECT/MOVE_SL_BE spam is reduced.
    """
    if e["action"] == "CUT_NOW":
        return "CUT_NOW"
    state = e.get("management_state") or "NONE"
    return f"{e['action']}:{state}:{fmt(e.get('suggested_sl'))}"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def already_sent(con: sqlite3.Connection, outcome_id: int, fp: str, target: str, action: str | None = None) -> bool:
    row = con.execute(
        "SELECT delivered_at FROM telegram_order_management_alerts WHERE outcome_id=? AND fingerprint=? AND target=? ORDER BY delivered_at DESC LIMIT 1",
        (outcome_id, fp, target),
    ).fetchone()
    if row is not None:
        return True
    if action == "CUT_NOW":
        return False
    prefix = (action or fp.split(":", 1)[0]) + ":%"
    recent = con.execute(
        """
        SELECT delivered_at FROM telegram_order_management_alerts
        WHERE outcome_id=? AND target=? AND fingerprint LIKE ?
        ORDER BY delivered_at DESC LIMIT 1
        """,
        (outcome_id, target, prefix),
    ).fetchone()
    if recent is None:
        return False
    delivered = _parse_dt(recent["delivered_at"])
    if delivered is None:
        return False
    cooldown_minutes = 30
    return (datetime.now(timezone.utc) - delivered).total_seconds() < cooldown_minutes * 60


def mark_sent(con: sqlite3.Connection, outcome_id: int, fp: str, target: str) -> None:
    con.execute(
        "INSERT OR IGNORE INTO telegram_order_management_alerts (outcome_id, fingerprint, target, delivered_at) VALUES (?, ?, ?, ?)",
        (outcome_id, fp, target, utc_now()),
    )


def close_for_cut(con: sqlite3.Connection, e: dict[str, Any]) -> None:
    """Close an order in the tracker when the manager says CUT_NOW."""
    now = utc_now()
    con.execute(
        """
        UPDATE trade_plan_outcomes
        SET status='closed', result='CUT', current_price=?, closed_at=COALESCE(closed_at, ?), last_checked_at=?,
            exit_reason=?
        WHERE id=? AND status IN ('pending','entered')
        """,
        (e["price"], now, now, e["reason"], e["id"]),
    )


def apply_management_state(con: sqlite3.Connection, e: dict[str, Any]) -> None:
    """Persist non-final management actions so final result can be classified."""
    now = utc_now()
    if e["action"] == "MOVE_SL_BE":
        con.execute(
            """
            UPDATE trade_plan_outcomes
            SET management_state='BE_PROTECTED', managed_sl=?, protected_at=COALESCE(protected_at, ?),
                current_price=?, last_checked_at=?
            WHERE id=? AND status IN ('pending','entered')
            """,
            (e["suggested_sl"], now, e["price"], now, e["id"]),
        )
    elif e["action"] == "TAKE_PARTIAL":
        con.execute(
            """
            UPDATE trade_plan_outcomes
            SET management_state='PARTIAL_TP', managed_sl=COALESCE(?, managed_sl), protected_at=COALESCE(protected_at, ?),
                partial_taken_at=COALESCE(partial_taken_at, ?), partial_price=COALESCE(partial_price, ?),
                partial_fraction=COALESCE(partial_fraction, 0.5), current_price=?, last_checked_at=?
            WHERE id=? AND status IN ('pending','entered')
            """,
            (e.get("suggested_sl"), now, now, e["price"], e["price"], now, e["id"]),
        )


def message(e: dict[str, Any]) -> str:
    lines = [
        f"Order #{e['id']} Management | {e['action']}",
        f"Score: {e['score']}/100 | ราคา: {fmt(e['price'])}",
        f"{e['direction']} {fmt(e['entry_low'])}–{fmt(e['entry_high'])}",
        f"Cut trigger: {fmt(e.get('cut_trigger'))} | Hard SL: {fmt(e['hard_sl'])}",
        f"TP: {fmt(e['tp1'])} / {fmt(e['tp2'])}",
        f"P/L: {e['profit']:.2f} จุดราคา | R≈{e['r_multiple']:.2f}",
        f"MFE: {e['mfe']:.2f} | MAE: {e['mae']:.2f}",
        f"เหตุผล: {e['reason']}",
    ]
    if e.get("suggested_sl") is not None:
        lines.append(f"แนะนำ SL ใหม่: {fmt(e['suggested_sl'])} (หน้าทุน)")
    lines.append(f"RSI: {fmt(e.get('rsi'))} | EMA20: {fmt(e.get('ema20'))}")
    return "\n".join(lines)


def should_alert(e: dict[str, Any]) -> bool:
    return e["action"] in {"CUT_NOW", "PROTECT", "MOVE_SL_BE", "TAKE_PARTIAL"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET") or "telegram:8237892676")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    with connect(Path(args.db_path).expanduser()) as con:
        latest = latest_signal(con, args.symbol, args.timeframe)
        if latest is None or latest["price"] is None:
            return 0
        for row in open_orders(con, args.symbol, args.timeframe):
            e = evaluate_order(row, latest)
            if not should_alert(e):
                continue
            fp = fingerprint(e)
            if e["action"] == "CUT_NOW" and not args.dry_run:
                close_for_cut(con, e)
            elif e["action"] in {"MOVE_SL_BE", "TAKE_PARTIAL"} and not args.dry_run:
                apply_management_state(con, e)
            if already_sent(con, int(e["id"]), fp, args.target, e["action"]):
                continue
            msg = message(e)
            if args.dry_run:
                print(msg)
                print("---")
                continue
            sent = subprocess.run(
                ["hermes", "send", "--quiet", "--to", args.target, "--subject", f"XAUUSD Order #{e['id']} {e['action']}", msg],
                text=True,
                capture_output=True,
                check=False,
            )
            if sent.returncode != 0:
                print(sent.stderr.strip() or sent.stdout.strip(), flush=True)
                return sent.returncode
            mark_sent(con, int(e["id"]), fp, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
