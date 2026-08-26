# Shadow Validation — Order Loss Logic (2026-08-06)

- DB: `/Users/waipop/.tradingview-mcp/trading_signals.sqlite3`
- Mode: `PRAGMA query_only=ON` (no DB mutation)
- Scope: outcome classification + pending/entered management + Scalp HTF gate

## Baseline vs shadow

- Stored closed: 56 | Win 27 | Loss 28 | Neutral 1
- Stored decided WR: 49.1%
- Closed rows with no actual entry (`entry_price` or `entered_at` NULL): **10** (1 false win / 9 false losses)
- Shadow actual entered trades: 26W / 19L / 1 neutral
- Shadow decided WR after excluding never-entered rows: **57.8%**
- Shadow Win/closed after excluding never-entered rows: **56.5%**

## Never-entered rows incorrectly counted as outcomes

| ID | Source | Side | Result | Entry trigger/zone | MFE | MAE |
|---:|---|---|---|---:|---:|---:|
| 41 | telegram_scalp_watch | SELL | CUT | 4135.32 | 0.00 | 3.14 |
| 42 | telegram_scalp_watch | SELL | PARTIAL_BE | 4160.65 | 6.65 | 0.00 |
| 43 | telegram_scalp_watch | SELL | CUT | 4174.48 | 2.68 | 0.00 |
| 44 | telegram_scalp_watch | BUY | CUT | 4159.28 | 0.00 | 1.90 |
| 49 | telegram_scalp_watch | SELL | CUT | 4230.50 | 2.02 | 0.00 |
| 50 | telegram_scalp_watch | SELL | SL | 4251.64 | 0.00 | 12.78 |
| 51 | telegram_entry_alert | BUY | CUT | 4262.04-4265.84 | 0.00 | 0.00 |
| 54 | telegram_scalp_watch | SELL | CUT | 4261.45 | 0.00 | 6.67 |
| 56 | telegram_scalp_watch | SELL | CUT | 4294.21 | 0.00 | 3.40 |
| 57 | telegram_scalp_watch | BUY | CUT | 4264.71 | 0.00 | 2.21 |

## Actual entered breakdown

| Source | Side | W | L | N | Decided WR |
|---|---|---:|---:|---:|---:|
| telegram_entry_alert | BUY | 20 | 17 | 0 | 54.1% |
| telegram_entry_alert | SELL | 0 | 0 | 1 | 0.0% |
| telegram_manual | BUY | 1 | 0 | 0 | 100.0% |
| telegram_scalp_watch | BUY | 3 | 0 | 0 | 100.0% |
| telegram_scalp_watch | SELL | 2 | 2 | 0 | 50.0% |

## Scalp Watch score/side

| Score | Side | W | L | N | Decided WR |
|---|---|---:|---:|---:|---:|
| 60-69 | BUY | 2 | 0 | 0 | 100.0% |
| 60-69 | SELL | 1 | 0 | 0 | 100.0% |
| <60 | BUY | 1 | 0 | 0 | 100.0% |
| <60 | SELL | 1 | 2 | 0 | 33.3% |

## Management timing

- Entered losses with MFE >= 5 but no partial protection: **5**
- IDs: #30, #31, #32, #33, #34

## Root-cause verdict

1. **PASS — safe to patch pending-management bug:** `trad_order_manager.open_orders()` selected both pending and entered rows. Pending setups could be closed as CUT before any entry occurred.
2. **PASS — safe to patch fallback bug:** emergency price fallback also evaluated pending rows and could create false TP/SL (observed in regression test).
3. **PASS — safe to patch entry-state bug:** generic zone crossing marked main pullback orders entered without touching their zone; crossing semantics belong only to Scalp Watch trigger orders.
4. **PASS — safe to patch Scalp HTF lookup bug:** `build_watch()` called `.get()` on `sqlite3.Row`; the caught exception silently forced HTF bias to NEUTRAL and bypassed counter-trend score >=75.
5. **PASS — safe to patch missing-HTF behavior:** an all-empty MTF response looked like valid NEUTRAL and allowed low-score scalps; Scalp Watch must fail closed when H1/H4 evidence is unavailable.
6. **PASS — safe to patch stale-signal behavior:** main entry alert had no age check and could reuse the last DB signal after a fail-soft collector outage.
7. **PASS — safe to patch reporting:** user-facing stats must exclude closed rows with no actual entry, without rewriting historical DB outcomes.
8. **NOT APPROVED in this patch:** broad score/session/strategy threshold changes. The actual-entered post-instrumentation sample is still small.
9. Existing historical rows must not be rewritten automatically; report corrected analytics separately unless user explicitly approves data repair.

## Applied production change

- Order manager and emergency fallback manage only `status='entered'` rows.
- Main/manual orders enter only while price is inside their zone; crossing is retained only for Scalp Watch triggers.
- Scalp Watch reads symbol via `row['symbol']`, requires real H1/H4 evidence, and otherwise fails closed.
- Main entry alert rejects stale/invalid signals older than 420 seconds.
- Outcome stats count only rows with non-null `entry_price` and `entered_at`.
- Existing score thresholds, SL/TP, and session rules remain unchanged.
