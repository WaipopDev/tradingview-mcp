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

- None currently.

## Completed / verified
- 2026-08-05: Established Manager/Analyst workflow and task-list policy.
- 2026-08-05: Approved proposal implemented locally; repo side updated for market_snapshots persistence.
- 2026-08-05: Checked DB tables and outcome summary; verified latest signal was WAIT_CONFIRMATION and no open orders at review time.
- 2026-08-05: Manager Agent prompt updated to stay silent on routine no-risk/no-open-order status and report only material changes or approval requests.
- 2026-08-05: MGT scope expanded to accept/categorize Dashboard, Backend, Data, DevOps, and Other department tasks.
- 2026-08-05: Approved Trad proposals completed locally: tighter 45m duplicate-zone guard, 90m post-SL/CUT pause requiring TRADE+score>=85, and normalized management-alert cooldown to reduce PROTECT/MOVE_SL_BE spam.
