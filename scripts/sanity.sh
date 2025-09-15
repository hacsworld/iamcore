#!/usr/bin/env bash
set -e

echo "+ wait app boot"
sleep 5

echo "+ health (with retries)"
for i in {1..15}; do
  if curl -fsS -H "X-API-Key: testkey" http://127.0.0.1:8000/health; then
    echo "HEALTH CHECK PASSED"
    exit 0
  fi
  echo "retry $i..."
  sleep 2
done

echo "FAIL: health"
exit 1
