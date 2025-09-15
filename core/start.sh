#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-2}"

if [[ -n "${APP_MODULE:-}" ]]; then
  TARGET="$APP_MODULE"
else
  CANDIDATES=("app:app" "core.app:app" "main:app" "api:app" "src.app:app")
  FOUND=""
  for c in "${CANDIDATES[@]}"; do
    py="${c%%:*}.py"
    if [[ -f "$py" ]] && grep -q "FastAPI(" "$py"; then
      FOUND="$c"
      break
    fi
  done
  if [[ -z "$FOUND" ]]; then
    file="$(grep -RIl --include='*.py' 'FastAPI(' . | head -n1 || true)"
    if [[ -n "$file" ]]; then
      mod="${file#./}"; mod="${mod%.py}"; mod="${mod//\//.}"
      FOUND="${mod}:app"
    fi
  fi
  TARGET="${FOUND:-app:app}"
fi

echo "▶️ Starting uvicorn: ${TARGET} on 0.0.0.0:${PORT} (workers=${WORKERS})"
exec uvicorn "${TARGET}" --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
