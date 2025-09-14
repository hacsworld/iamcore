from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
import random  # <— для харизматичных фраз

app = FastAPI(title="HACS Core (Local)", version="2.3")

# === Embeddings ===
model = SentenceTransformer('all-MiniLM-L6-v2')

# Простейшая локальная база знаний
KNOWLEDGE_BASE = [
    {"text": "Open settings and configure preferences"},
    {"text": "Create a new note or document"},
    {"text": "Pay invoices and manage billing"},
    {"text": "Control smart home devices and lights"},
    {"text": "Schedule appointments and meetings"},
    {"text": "Search the web for information"},
    {"text": "Play music and control playback"},
    {"text": "Set reminders and timers"},
    {"text": "Send messages and emails"},
    {"text": "Translate languages in real-time"},
]

# Предрасчёт эмбеддингов для базы
knowledge_embeddings = np.array([model.encode(item["text"]) for item in KNOWLEDGE_BASE])

class IntentRequest(BaseModel):
    text: str

def cosine_similarity(query_embedding, knowledge_embeddings):
    """Cosine similarity между запросом и базой знаний"""
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    knowledge_norm = knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9)
    similarities = np.dot(knowledge_norm, query_norm)
    return similarities

# === Харизма / стиль ответа ===
PERSONA_PHRASES = [
    "🔥 Держи свежак!",
    "😎 Вот так это делается!",
    "✨ Проверил — всё сходится!",
    "💡 Подкинул идею на резонансе!",
    "🚀 Поехали по простому и по делу.",
    "👌 Лаконично и чётко.",
]

def style_response(payload: dict, tone: str = "friendly") -> dict:
    """
    Оборачиваем сухой результат в «живой» ответ.
    Ничего не ломаем — просто добавляем поля 'style' и 'persona'.
    """
    styled = dict(payload)  # копия
    styled["style"] = random.choice(PERSONA_PHRASES)
    styled["persona"] = {
        "tone": tone,           # friendly | chill | confident — на будущее
        "brevity": "concise",   # лаконично
        "emoji": True,          # можно выключить позже политикой
    }
    return styled

@app.post("/act")
async def process_intent(request: IntentRequest):
    """
    Обрабатываем интент локально:
    - эмбеддинг запроса
    - поиск ближайших смыслов (top-3)
    - простая «резонансная» оценка
    - харизматичная обёртка ответа
    """
    try:
        # 1) Вектор запроса
        query_embedding = model.encode(request.text)

        # 2) Сходство с базой
        similarities = cosine_similarity(query_embedding, knowledge_embeddings)
        top_indices = np.argsort(similarities)[-3:][::-1]  # Top-3

        results = []
        for idx in top_indices:
            results.append({
                "text": KNOWLEDGE_BASE[idx]["text"],
                "similarity": float(similarities[idx]),
            })

        # 3) Резонанс
        best_match = float(similarities[top_indices[0]]) if len(top_indices) > 0 else 0.0
        status = "EXECUTE" if best_match > 0.6 else "REFINE"

        base_payload = {
            "status": status,
            "resonance": {
                "purity": best_match,
                "decay": float(1.0 - best_match),
                "gain": 0.9,
                "strength": float(best_match * 0.9),
            },
            "context": results,
            "local": True,
        }

        # 4) Харизма ✨
        return style_response(base_payload, tone="friendly")

    except Exception as e:
        error_payload = {
            "status": "ERROR",
            "error": str(e),
            "local": True,
        }
        return style_response(error_payload, tone="confident")

@app.get("/health")
async def health_check():
    """Health-check для CI/мониторинга"""
    return {
        "status": "OK",
        "service": "HACS Local Core",
        "version": "2.3",
        "model": "all-MiniLM-L6-v2",
    }

if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
