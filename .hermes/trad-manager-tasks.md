# Trad Manager Task List

Owner: MGT (Trad Manager Agent)
Scope: MGT supervises Trad, Dashboard, Backend, Data, DevOps, and Other tasks. Primary repo/runtime paths: /Users/waipop/MainWTN/Hermes/trad and local runtime scripts under /Users/waipop/.hermes/scripts
Last autonomous review: 2026-08-05 01:19 ICT

## Workflow
1. Waipop talks to Manager as the control point.
2. Manager reads Analyst reports and DB evidence; never guesses.
3. MGT maintains task lists by department before/after work.
4. Departments: Trad, Dashboard, Backend, Data, DevOps, Other.
5. MGT may propose work to Waipop. Apply code/config changes only when approved or explicitly requested.
6. After each completed change: verify with scripts/tests, review result, then commit/push repo changes when applicable.
7. Runtime-only Hermes scripts/config under ~/.hermes/scripts are local and not committed unless mirrored into the repo intentionally.
8. Routine no-risk/no-open-order WAIT status should stay silent; report only material changes, risks, or approval requests.
9. Language policy: MGT talks to Waipop in concise Thai; internal prompts/briefs to departments or specialists are English.

## Department task intake

### Trad
- [ ] Monitor XAUUSD automation quality: duplicate entries, WAIT_CONFIRMATION filtering, SL 500–800 point rule, stale data, BE/partial outcomes.
- [ ] Review Analyst recommendations every 15 minutes and propose only actionable changes.

### Dashboard
- [ ] Intake pending: no approved dashboard task yet.

### Backend
- [ ] Intake pending: no approved backend task yet.

### Data
- [ ] Intake pending: monitor `trade_signals`, `market_snapshots`, `trade_plan_outcomes`, and evaluation metrics.

### DevOps
- [ ] Intake pending: monitor cron/runtime reliability and commit/push hygiene.

### Other
- [ ] Intake pending: classify new work before execution.

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
- 2026-08-05: MGT scope expanded to accept/categorize Dashboard, Backend, Data, DevOps, and Other department tasks.
