FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# curl нужен для HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr libgl1 libglib2.0-0 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD curl -fsS -H "X-API-Key: ${API_KEY}" http://127.0.0.1:8000/health || exit 1

CMD ["python","-m","uvicorn","app:app","--host","0.0.0.0","--port","8000","--workers","2"]
