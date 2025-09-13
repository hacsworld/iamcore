# core/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# системные зависимости по минимуму
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# код приложения
COPY app.py /app/app.py

# путь к политикам (папку создаём; файл необязателен — приложение само переживёт его отсутствие)
ENV POLICY_PATH=/app/hot/policies/policies.yaml
RUN mkdir -p /app/hot/policies

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
