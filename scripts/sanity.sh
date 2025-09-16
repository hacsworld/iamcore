#!/usr/bin/env bash
set -euo pipefail
API=${API:-http://127.0.0.1:8000}
KEY=${API_KEY:-changeme}

curl -fsS "$API/docs" >/dev/null
curl -fsS -H "X-API-Key: $KEY" "$API/ping" | grep -q '"ok": true'
curl -fsS -H "X-API-Key: $KEY" "$API/capabilities" >/dev/null
curl -fsS -H "X-API-Key: $KEY" -H "Content-Type: application/json"   -d '{"text":"/wallet balance","context":{"ui":"dev"}}' "$API/events/dispatch" >/dev/null
echo "SANITY OK"
