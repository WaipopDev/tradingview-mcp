# SteevStyleGridEA Live-Attach Incident — Closure Note (2026-08-26)

## Background

`.hermes/mt5-live-attach-handoff.md` (2026-08-06) tasked attaching `SteevStyleGridEA`
live on `GOLD,H1`. Several read-only investigation scripts
(`extract_steev_*.py`, `inspect_mt5_steev_logs.py`) were written the same day to dig
into the MT5 log after live trading started, but no conclusion was ever written down —
the investigation trailed off. This note closes it using what evidence still exists.

## What the evidence shows

Source: MT5 terminal `logs/20260806.log` and `logs/20260807.log` (plain-text Journal,
UTF-16LE). The detailed per-EA Experts-tab prints (`SGRID initialized...`,
`Grid placed...`, basket TP/SL messages) that `mt5-live-attach-handoff.md` asked for as
proof lived in `MQL5/Logs/20260806.log`, which **has since rotated out and no longer
exists** — that level of detail is not recoverable.

What the surviving Journal/Trades log does show:

- Account `321782852` on broker `XMGlobal-MT5`.
- Between 2026-08-06 12:31 and 13:54, the EA was attached/removed/re-attached **many**
  times, with 4 separate `initializing ... failed with code 32767 (incorrect
  parameters)` errors (13:17, 13:35, 13:38, 13:54). This pattern — rapid reload cycles
  clustered in one ~80-minute window, then stable — reads as manual preset/parameter
  tuning while attaching, not a runtime crash mid-trade.
- Across 2026-08-06 and 2026-08-07 the account filled **266 GOLD trades** (130 buy /
  136 sell, all 0.01 lot per the sampled lines) while price ranged roughly
  **4231.72 – 4315.79** (~84 price units). That trade count and lot size match a
  basket-cycling grid EA re-opening after every basket TP/SL hit, not a single
  runaway position.
- The EA that was actually running for most of the session was
  `SteevStyleGridEA_ReversalShadow (GOLD,M15)` — **M15, Reversal mode**, not the
  `GOLD,H1` from the original handoff doc. Whoever ran this pivoted to the Reversal
  Shadow preset partway through, which the original handoff plan didn't anticipate.
- **The session ended cleanly.** At 2026-08-07 15:41:57 automated trading was manually
  disabled; both open pending orders were cancelled by 15:42:00; the EA was removed at
  15:43:17; the terminal exited normally (`exit with code 0`) and disconnected from the
  broker at 15:48:48. No dangling pending orders or unmanaged exposure was left behind.

## What is NOT established

- **Exact realized $ P&L is not recoverable from this log.** The Journal shows fill
  prices but not per-deal profit/commission/swap; that requires MT5's own Account
  History / deals report, which needs the terminal's GUI (out of reach for a headless
  read-only log scrape). If an exact number matters, open MT5 → Toolbox → History,
  filter 2026-08-06 to 2026-08-07, and read the account's realized P&L directly.
- Whether the 4 "incorrect parameters" init failures reflect a real EA input-validation
  bug (e.g. a parameter combination the EA should accept but rejects) versus operator
  error while typing preset values — the log does not say which input was rejected.

## Verdict

No evidence of an unbounded loss, a stuck position, or the EA misbehaving after
initialization — the trade volume and price range are consistent with a basket-cycling
grid EA absorbing normal chop, and the session was closed out deliberately and cleanly.
The open items are process gaps, not proof of a losing-logic bug:

1. `MQL5/Logs/` rotates fast enough that same-day forensic detail can be gone within
   ~2-3 weeks — if a live/shadow run matters, export or copy that log before it rotates.
2. The `GOLD,H1` → `GOLD,M15` Reversal-Shadow preset switch was never captured in a
   handoff/decision doc.

## Recommendation

Do not re-attach `SteevStyleGridEA` (or its Reversal Shadow variant) live or on shadow
without: (a) a fresh Strategy Tester pass on the current v1.02 build per
`docs/backtest-plan.md`, and (b) copying `MQL5/Logs/<date>.log` out of the terminal
data folder before it rotates, so any future incident review has the detail this one
was missing.
