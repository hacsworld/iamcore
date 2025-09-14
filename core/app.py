from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
import random

try:
    from .privacy import load_policy, redact_pii
    from .peers import resonant_exchange
except ImportError:
    from privacy import load_policy, redact_pii
    from peers import resonant_exchange

app = FastAPI(title="HACS Core (Local)", version="2.4")

# === Policies (privacy & peers) ===
POLICY = load_policy()

# === Embeddings ===
model = SentenceTransformer('all-MiniLM-L6-v2')

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

knowledge_embeddings = np.array([model.encode(item["text"]) for item in KNOWLEDGE_BASE])

class IntentRequest(BaseModel):
    text: str

PERSONA_PHRASES = [
    "🔥 Держи свежак!",
    "😎 Вот так это делается!",
    "✨ Всё сходится.",
    "💡 Подкинул идею на резонансе!",
    "🚀 Поехали просто и по делу.",
    "👌 Лаконично и чётко.",
]

def style_response(payload: dict, tone: str = "friendly") -> dict:
    styled = dict(payload)
    styled["style"] = random.choice(PERSONA_PHRASES)
    styled["persona"] = {"tone": tone, "brevity": "concise", "emoji": True}
    return styled

def cosine_similarity(query_embedding, knowledge_embeddings):
    q = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    k = knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9)
    return np.dot(k, q)

@app.post("/act")
async def process_intent(request: IntentRequest):
    try:
        # приватная обработка текста: маскируем PII (внутри запроса дальше по пайплайну)
        safe_text = redact_pii(request.text, POLICY)

        q_emb = model.encode(safe_text)
        sims = cosine_similarity(q_emb, knowledge_embeddings)
        top_idx = np.argsort(sims)[-3:][::-1]

        results = [{"text": KNOWLEDGE_BASE[i]["text"], "similarity": float(sims[i])} for i in top_idx]
        best = float(sims[top_idx[0]]) if len(top_idx) else 0.0

        status = "EXECUTE" if best > 0.6 else "REFINE"
        base = {
            "status": status,
            "resonance": {
                "purity": best,
                "decay": float(1.0 - best),
                "gain": 0.9,
                "strength": float(best * 0.9),
            },
            "context": results,
            "local": True,
        }

        # === Авто-обмен по резонансу (без подтверждений) ===
        # Если уверенность ниже порога политики — пробуем «обмен с пирамии».
        if POLICY.peers_enabled and best < POLICY.peers_resonance_threshold:
            px = resonant_exchange(safe_text, results, max_peers=POLICY.peers_max_peers)
            base["peers"] = {
                "auto_exchange": True,
                "used_peers": int(px.get("used_peers", 0)),
                "hints": px.get("hints", []),
            }
            # Если пировые подсказки есть — усилим контекст и поднимем статус до EXECUTE-lite
            if base["peers"]["used_peers"] > 0 and status == "REFINE":
                base["status"] = "EXECUTE_HINTS"

        return style_response(base)

    except Exception as e:
        return style_response({"status": "ERROR", "error": str(e), "local": True}, tone="confident")

@app.get("/health")
async def health_check():
    return {
        "status": "OK",
        "service": "HACS Local Core",
        "version": "2.4",
        "model": "all-MiniLM-L6-v2",
        "policy": {
            "peers_enabled": POLICY.peers_enabled,
            "resonance_threshold": POLICY.peers_resonance_threshold
        }
    }

if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

