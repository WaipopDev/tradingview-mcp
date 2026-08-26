#!/usr/bin/env bash
set -euo pipefail
cd /Users/waipop/MainWTN/Hermes/trad
exec /Users/waipop/.local/bin/uv run python scripts/collect_trad_signal.py
