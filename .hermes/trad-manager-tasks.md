# Trad Manager Task List

Owner: Trad Manager Agent
Scope: /Users/waipop/MainWTN/Hermes/trad and local runtime scripts under /Users/waipop/.hermes/scripts
Last autonomous review: 2026-08-05 01:02 ICT

## Workflow
1. Waipop talks to Manager as the control point.
2. Manager reads Analyst reports and DB evidence; never guesses.
3. Manager maintains this task list before/after work.
4. Manager may propose work to Waipop. Apply code/config changes only when approved or explicitly requested.
5. After each completed change: verify with scripts/tests, review result, then commit/push repo changes when applicable.
6. Runtime-only Hermes scripts/config under ~/.hermes/scripts are local and not committed unless mirrored into the repo intentionally.
7. Routine no-risk/no-open-order WAIT status should stay silent; report only material changes, risks, or approval requests.

## Active monitoring
- [ ] Monitor XAUUSD automation quality: duplicate entries, WAIT_CONFIRMATION filtering, SL 500–800 point rule, stale data, BE/partial outcomes.
- [ ] Review Analyst recommendations every 15 minutes and propose only actionable changes.

## Proposed / awaiting Waipop approval

1. **Tighten duplicate-zone entry guard**
   - Evidence: orders #30-#33 were repeated BUY entries in nearby zones during the same downswing and all closed SL; later #34 and #37 closed CUT.
   - Proposal: block same-direction XAUUSD entries when a recent open/closed order within the last 30-45 minutes has overlapping entry zone or same 5-8 USD band, unless a new higher-timeframe confirmation/fresh BOS is present.

2. **Reduce repeated management-alert spam**
   - Evidence: order #36 received multiple `MOVE_SL_BE` management alerts with changing fingerprints before TP1; order #37 received repeated `PROTECT` alerts before CUT.
   - Proposal: normalize alert fingerprint by outcome_id + action + management_state, and add cooldown per action unless severity changes to `CUT_NOW`.

3. **Review post-SL pause/reduce-direction logic**
   - Evidence: today has 13 SL, 2 CUT, 18 TP1, 2 TP2, 1 TP3; recent SL cluster #30-#33 followed by later CUTs suggests BUY pause after repeated SLs should be stricter.
   - Proposal: after 3 same-direction SL/CUT within 90 minutes, require WAIT_CONFIRMATION or higher score threshold for next same-direction entry.

## Completed / verified
- 2026-08-05: Established Manager/Analyst workflow and task-list policy.
- 2026-08-05: Approved proposal implemented locally; repo side updated for market_snapshots persistence.
- 2026-08-05: Checked DB tables and outcome summary; verified latest signal was WAIT_CONFIRMATION and no open orders at review time.
- 2026-08-05: Manager Agent prompt updated to stay silent on routine no-risk/no-open-order status and report only material changes or approval requests.
