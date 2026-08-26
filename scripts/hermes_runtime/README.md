# Hermes Runtime Scripts

Mirrors of the local production scripts used by the Hermes cron job for Waipop's XAUUSD automation.

Live runtime location:

```text
/Users/waipop/.hermes/scripts/
```

Mirrored files in this directory are committed so logic changes can be reviewed/versioned. Deploy by copying the relevant file back to the live runtime location and ensuring executable permissions where needed.

Notes:
- Telegram target may still be overridden by `TRAD_TELEGRAM_TARGET` at runtime.
- Trading decisions remain deterministic unless the AI gate explicitly asks for an AI summary.
- `trad_price_fallback.py` may use Yahoo `GC=F` + stored basis only as an emergency TP/SL proxy when TradingView is stale; it is not used for new entries.
- 2026-08-26: mirror expanded to cover the full live script set (was previously only 3 of 13 files, and those 3 had drifted weeks behind live). Sync direction was live → repo for this pass, since `~/.hermes/scripts/` had the validated/battle-tested versions. Going forward, keep both sides in sync on every logic change — do not let this drift again.
- `trad_collect_and_ai_alert_xauusd.sh` reverted to the TradingView data source on 2026-08-26. It had been silently running on `--data-source mt5` with no `MT5MarketDataBridge` snapshot available (indicator was never attached to a live chart), which caused ~20 days of no new signals/alerts while reporting cron success. Do not re-enable `--data-source mt5` until `mt5/MT5MarketDataBridge/README.md`'s attach + tick-freshness proof passes.
