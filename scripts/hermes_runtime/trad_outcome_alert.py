#!/usr/bin/env python3
"""Notify Telegram when tracked trade-plan outcomes close at TP/SL."""
from __future__ import annotations

import argparse
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


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
        CREATE TABLE IF NOT EXISTS telegram_outcome_alerts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          outcome_id INTEGER NOT NULL,
          result TEXT NOT NULL,
          target TEXT NOT NULL,
          delivered_at TEXT NOT NULL,
          UNIQUE(outcome_id, result, target)
        )
        """
    )
    return con


def fmt(n: float | None) -> str:
    return "-" if n is None else f"{float(n):.1f}".rstrip("0").rstrip(".")


def pending_closed(con: sqlite3.Connection, symbol: str, timeframe: str, target: str):
    return con.execute(
        """
        SELECT o.* FROM trade_plan_outcomes o
        LEFT JOIN telegram_outcome_alerts a
          ON a.outcome_id=o.id AND a.result=o.result AND a.target=?
        WHERE UPPER(o.symbol)=UPPER(?) AND o.timeframe=?
          AND o.status='closed' AND o.result IS NOT NULL
          AND a.id IS NULL
        ORDER BY o.closed_at ASC, o.id ASC
        """,
        (target, symbol, timeframe),
    ).fetchall()


def stats(con: sqlite3.Connection, symbol: str, timeframe: str) -> tuple[int, int, int, float]:
    row = con.execute(
        """
        SELECT COUNT(*) total,
               SUM(CASE WHEN result LIKE 'TP%' OR result='PARTIAL_BE' THEN 1 ELSE 0 END) wins,
               SUM(CASE WHEN result IN ('SL','CUT') THEN 1 ELSE 0 END) losses
        FROM trade_plan_outcomes
        WHERE UPPER(symbol)=UPPER(?) AND timeframe=? AND status='closed'
          AND entry_price IS NOT NULL AND entered_at IS NOT NULL
          AND (
            (direction='BUY' AND sl < entry_low AND entry_low <= entry_high AND entry_high < tp1)
            OR
            (direction='SELL' AND tp1 < entry_low AND entry_low <= entry_high AND entry_high < sl)
          )
        """,
        (symbol, timeframe),
    ).fetchone()
    total = int(row["total"] or 0)
    wins = int(row["wins"] or 0)
    losses = int(row["losses"] or 0)
    wr = wins / total * 100 if total else 0.0
    return total, wins, losses, wr


def close_reason(row: sqlite3.Row) -> str:
    result = str(row["result"] or "")
    direction = str(row["direction"])
    entry_low = float(row["entry_low"])
    entry_high = float(row["entry_high"])
    current = float(row["current_price"] or 0)
    mfe = float(row["max_favorable"] or 0)
    mae = float(row["max_adverse"] or 0)
    if result in {"SL", "CUT", "BE", "PARTIAL_BE", "TRAIL_SL"}:
        if result == "SL":
            label = "SL"
        elif result == "CUT":
            label = "จุดคัทก่อน SL"
        elif result == "BE":
            label = "หน้าทุน"
        elif result == "PARTIAL_BE":
            label = "แบ่งปิดกำไรแล้วกลับมาปิดหน้าทุน"
        else:
            label = "trailing SL"
        if direction == "BUY":
            return f"เหตุผล: ราคาหลุดโซน BUY และแตะ {label}; MFE {mfe:.2f} / MAE {mae:.2f}"
        return f"เหตุผล: ราคาทะลุโซน SELL และแตะ {label}; MFE {mfe:.2f} / MAE {mae:.2f}"
    if result.startswith("TP"):
        if direction == "BUY":
            return f"เหตุผล: BUY ถูกทาง ราคาไปต่อเหนือโซนเข้าและแตะ {result}; MFE {mfe:.2f}"
        return f"เหตุผล: SELL ถูกทาง ราคาไหลต่ำกว่าโซนเข้าและแตะ {result}; MFE {mfe:.2f}"
    return "เหตุผล: ปิดตามเงื่อนไขระบบ"


def logic_note(row: sqlite3.Row) -> str:
    result = str(row["result"] or "")
    direction = str(row["direction"])
    if result == "SL":
        return f"ปรับ logic: ลด/งด {direction} หาก order ฝั่งเดียวกันชน SL ต่อเนื่อง หรือ RSI อยู่ปลายรอบ"
    return "ปรับ logic: เก็บรูปแบบนี้เป็นฝั่งที่ใช้ได้ แต่ยังคุมไม่ให้ส่งซ้ำถี่"


def message(row: sqlite3.Row, total: int, wins: int, losses: int, wr: float) -> str:
    source = str(row["source"] or "") if "source" in row.keys() else ""
    is_scalp = "scalp" in source.lower()
    win_result = str(row["result"] or "").startswith("TP") or str(row["result"] or "") == "PARTIAL_BE"
    icon = "✅" if win_result else "❌"
    title = f"{icon} Scalp Outcome #{row['id']} ปิดแล้ว: {row['result']}" if is_scalp else f"{icon} Order #{row['id']} ปิดแล้ว: {row['result']}"
    type_line = "ประเภท: Scalp Watch tracked result" if is_scalp else "ประเภท: Entry Order"
    return "\n".join([
        title,
        type_line,
        f"{row['direction']} {fmt(row['entry_low'])}–{fmt(row['entry_high'])}",
        f"SL: {fmt(row['sl'])} | TP: {fmt(row['tp1'])} / {fmt(row['tp2'])} / {fmt(row['tp3'])}",
        f"ราคาปิด/ล่าสุด: {fmt(row['current_price'])}",
        f"MFE: {float(row['max_favorable'] or 0):.2f} | MAE: {float(row['max_adverse'] or 0):.2f}",
        close_reason(row),
        "",
        f"สถิติรวม: Win {wins}/{total} = {wr:.1f}% | Loss {losses}",
    ])


def mark(con: sqlite3.Connection, row: sqlite3.Row, target: str) -> None:
    con.execute(
        """
        INSERT OR IGNORE INTO telegram_outcome_alerts
        (outcome_id, result, target, delivered_at)
        VALUES (?, ?, ?, ?)
        """,
        (row["id"], row["result"], target, utc_now()),
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db-path", default=str(db_path_from_env()))
    p.add_argument("--symbol", default="XAUUSD")
    p.add_argument("--timeframe", default="15m")
    p.add_argument("--target", default=os.getenv("TRAD_TELEGRAM_TARGET") or "telegram:8237892676")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    with connect(Path(args.db_path).expanduser()) as con:
        rows = pending_closed(con, args.symbol, args.timeframe, args.target)
        if not rows:
            return 0
        total, wins, losses, wr = stats(con, args.symbol, args.timeframe)
        for row in rows:
            msg = message(row, total, wins, losses, wr)
            if args.dry_run:
                print(msg)
                print("---")
                continue
            subject_prefix = "XAUUSD Scalp Outcome" if "scalp" in str(row["source"] or "").lower() else "XAUUSD Order"
            sent = subprocess.run(
                ["hermes", "send", "--quiet", "--to", args.target, "--subject", f"{subject_prefix} #{row['id']} {row['result']}", msg],
                text=True,
                capture_output=True,
                check=False,
            )
            if sent.returncode != 0:
                print(sent.stderr.strip() or sent.stdout.strip(), flush=True)
                return sent.returncode
            mark(con, row, args.target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
