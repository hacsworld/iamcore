# HACS Core Lite — Human AGI Core Symbiosis (local orchestrator)

Локальный оркестратор: дистиллирует суть (essence), навешивает Закон Резонанса (policy),
и праймит любую внешнюю модель. Фронт вызывает единый вход `/events/dispatch`.

## Быстрый старт (без Docker)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# при желании выставь USE_GENERATION=grok|openai|ollama
uvicorn core.app:app --host 127.0.0.1 --port 8000 --reload
