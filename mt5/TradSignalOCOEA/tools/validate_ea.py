#!/usr/bin/env python3
"""Fail-closed static/package validation for TradSignalOCOEA.

A source-only pass deliberately does not mean MetaEditor compilation occurred.
"""
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SOURCE_MARKERS = (
    "#include <Trade/Trade.mqh>", "input string SignalFile",
    "FILE_TXT", "StringSplit", "AllowedSide", "AllowedSession", "MinScore",
    "MaxSpreadPoints", "MaxSignalAgeMinutes", "DailyLossLimit",
    "MaxEquityDrawdownPercent", "ResultRetcode", "HasOwnedExposure",
    "GlobalVariableSet", "Duplicate", "PositionClose", "OrderDelete",
    "VerifyFlat", "BUY", "SELL", "TimeGMT", "ExecutionAccountAllowed", "ACCOUNT_TRADE_MODE_REAL",
)
HEADER = "signal_id,created_utc,side,entry,sl,tp1,tp2,score,session,expiry_utc"


def fail(message: str) -> bool:
    print(f"FAIL: {message}")
    return False


def validate_source() -> bool:
    ok = True
    source = ROOT / "TradSignalOCOEA_V0.02.mq5"
    readme = ROOT / "README.md"
    example = ROOT / "signal-example.csv"
    preset = ROOT / "presets/XAUUSD-AllDay-Both-Tester.set"
    plan = ROOT / "docs/backtest-plan.md"
    for path in (source, readme, example, preset, plan):
        if not path.is_file():
            ok = fail(f"missing required delivery file: {path.relative_to(ROOT)}") and ok
    if not source.is_file():
        return False
    text = source.read_text(encoding="utf-8")
    missing = [marker for marker in REQUIRED_SOURCE_MARKERS if marker not in text]
    if not re.search(r"\binput\s+ulong\s+Magic\b", text):
        missing.append("input ulong Magic")
    if missing:
        ok = fail("source safety markers missing: " + ", ".join(missing)) and ok
    else:
        print("PASS: TradSignalOCOEA_V0.02.mq5")
    if readme.is_file() and example.is_file():
        sample = example.read_text(encoding="utf-8").splitlines()
        if (HEADER not in readme.read_text(encoding="utf-8") or len(sample) != 2
                or sample[0] != HEADER):
            ok = fail("signal contract README/example mismatch") and ok
        else:
            print("PASS: signal contract")
    return ok


def validate_compile() -> bool:
    artifact = ROOT / "build/TradSignalOCOEA_V0.02.ex5"
    report = ROOT / "build/compile-report.txt"
    if not artifact.is_file() or not report.is_file():
        return fail("MetaEditor compile evidence missing: require build/TradSignalOCOEA_V0.02.ex5 and build/compile-report.txt")
    source = ROOT / "TradSignalOCOEA_V0.02.mq5"
    if not source.is_file():
        return fail("source missing; cannot bind compile evidence")
    report_text = report.read_text(encoding="utf-8", errors="replace")
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if not re.search(r"\b0 errors, 0 warnings\b", report_text, re.I):
        return fail("compile report does not prove 0 errors, 0 warnings")
    if source_digest not in report_text:
        return fail("compile report does not contain Source SHA-256 matching TradSignalOCOEA_V0.02.mq5")
    if digest not in report_text:
        return fail("compile report does not contain SHA-256 of TradSignalOCOEA_V0.02.ex5")
    print("MetaEditor compile verified: 0 errors, 0 warnings.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    ok = validate_source()
    if not args.source_only:
        ok = validate_compile() and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
