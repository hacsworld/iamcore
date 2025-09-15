#!/usr/bin/env bash
set -euo pipefail
API=${API:-http://127.0.0.1:8000}
KEY=${API_KEY:-changeme}
cecho(){ printf "\033[1;32m%s\033[0m\n" "$*"; }
fail(){ printf "\033[1;31mFAIL:\033[0m %s\n" "$*" >&2; exit 1; }

cecho "→ HEALTH"
curl -fsS -H "X-API-Key: $KEY" "$API/health" | jq .status | grep -q "OK" || fail "health"

cecho "→ METRICS"
curl -fsS -H "X-API-Key: $KEY" "$API/metrics" >/dev/null || fail "metrics"

cecho "→ CHAT (local)"
curl -fsS -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"text":"Привет, что ты умеешь?","humor":true}' "$API/chat" >/dev/null || fail "chat"

cecho "✓ SANITY OK"
