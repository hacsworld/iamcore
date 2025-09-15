# лёгкий и надёжный базовый образ
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=2

# системные утилиты для диагностики и curl для HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000
# healthcheck спрашивает наш /health с ключом
HEALTHCHECK --interval=15s --timeout=5s --retries=10 \
  CMD curl -fsS -H "X-API-Key: ${API_KEY:-changeme}" http://127.0.0.1:8000/health || exit 1

# uvicorn слушает 0.0.0.0:8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000","--log-level","info"]
