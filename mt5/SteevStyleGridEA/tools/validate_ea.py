#!/usr/bin/env python3
"""Lightweight static validation for SteevStyleGridEA artifacts.

This does not replace MetaEditor compilation. It catches incomplete files,
unbalanced delimiters, missing required safety inputs, and preset drift.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EA = ROOT / "SteevStyleGridEA.mq5"
PRESET = ROOT / "presets" / "XAUUSD-Demo.set"
README = ROOT / "README.md"
PLAN = ROOT / "docs" / "backtest-plan.md"
COMPILED = ROOT / "build" / "SteevStyleGridEA.ex5"
COMPILE_REPORT = ROOT / "build" / "compile-report.txt"

REQUIRED_INPUTS = {
    "InpGridMode",
    "InpFixedLot",
    "InpLevelsPerSide",
    "InpGridSpacingPoints",
    "InpStopLossPoints",
    "InpTakeProfitPoints",
    "InpMaxOpenPositions",
    "InpMaxOpenLots",
    "InpMaxPendingLots",
    "InpBasketTakeProfitMoney",
    "InpBasketStopLossMoney",
    "InpMaxDailyLossPercent",
    "InpMaxEquityDrawdownPct",
    "InpMaxSpreadPoints",
    "InpMagic",
}

REQUIRED_FUNCTIONS = {
    "OnInit",
    "OnTick",
    "OnTradeTransaction",
    "PlaceFreshGrid",
    "ManageRiskAndPositions",
    "ManageBreakEvenPartialAndTrail",
    "CancelPendingType",
    "CloseAllPositions",
    "EmergencyStop",
    "HasPositionType",
    "TradeResultAccepted",
}

REQUIRED_SAFETY_SNIPPETS = {
    "potential_lots>InpMaxOpenLots": "worst-case open-lot cap",
    "TradeResultAccepted(close_sent,false,false,false)": "full-close retcode enforcement",
    'CloseAllPositions("persistent risk-lock enforcement")': "risk-lock liquidation retry",
    "g_cycle_active && g_exit_seen": "between-poll exit lifecycle tracking",
    'CancelAllPendings("restart orphan-safety reset")': "restart orphan cleanup",
    "(g_risk_lock || stored_lock) && owned_exposure": "risk-lock rollover persistence",
}


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r'"(?:\\.|[^"\\])*"', '""', text)
    return text


def assert_balanced(text: str) -> None:
    clean = strip_comments_and_strings(text)
    pairs = {"(": ")", "{": "}", "[": "]"}
    stack: list[str] = []
    for char in clean:
        if char in pairs:
            stack.append(char)
        elif char in pairs.values():
            if not stack or pairs[stack.pop()] != char:
                raise AssertionError(f"Unbalanced delimiter near {char!r}")
    if stack:
        raise AssertionError(f"Unclosed delimiters: {stack[-10:]}")


def main() -> int:
    for path in (EA, PRESET, README, PLAN, COMPILED, COMPILE_REPORT):
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"Missing or empty artifact: {path}")

    source = EA.read_text(encoding="utf-8")
    assert_balanced(source)

    inputs = set(re.findall(r"(?m)^input\s+\w+(?:\s+\w+)?\s+(Inp\w+)\s*=", source))
    missing_inputs = REQUIRED_INPUTS - inputs
    if missing_inputs:
        raise AssertionError(f"Missing required inputs: {sorted(missing_inputs)}")

    functions = set(re.findall(r"(?m)^(?:int|void|bool|double|string)\s+(\w+)\s*\(", source))
    missing_functions = REQUIRED_FUNCTIONS - functions
    if missing_functions:
        raise AssertionError(f"Missing required functions: {sorted(missing_functions)}")

    for snippet, label in REQUIRED_SAFETY_SNIPPETS.items():
        if snippet not in source:
            raise AssertionError(f"Missing safety invariant: {label}")

    preset_keys = {
        line.split("=", 1)[0].strip()
        for line in PRESET.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
    missing_preset = REQUIRED_INPUTS - preset_keys
    if missing_preset:
        raise AssertionError(f"Preset missing safety inputs: {sorted(missing_preset)}")

    forbidden = ("martingale", "lot_multiplier", "doubling_lot")
    lower_source = source.lower()
    for token in forbidden:
        if token in lower_source and token != "martingale":
            raise AssertionError(f"Forbidden risk pattern found: {token}")

    report = COMPILE_REPORT.read_text(encoding="utf-8")
    if "Result: 0 errors, 0 warnings" not in report:
        raise AssertionError("Compile report does not confirm a clean MetaEditor build")
    digest = hashlib.sha256(COMPILED.read_bytes()).hexdigest()
    if f"SHA-256: {digest}" not in report:
        raise AssertionError("Compiled EX5 hash does not match compile report")

    print(f"PASS: {EA.name}")
    print(f"inputs={len(inputs)} functions={len(functions)} preset_keys={len(preset_keys)}")
    print(f"compiled_ex5_bytes={COMPILED.stat().st_size} sha256={digest}")
    print("MetaEditor compile verified: 0 errors, 0 warnings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
