# HACS Local Core

FastAPI сервис локального ядра (векторный поиск + простая резонанс-оценка).

## Запуск
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Endpoints:
- `GET /health`
- `POST /act` -> `{ "text": "..." }`
