#!/usr/bin/env bash
set -euo pipefail
cd /Users/waipop/MainWTN/Hermes/trad

# XAUUSD market guard: stay silent while spot gold is closed.
# Uses UTC close window: Friday 22:00 UTC → Sunday 22:00 UTC
# (about Saturday 05:00 → Monday 05:00 Thailand time).
if ! python /Users/waipop/.hermes/scripts/trad_market_hours.py --symbol XAUUSD --quiet; then
  exit 0
fi

json_out="$(mktemp /tmp/trad_collect_ai_json.XXXXXX)"
err_out="$(mktemp /tmp/trad_collect_ai_err.XXXXXX)"
tracker_out="$(mktemp /tmp/trad_outcome_tracker.XXXXXX)"
trap 'rm -f "$json_out" "$err_out" "$tracker_out"' EXIT

# Collect first. Retryable upstream outages exit 0; keep previous DB state and stay silent.
if ! /Users/waipop/.local/bin/uv run python scripts/collect_trad_signal.py --json >"$json_out" 2>"$err_out"; then
  cat "$err_out" >&2
  exit 1
fi

# Track/evaluate trade-plan outcomes after each fresh price pull. Stay quiet on success.
python /Users/waipop/.hermes/scripts/trad_outcome_tracker.py --auto-track --evaluate >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Warn if upstream is stale while orders are open, so stale DB prices do not hide TP/SL hits.
python /Users/waipop/.hermes/scripts/trad_stale_guard.py --target "${TRAD_TELEGRAM_TARGET:-telegram:8237892676}" >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# If main 15m collector is stale, use a lighter 5m single-symbol fallback price to close/update open orders.
/Users/waipop/.local/bin/uv run python /Users/waipop/.hermes/scripts/trad_price_fallback.py >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Default target is Waipop's Telegram chat; override with TRAD_TELEGRAM_TARGET if needed.
export TRAD_TELEGRAM_TARGET="${TRAD_TELEGRAM_TARGET:-telegram:8237892676}"

# Notify when any tracked order closes at TP/SL.
python /Users/waipop/.hermes/scripts/trad_outcome_alert.py --target "$TRAD_TELEGRAM_TARGET" >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Manage still-open orders: hold/cut/breakeven/partial TP advice with score.
# This can close orders as CUT or persist BE/PARTIAL state.
python /Users/waipop/.hermes/scripts/trad_order_manager.py --target "$TRAD_TELEGRAM_TARGET" >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Run closure alert again after order manager, so CUT_NOW/BE/PARTIAL_BE closures are delivered immediately.
python /Users/waipop/.hermes/scripts/trad_outcome_alert.py --target "$TRAD_TELEGRAM_TARGET" >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Send deterministic entry-zone order when setup/price bucket changes. Each order gets a numbered tracker row.
python /Users/waipop/.hermes/scripts/trad_entry_alert.py --target "$TRAD_TELEGRAM_TARGET" >"$tracker_out" 2>"$err_out" || {
  cat "$err_out" >&2
  exit 1
}

# Then notify Telegram only when ai_gate.should_ask_ai=true and no duplicate delivery exists.
exec /Users/waipop/.local/bin/uv run python scripts/ai_alert_if_needed.py --target "$TRAD_TELEGRAM_TARGET"
