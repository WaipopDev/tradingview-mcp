# Tester-only MQL5 port — fixed experiment

## Results (2026-09-11 to 2026-10-11, GOLD M5, 100 USD, 1:1000)

Real isolated run: `Model=4`, report quality **100% real ticks**, 5796 bars,
6,425,595 ticks, 18 deals. Raw report `D:/Hermes/mt5-portable/reports/risk10.htm`;
parsed values in `artifacts/tester-results-2026-09-11-to-2026-10-11.json`.

| run | risk per trade | signals | trades | net | ending | PF | equity DD | win rate |
|---|---|---|---|---|---|---|---|---|
| risk1 | 1% (1.00 USD) | 10 | 0 | 0.00 | 100.00 | 0 | 0.00 | 0% |
| risk3 | 3% (3.00 USD) | 10 | 0 | 0.00 | 100.00 | 0 | 0.00 | 0% |
| risk10 | 10% (10.00 USD) | 10 | 9 | +9.24 | 109.24 | 1.27 | 33.45 (26.62%) | 55.56% |

The 1% and 3% runs are empty by construction, not by luck: the ten signals had
stop distances of 3.24-9.59 price units and 0.01 lots on GOLD risks about
1.00 USD per unit, so the minimum lot already exceeded the budget. The `RISK_SKIP`
lines in `artifacts/tester-agent-20261011.log` show the distance and budget for
each skipped signal. `risk10` is the only run with enough budget for the minimum
lot; its 6.3-9.7% per-trade risk is what produces the 26.6% equity drawdown.

Details from the report: 7 SELL and 2 BUY, 5 winners / 4 losers, largest win
10.99, largest loss -9.34, average hold 31:49, recovery factor 0.28, Sharpe 1.69,
commission/swap/fee all 0.00, one signal skipped while a position was open, and
252 of 5796 bars rejected by the staleness/gap validator.

Nine trades on one symbol over one month proves nothing about the edge; treat the
table as a mechanism check plus a sizing warning, not a performance claim.

### How the run was reached, and what did not work

Two isolated routes were tried before this one ran; both stop before a report is
produced, and the reasons are evidence in the artifacts.
MetaEditor produced `NakedChartTester.ex5`; `NakedChartTester.log` records
**0 errors, 0 warnings**. The isolated portable terminal then loaded `tester.ini`
and exited with the exact blocker:

> tester not started because the account is not specified

See `artifacts/terminal-20261011.log`, `artifacts/tester-20261011.log`, and
`artifacts/summary.json`. No profitability report was generated. Metrics are
**unavailable**, not zero trades or a $100 verified ending balance. The 169
synthetic reference cases were generated and compiled into the EA; their MQL5
runtime execution is **not verified**, because initialization in the tester
never occurred. Python safety/contract tests are not a substitute for MQL5
runtime tests.

The isolated installation has no authenticated account. A user must authenticate
it themselves before a broker-backed test can run; no credentials were read,
copied, entered, or requested in chat. Do not copy the live installation's Config
or account files to work around this. The user's main terminal was not closed,
reconfigured, or given an EA; AutoTrading was not changed. No live orders were
submitted. The isolated terminal shut itself down after rejecting the test.

### What else was ruled out (later the same day)

- **Durable isolated install**: `D:/Hermes/mt5-portable` (portable mode, so its
  data folder is the install folder). Binaries plus non-secret GOLD market
  caches only; `credentials_copied=false` in `portable-manifest.json`. Built by
  `prepare_portable.py`, launched by `launch_portable.py`. The same
  `account is not specified` blocker applies until the user logs in once in that
  window; after that the login persists there and runs become repeatable.
- **Running the tester in the live terminal without a restart is impossible**:
  `terminal64.exe /config:...` launched while the live terminal is already
  running did nothing — no journal line, no tester job, still one process. An
  auto-start `[Tester]` config only applies at terminal startup, so an in-place
  run needs that terminal restarted. Not done.
- **MT5 has a built-in MCP server** (build 6060+): `http://127.0.0.1:22346/mcp`,
  server `MetaTrader5-MCP` on 127.0.0.1, with documented strategy-tester tools —
  `tester_prepare_config`, `tester_run_backtest`, `tester_optimization`,
  `tester_get_status`, `tester_wait`, `tester_get_report`, `tester_get_configuration`.
  Its API key is stored **encrypted at rest** (168 hex characters under
  `[MCP.MetaTrader]` in `config/assistant.ini`); Bearer/X-API-Key/query variants
  all return 401, so the plaintext key exists only in the terminal UI and cannot
  be recovered from disk. `tester_mcp.py` is a ready client once the key is
  supplied out-of-band (it reads the terminal's own file and never prints it).
- **The tester's settings fields are custom-drawn**, so Windows UIA exposes only
  the toolbar and tabs (verified: `Single`, `Visualize`, `Overview`, `Settings`,
  … but no Expert/Symbol/Model/Deposit fields and no vision provider configured
  on this host). Blind coordinate clicking of the tester could not be verified
  and was not attempted.

## Scope and exact fixed settings

- Exact instrument **GOLD**, never XAUUSD or GOLD24-7 substitution.
- Closed M5 bars with closed H1 alignment; 260-bar rolling windows match CLI
  analysis defaults. This differs from Python `replay`'s ever-growing prefix;
  pivot/BOS/retest logic itself is directly ported from `core.py`.
- Strict confirmed pivot width 2; HH+HL bullish, LH+LL bearish, otherwise range.
- BOS structure is computed only from bars **before** the BOS candle. A later
  rejection retests the BOS level within 1–4 bars; wick >= body, directional
  candle and all intervening closes intact. H1 must agree at M5 close time.
- One position at a time; first occurrence of `(side, BOS time)` is consumed
  even if rejected by spread/risk/position checks, with no repeated attempts.
- Market BUY at current ask, SELL at current bid. Stop is the BOS-to-rejection
  extreme rounded outward to the symbol tick grid. Requested TP is
  `2 * executable_quote - normalized_stop`: exactly 1:1 price distance before
  costs. Off-grid quotes, invalid stop direction, and broker stop-distance
  violations are skipped rather than moving the risk parameters.
- Fixed **1% of current equity** for modeled entry-to-stop loss. Size is floored
  to the lot step, then rechecked with `OrderCalcProfit`. If the minimum lot is
  too risky, skip. Margin is checked with `OrderCalcMargin` and `OrderCheck`.
  No risk escalation, martingale, optimization, or parameter search.
- Maximum ask-minus-bid spread **1.0 absolute price units**. Tick age <=120 sec.
- Initial deposit **100 USD**, leverage **1:1000**, also asserted by `OnInit`.
- Hard `MQL_TESTER` guard in `OnInit`, `OnTick`, `OnTester`, and the only
  `OrderSend` wrapper. There is no bypass parameter and no configurable inputs.

## Dates and modeling conventions

The supplied fixed config uses `FromDate=2026.09.11` and
`ToDate=2026.10.11`, as explicitly requested. MT5 date-only testing boundaries
are interpreted as start midnight inclusive and end midnight exclusive:
**[2026-09-11 00:00, 2026-10-11 00:00)** in tester/broker chart time, not UTC+7.
This is a trailing month, not the full previous calendar month. Including all
of October 11 would require `ToDate=2026.10.12` on October 12 or later; MT5
excludes the current day and clamps future end dates. That change was not made.
The interval was never reached by this run, so runtime boundary confirmation
is not available. October 11 is also incomplete at the time of this attempt.
This convention is explicit in the official [Strategy Testing documentation](https://www.metatrader5.com/en/terminal/help/algotrading/testing).

`Model=4` requests **Every tick based on real ticks**; `ExecutionMode=0` requests
no artificial execution delay. No alternate modeling mode was silently used.
No cached GOLD real-tick files were present in the source at preparation time;
only available broker bar/symbol caches were copied. A locked older bar file
was skipped and recorded in `isolation-manifest.json`. Broker synchronization
and real-tick coverage remain unverified. MT5 can synthesize gaps under real-tick
mode; a completed run must inspect the report/journal rather than assume 100%
real ticks from the setting alone.

Spread is included through executable bid/ask and tester prices. Broker
commission, swap, and fee totals are collected from tester deal history if the
run completes. They were not overridden or fabricated. The 1% budget excludes
commission, swap, fees, gaps, and slippage; realized loss can exceed 1%.
Deviation=0 and no-delay simulation do not guarantee zero fill slippage.
Requested and actual entry are logged separately; realized RR can differ from
requested RR if the fill slips. No break-even, trailing stop, or timed exit.
A completed test may close an open position at the tester's end boundary.

## Files and reproduction

- `NakedCore.mqh`: pure algorithm and volume floor.
- `NakedChartTester.mq5` / `.ex5`: tester-only EA, fixed settings.
- `CoreSelfTest.mqh`: generated synthetic Python-reference cases (169), including
  both directions, opposing/range H1 filters, prefixes, equal extrema, volume
  flooring, minimum-lot skip, and timestamp/stale/forming-bar validation.
- `generate_fixtures.py`: deterministic fixture generator importing unchanged
  Python `trad_auto.core`; the fixtures are **not real market data**.
- `test_port.py`: safety and contract tests, developed RED -> GREEN.
- `prepare_isolated.py`: allowlisted binaries + nonsecret GOLD market cache copy;
  isolated MetaEditor compile, no credentials or source profiles/config/logs.
- `launch_isolated.py`: compile-log-gated launch of only the isolated terminal.
- `tester.ini`: fixed real-tick experiment configuration.
- `isolation-manifest.json`, `launch.json`, `artifacts/`: execution evidence.

Run from the repository root (Windows Git Bash):

```bash
.venv/Scripts/python.exe trad_auto/mql5/generate_fixtures.py
.venv/Scripts/python.exe -m pytest trad_auto/mql5/test_port.py -q
.venv/Scripts/python.exe trad_auto/mql5/prepare_isolated.py
.venv/Scripts/python.exe trad_auto/mql5/launch_isolated.py
```

The durable portable route (preferred; login once by hand, then repeatable):

```bash
.venv/Scripts/python.exe trad_auto/mql5/prepare_portable.py   # build D:/Hermes/mt5-portable
# user logs in once inside that window: File -> Login to Trade Account
.venv/Scripts/python.exe trad_auto/mql5/launch_portable.py    # /portable + tester.ini -> report
.venv/Scripts/python.exe trad_auto/mql5/collect_portable_evidence.py
```

`run_tester_live.py` + `live/tester-live.ini` are kept as evidence of the
live-terminal attempt: they compile the EA into the live data folder and launch
`/config`, which is a verified no-op while that terminal is already running.
`tester_mcp.py list` / `schema <tool>` / `call <tool> <json>` drives the built-in
terminal MCP server (needs its undocumented-on-disk API key).

The portable location is
`C:/Users/waipo/AppData/Local/hermes/cache/scratch/trad-auto-mt5-isolated`.
It may be pruned as scratch; durable source, compiled binary, and evidence are
under this repository directory. `prepare_isolated.py` reads only the specified
MetaTrader binary paths and allowlisted broker market cache subdirectories.
MetaEditor can return exit code 1 **despite successful compilation**; validate
the log and fresh `.ex5`, not the process return code alone.

Do not count this attempt as a completed or zero-trade backtest. After user
setup of an isolated broker session, rerun this one fixed experiment and retain
its raw HTML report, journal, `CORE_SELFTEST ... failures=0`, and
`TESTER_SUMMARY` before reporting trades, profit, drawdown, or costs.

## Official references

- [Portable startup, configuration, tester Model/Deposit/Leverage/Report](https://www.metatrader5.com/en/terminal/help/start_advanced/start)
- [MetaEditor command-line compiler and /log](https://www.metatrader5.com/en/metaeditor/help/beginning/integration_ide)
- [MetaEditor portable mode](https://www.metatrader5.com/en/metaeditor/help/beginning/open)
- [Tester data synchronization and real-tick limitations](https://www.metatrader5.com/en/terminal/help/algotrading/test_preparation)
