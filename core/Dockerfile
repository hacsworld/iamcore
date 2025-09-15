FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные пакеты + curl для HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr libgl1 libglib2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Приложение
COPY . .

EXPOSE 8000

# Внутри контейнера дергаем health (ключ можно пробросить переменной окружения)
HEALTHCHECK --interval=20s --timeout=5s --retries=6 \
  CMD curl -fsS -H "X-API-Key: ${API_KEY:-changeme}" http://127.0.0.1:8000/health || exit 1

# ВАЖНО: слушаем 0.0.0.0, иначе наружу не видно
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
