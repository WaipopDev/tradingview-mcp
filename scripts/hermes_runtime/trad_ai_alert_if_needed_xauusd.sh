#!/usr/bin/env bash
set -euo pipefail
cd /Users/waipop/MainWTN/Hermes/trad

# Explicit Telegram alert runner. No hardcoded target: set TRAD_TELEGRAM_TARGET
# or pass --target to scripts/ai_alert_if_needed.py. Use --no-send for tests.
exec /Users/waipop/.local/bin/uv run python scripts/ai_alert_if_needed.py "$@"
