#!/usr/bin/env bash
set -euo pipefail

API="${API:-http://127.0.0.1:8000}"
KEY="${API_KEY:-changeme}"

echo "→ wait app boot"
# подождем чуть-чуть, чтобы uvicorn успел подняться
sleep "${BOOT_WAIT:-5}"

echo "→ health (with retries)"
# 20 попыток по 1с ( ~20с общего ожидания )
for i in $(seq 1 20); do
  if curl -fsS -H "X-API-Key: $KEY" "$API/health" >/dev/null; then
    ok=1; break
  fi
  sleep 1
done
[ "${ok:-0}" -eq 1 ] || { echo "FAIL: health"; exit 1; }

echo "→ metrics"
curl -fsS -H "X-API-Key: $KEY" "$API/metrics" >/dev/null

echo "→ /docs"
curl -fsS "$API/docs" >/dev/null

echo "→ chat smoke"
curl -fsS -H "Content-Type: application/json" -H "X-API-Key: $KEY" \
  -d '{"text":"Привет! Что умеешь?","humor":false}' "$API/chat" >/dev/null

echo "✓ SANITY OK"
