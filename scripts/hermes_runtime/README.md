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
