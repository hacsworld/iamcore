#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-2}"

# Если явно дали модуль — используем его (пример: APP_MODULE=core.app:app)
if [[ -n "${APP_MODULE:-}" ]]; then
  TARGET="$APP_MODULE"
else
  # 1) быстрые известные кандидаты
  CANDIDATES=(
    "app:app"
    "core.app:app"
    "main:app"
    "api:app"
    "src.app:app"
  )

  # 2) попытка найти файл, где создаётся FastAPI()
  if [[ ${#CANDIDATES[@]} -eq 0 ]]; then :; fi
  FOUND=""
  for c in "${CANDIDATES[@]}"; do
    mod="${c%%:*}"; obj="${c##*:}"
    py="${mod//.//}.py"
    if [[ -f "$py" ]] && grep -q "FastAPI(" "$py"; then
      FOUND="$c"; break
    fi
  done

  if [[ -z "$FOUND" ]]; then
    # глубокий поиск любого файла с FastAPI(
    file="$(grep -RIl --include='*.py' 'FastAPI(' . || true | head -n1)"
    if [[ -n "$file" ]]; then
      mod="${file#./}"; mod="${mod%.py}"; mod="${mod//\//.}"
      FOUND="${mod}:app"
    fi
  fi

  TARGET="${FOUND:-app:app}"  # дефолт
fi

echo "▶️ Starting uvicorn: ${TARGET} on 0.0.0.0:${PORT} (workers=${WORKERS})"
exec uvicorn "${TARGET}" --host 0.0.0.0 --port "${PORT}" --workers "${WORKERS}"
