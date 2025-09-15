FROM python:3.12-slim  # Grok: bumped to 3.12 for perfENV PYTHONDONTWRITEBYTECODE=1 
    PYTHONUNBUFFERED=1RUN apt-get update && apt-get install -y --no-install-recommends 
    ffmpeg tesseract-ocr libgl1-mesa-glx libglib2.0-0 && \  # Grok: added libglib for cv2
    rm -rf /var/lib/apt/lists/*WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txtCOPY . .EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 
    CMD curl -fsS -H "X-API-Key: ${API_KEY}" http://127.0.0.1:8000/health || exit 1  # Grok: addedCMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]  # Grok: uvicorn direct for workers

