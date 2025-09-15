#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://127.0.0.1:8000}"
KEY="${API_KEY:-changeme}"

cecho(){ printf "\033[1;32m%s\033[0m\n" "$*"; }
fail(){ printf "\033[1;31mFAIL:\033[0m %s\n" "$*" >&2; exit 1; }

# ждём, пока приложение действительно поднимется
cecho "→ wait app boot"
for i in $(seq 1 30); do
  if curl -fsS -H "X-API-Key: $KEY" "$API/health" >/dev/null; then
    break
  fi
  sleep 2
  [[ $i -eq 30 ]] && fail "health (timeout)"
done

cecho "→ HEALTH"
curl -fsS -H "X-API-Key: $KEY" "$API/health" | grep -q '"OK"' || fail "health"

cecho "→ METRICS"
curl -fsS -H "X-API-Key: $KEY" "$API/metrics" >/dev/null || fail "metrics"

cecho "→ CHAT"
curl -fsS -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"text":"ping"}' "$API/chat" >/dev/null || fail "chat"

cecho "✓ SANITY OK"

