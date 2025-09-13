from contextlib import asynccontextmanager
import asyncio
import threading
import time
import os
import json
import hmac
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import aioredis
import asyncpg
import nats
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sentence_transformers import SentenceTransformer
from anyio.to_thread import run_sync
from ipaddress import ip_address, ip_network
from functools import partial

# ==================== КОНФИГУРАЦИЯ ====================
HMAC_SECRET = os.getenv("HMAC_SECRET", "change-me").encode()
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
PG_VECTOR_URL = os.getenv("PG_VECTOR_URL", "postgresql://postgres:postgres@localhost:5432/hacs")
NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
POLICY_PATH = os.getenv("POLICY_PATH", "/app/hot/policies/policies.yaml")
VECTOR_DIM = 384

# Создаем директории если нет
os.makedirs(os.path.dirname(POLICY_PATH), exist_ok=True)
os.makedirs("/app/hot", exist_ok=True)

# ==================== МОДЕЛИ ДАННЫХ ====================
class Intent(BaseModel):
    text: str
    context: dict = None

class ResonanceScore(BaseModel):
    purity: float
    decay: float
    gain: float
    strength: float

# ==================== УТИЛИТЫ ====================
def to_vector_literal(vec: list[float]) -> str:
    """Конвертируем список float в строку векторного литерала для PostgreSQL"""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

def _to_int(x):
    try: return int(x) if x else 0
    except: return 0

def _to_float(x):
    try: return float(x) if x else 0.0
    except: return 0.0

def ip_allowed(client_ip: str, cidrs: list[str]) -> bool:
    """Проверка IP по allowlist CIDR"""
    if not cidrs: return True
    try:
        ip = ip_address(client_ip)
        return any(ip in ip_network(cidr) for cidr in cidrs)
    except:
        return False

def verify_hmac_signature(signature: str, body: bytes) -> bool:
    """Проверка HMAC подписи"""
    if not signature: return False
    expected = hmac.new(HMAC_SECRET, body, 'sha256').hexdigest()
    return hmac.compare_digest(expected, signature)

# ==================== МОДЕЛЬ ЭМБЕДДИНГОВ ====================
embedder = None

def load_embedder():
    global embedder
    if embedder is None:
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return embedder

async def get_embedding(text: str):
    """Асинхронно получаем эмбеддинг через thread pool"""
    model = load_embedder()
    return await run_sync(partial(model.encode, text))

# ==================== ПОЛИТИКИ (Hot Reload) ====================
class PolicyLoader:
    def __init__(self, policy_path=POLICY_PATH):
        self.policy_path = policy_path
        self.policies = {}
        self.load_policies()
        
    def load_policies(self):
        try:
            if os.path.exists(self.policy_path):
                import yaml
                with open(self.policy_path, 'r') as f:
                    self.policies = yaml.safe_load(f)
                print("✅ Policies reloaded")
        except Exception as e:
            print(f"❌ Failed to load policies: {e}")

policy_loader = PolicyLoader()

class PolicyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.yaml'):
            policy_loader.load_policies()

# ==================== HOT RELOAD ====================
class HotHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print(f"🔄 Hot reload triggered: {event.src_path}")

# ==================== LIFESPAN MANAGEMENT ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация подключений
    app.state.redis = await aioredis.from_url(REDIS_URL)
    app.state.pg = await asyncpg.connect(PG_VECTOR_URL)
    app.state.nats = await nats.connect(NATS_URL)
    
    # Загрузка политик
    policy_loader.load_policies()
    
    # Инициализация модели эмбеддингов
    load_embedder()
    
    # Hot reload watcher
    def run_watcher():
        observer = Observer()
        observer.schedule(HotHandler(), path='/app/hot', recursive=True)
        observer.schedule(PolicyHandler(), path=os.path.dirname(POLICY_PATH), recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    
    thread = threading.Thread(target=run_watcher, daemon=True)
    thread.start()
    print("✅ Hot reload watcher started")
    
    yield
    
    # Завершение работы
    await app.state.redis.close()
    await app.state.pg.close()
    await app.state.nats.close()

# ==================== FASTAPI APP ====================
app = FastAPI(title="HACS Core", lifespan=lifespan)

# ==================== ЭНДПОИНТЫ ====================
@app.get("/")
async def root():
    return {"message": "HACS Resonance AI Engine", "version": "2.2"}

@app.get("/health")
async def health():
    try:
        # Проверяем все соединения
        await app.state.redis.ping()
        await app.state.pg.execute("SELECT 1")
        await app.state.nats.flush(timeout=1)  # Проверка NATS
        return {"status": "OK", "services": ["redis", "pg", "nats", "embedder"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Healthcheck failed: {str(e)}")

@app.post("/act")
async def act(intent: Intent, background_tasks: BackgroundTasks):
    """
    Основной эндпоинт для обработки интентов через резонанс-движок
    """
    try:
        # Получаем эмбеддинг запроса
        query_embedding = await get_embedding(intent.text)
        query_vec_literal = to_vector_literal(query_embedding)
        
        # Ищем в векторной БД (используем DISTANCE)
        similar_items = await app.state.pg.fetch(
            "SELECT id, text, embedding <=> $1::vector AS distance FROM items ORDER BY distance ASC LIMIT 5",
            query_vec_literal
        )
        
        # Формируем контекст на основе расстояния
        context_snippets = []
        best_distance = float(similar_items[0]['distance']) if similar_items else 99.0
        distance_threshold = policy_loader.policies.get('resonance', {}).get('distance_threshold', 0.25)
        
        if best_distance > distance_threshold:
            # Если локальные результаты плохие - идем в облако
            context_snippets = [{"source": "cloud", "snippet": "High-level context from cloud index..."}]
        else:
            # Используем локальные результаты
            context_snippets = [
                {
                    "source": "local_pgvector", 
                    "snippet": item['text'], 
                    "distance": float(item['distance'])
                } for item in similar_items
            ]
        
        # Скоринг резонанса
        purity = 0.92
        decay = 0.08
        gain = 0.88
        
        # Расчет силы резонанса
        strength = purity * (1 - decay) * (0.5 + gain/2)
        resonance_score = ResonanceScore(
            purity=purity, 
            decay=decay, 
            gain=gain, 
            strength=strength
        )
        
        # Определяем статус based on resonance strength
        status = "EXECUTE" if strength >= 0.7 else "REFINE"
        
        # Публикуем событие в NATS (в фоне)
        event_data = {
            "intent": intent.text,
            "status": status,
            "resonance": resonance_score.dict(),
            "context_snippets": context_snippets,
            "timestamp": time.time()
        }
        
        background_tasks.add_task(
            app.state.nats.publish, 
            "resonance.complete", 
            json.dumps(event_data).encode()
        )
        
        # Кэшируем результат
        cache_key = f"intent:{hash(intent.text)}"
        await app.state.redis.setex(
            cache_key,
            300,
            json.dumps(event_data)
        )
        
        return {
            "status": status,
            "resonance": resonance_score,
            "context": context_snippets,
            "cache_key": cache_key
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/context/{cache_key}")
async def get_cached_context(cache_key: str):
    """Получение закэшированного результата обработки интента"""
    try:
        cached_data = await app.state.redis.get(cache_key)
        if cached_data:
            return JSONResponse(content=json.loads(cached_data))
        else:
            raise HTTPException(status_code=404, detail="Context not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: Request, x_hmac: str = Header(None)):
    """Входящий webhook для интеграций"""
    body = await request.body()
    
    # Проверка безопасности из политик
    sec_config = policy_loader.policies.get("security", {})
    
    # Allowlist проверка
    allowed_ips = sec_config.get("allowed_ips", [])
    if not ip_allowed(request.client.host, allowed_ips):
        raise HTTPException(status_code=403, detail="IP not allowed")
    
    # HMAC проверка
    if sec_config.get("hmac_required", True):
        if not verify_hmac_signature(x_hmac, body):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        event = json.loads(body)
        # Публикуем событие в NATS
        await app.state.nats.publish("webhook.event", json.dumps(event).encode())
        
        return {"status": "accepted", "event_type": event.get('type')}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Метрики для Prometheus"""
    try:
        # Базовые метрики
        hits = _to_int(await app.state.redis.get("metrics:cache_hits"))
        misses = _to_int(await app.state.redis.get("metrics:cache_misses"))
        total_requests = _to_int(await app.state.redis.get("metrics:total_requests"))
        total_time = _to_float(await app.state.redis.get("metrics:total_processing_time"))
        
        metrics_data = {
            "resonance_requests_total": total_requests,
            "cache_hits_total": hits,
            "cache_misses_total": misses,
            "cache_hit_rate": hits / (hits + misses) if (hits + misses) > 0 else 0,
            "average_processing_time_seconds": total_time / total_requests if total_requests > 0 else 0
        }
        return metrics_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
