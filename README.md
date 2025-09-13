# HACS Core — Resonance AI Engine

**Стек:** FastAPI · pgvector · Redis · NATS (JetStream) · SentenceTransformers  
**Фичи:** hot policies, локальный векторный поиск, кэш, события, HMAC/IP allowlist, health/metrics

## Quick start

```bash
cp example.env .env
docker compose -f docker-compose.ai.yml up -d --build
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/act -H "Content-Type: application/json" -d '{"text":"test intent"}'
```

**Endpoints**
- GET / — статус/версия
- GET /health — проверка Redis/PG/NATS/embedder
- POST /act — резонанс-обработка интента
- GET /context/{cache_key} — кэш результата
- POST /webhook — входящая интеграция (HMAC + allowlist)
- GET /metrics — базовые метрики (Prometheus-friendly JSON)

**Policies (hot reload)**  
`hot/policies/policies.yaml`

**Dev tips**
- Локальные эмбеддинги — CPU, завернуты в thread-pool
- В pgvector оператор `<=>` — distance (меньше — лучше)
- Seed примеров вектора в init.sql убран — соблюдайте размерность VECTOR(384)
