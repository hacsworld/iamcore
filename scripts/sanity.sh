#!/usr/bin/env bash
set -euo pipefail

API=${API:-http://127.0.0.1:8000}
KEY=${API_KEY:-changeme}
SKIP_CLOUD=${SKIP_CLOUD:-0}

cecho(){ printf "\033[1;32m%s\033[0m\n" "$*"; }
fail(){ printf "\033[1;31mFAIL:\033[0m %s\n" "$*" >&2; exit 1; }

cecho "→ HEALTH"
curl -fsS "$API/health" | jq .status | grep -q "OK" || fail "health"

cecho "→ METRICS"
curl -fsS -H "X-API-Key: $KEY" "$API/metrics" >/dev/null || fail "metrics"

cecho "→ UI /docs"
curl -fsS "$API/docs" >/dev/null || fail "docs"

cecho "→ CHAT (local)"
curl -fsS -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"text":"Привет, что ты умеешь?","humor":true}' "$API/chat" >/dev/null || fail "chat"

cecho "→ INGEST small txt"
echo "hello core resonance" > /tmp/hello.txt
curl -fsS -H "X-API-Key: $KEY" -F "file=@/tmp/hello.txt" -F "tag=test" "$API/ingest" | jq .status | grep -q "OK" || fail "ingest"

if [ "$SKIP_CLOUD" != "1" ]; then
  cecho "→ CLOUD essence (allowlist)"
  curl -fsS -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
    -d '{"text":"Latest info about ffmpeg filters","k_docs":2}' "$API/cloud/accelerate" >/dev/null || fail "cloud"
else
  cecho "→ CLOUD essence skipped (SKIP_CLOUD=1)"
fi

cecho "→ VIDEO status"
curl -fsS -H "X-API-Key: $KEY" "$API/video/status" >/dev/null || fail "video-status"

cecho "✓ SANITY OK"
