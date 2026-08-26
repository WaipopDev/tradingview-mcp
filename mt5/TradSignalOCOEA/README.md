# TradSignalOCOEA

Fail-closed MT5 execution EA for externally scored `trad` signals. It is an execution/risk layer, not a strategy generator: no martingale, grid, or averaging is implemented.

> **Version status:** five source iterations exist (`TradSignalOCOEA_V0.02.mq5` … `_V0.06.mq5`). Only **V0.02** has a MetaEditor compile report and `.ex5` in `build/`, and `tools/validate_ea.py` only checks V0.02. `V0.03`–`V0.06` are later source revisions that have **never been compiled or validated** — do not treat them as ready, and do not use them in Strategy Tester/Demo/Live until each has its own compile report and the validator is updated to point at the intended release.

## Signal contract

`SignalFile` is a **relative file name** in the terminal's `MQL5/Files` sandbox. It must contain exactly a header and one non-empty CSV record, UTF-8/ANSI plain text:

```csv
signal_id,created_utc,side,entry,sl,tp1,tp2,score,session,expiry_utc
xau-asia-sell-20260817-001,2026-08-17T01:15:00Z,SELL,3350.00,3360.00,3340.00,3330.00,78,Asia,2026-08-17T03:15:00Z
```

All timestamps are ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`). The EA rejects malformed/multi-row files, blank IDs, duplicate IDs, stale creation timestamps, expiry timestamps at or before creation, expired signals, score below `MinScore`, wrong side/session gates, or invalid price geometry. Default gates are **BOTH** sides, **ALL** sessions, and score **>=70**. `AllowedSide` can be `BOTH`, `BUY`, or `SELL`; `AllowedSession=ALL` permits the full broker day.

For SELL, `sl > entry > tp1 > tp2`; for BUY, `sl < entry < tp1 < tp2`. Only one `Symbol()+Magic` position or pending order may exist. The EA uses a fixed lot and chooses one pending stop/limit order based on the live quote. It checks spread/session/risk locks before submitting. CTrade retcodes are checked after every trade request.

## Risk and operations

Daily realized-loss and equity-drawdown locks are persisted as terminal global variables. A lock blocks new entries and repeatedly attempts EA-owned position/order cleanup until ownership is verified flat. Duplicate signal IDs are persisted too. Use `presets/XAUUSD-AllDay-Both-Tester.set` for Shadow testing. Compilation is intentionally not represented as complete until an independently generated `.ex5` and MetaEditor report are placed in `build/`.

Run static delivery checks:

```sh
python3 tools/validate_ea.py --source-only
python3 tools/validate_ea.py
```

The second command must fail until a real MetaEditor compile report and artifact exist; do not fabricate either.
