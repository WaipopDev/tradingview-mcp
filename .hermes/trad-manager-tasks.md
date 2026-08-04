# Trad Manager Task List

Owner: Trad Manager Agent
Scope: /Users/waipop/MainWTN/Hermes/trad and local runtime scripts under /Users/waipop/.hermes/scripts

## Workflow
1. Waipop talks to Manager as the control point.
2. Manager reads Analyst reports and DB evidence; never guesses.
3. Manager maintains this task list before/after work.
4. Manager may propose work to Waipop. Apply code/config changes only when approved or explicitly requested.
5. After each completed change: verify with scripts/tests, review result, then commit/push repo changes when applicable.
6. Runtime-only Hermes scripts/config under ~/.hermes/scripts are local and not committed unless mirrored into the repo intentionally.

## Active Tasks
- [ ] Monitor XAUUSD automation quality: duplicate entries, WAIT_CONFIRMATION filtering, SL 500–800 point rule, stale data, BE/partial outcomes.
- [ ] Review Analyst recommendations every 15 minutes and propose only actionable changes.
- [x] Apply approved Manager proposal 2026-08-05: post-manager outcome alert, earlier partial rule, market_snapshots persistence, non-TradingView price fallback.

## Done Log
- 2026-08-05: Established Manager/Analyst workflow and task-list policy.
- 2026-08-05: Approved proposal implemented locally; repo side updated for market_snapshots persistence.
