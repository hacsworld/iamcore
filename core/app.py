from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
from typing import List, Dict, Any
import os

app = FastAPI(title="HACS Core (Local)", version="2.3")

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Simple in-memory knowledge base with embeddings
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
    {"text": "Translate languages in real-time"}
]

# Precompute embeddings
knowledge_embeddings = np.array([model.encode(item["text"]) for item in KNOWLEDGE_BASE])

# Initialize Resonance Memory
try:
    from .self_learn import ResonanceMemory
except ImportError:
    from self_learn import ResonanceMemory

MEMORY = ResonanceMemory(dim=knowledge_embeddings.shape[1], k=8, save_every=5)

# ---------- NEW: file readers ----------
try:
    from .readers import sniff_and_read
except Exception:
    from readers import sniff_and_read

# ---------- Models ----------
class IntentRequest(BaseModel):
    text: str

# ---------- Utils ----------
def cosine_similarity(query_embedding, knowledge_embeddings):
    """Compute cosine similarity between query and knowledge base"""
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    knowledge_norm = knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9)
    similarities = np.dot(knowledge_norm, query_norm)
    return similarities

def _ingest_text_payload(filename: str, raw_text: str, tag: str) -> Dict[str, Any]:
    """
    Чанкуем текст и кладём в локальную память (MEMORY).
    Ограничение: ~20 чанков по ~1500 символов.
    """
    raw = (raw_text or "").strip()
    if not raw:
        return {"filename": filename, "ingested_chunks": 0, "approx_chars": 0}

    step = 1500
    limit = 1500 * 20
    ingested = 0
    for i in range(0, min(len(raw), limit), step):
        ch = raw[i:i+step]
        emb = model.encode(ch)
        score = min(0.99, 0.5 + len(ch) / 5000.0)
        MEMORY.learn(f"[{tag}] {filename}: {ch[:120]}", emb, score)
        ingested += 1

    return {"filename": filename, "ingested_chunks": ingested, "approx_chars": len(raw)}

# ---------- Core endpoints ----------
@app.post("/act")
async def process_intent(request: IntentRequest):
    """Process user intent with local AI"""
    try:
        # Generate embedding for query
        query_embedding = model.encode(request.text)

        # Find most relevant knowledge
        similarities = cosine_similarity(query_embedding, knowledge_embeddings)
        top_indices = np.argsort(similarities)[-3:][::-1]  # Top 3 results

        results = []
        for idx in top_indices:
            results.append({
                "text": KNOWLEDGE_BASE[idx]["text"],
                "similarity": float(similarities[idx])
            })

        # Simple resonance scoring
        best_match = similarities[top_indices[0]] if len(top_indices) > 0 else 0.0
        status = "EXECUTE" if best_match > 0.6 else "REFINE"

        # Learn from this interaction
        MEMORY.learn(request.text, query_embedding, float(best_match))

        return {
            "status": status,
            "resonance": {
                "purity": float(best_match),
                "decay": float(1.0 - best_match),
                "gain": 0.9,
                "strength": float(best_match * 0.9)
            },
            "context": results,
            "local": True
        }

    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "local": True
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "OK",
        "service": "HACS Local Core",
        "version": "2.3",
        "model": "all-MiniLM-L6-v2"
    }

@app.get("/memory/stats")
async def memory_stats():
    """Get resonance memory statistics"""
    return MEMORY.stats()

# ---------- NEW: ingest endpoints ----------
@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...), tag: str = Form(default="generic")):
    """
    Принимает один файл (multipart/form-data), парсит текст, встраивает в память.
    Возвращает короткий отчёт.
    """
    data = await file.read()
    kind, text = sniff_and_read(file.filename, data)
    if not (text or "").strip():
        return {"status": "EMPTY", "kind": kind, "bytes": len(data), "filename": file.filename}

    res = _ingest_text_payload(file.filename, text, tag)
    return {"status": "OK", "kind": kind, **res}

@app.post("/ingest/batch")
async def ingest_batch(files: List[UploadFile] = File(...), tag: str = Form(default="generic")):
    """
    Принимает несколько файлов (multipart/form-data) — 'files' может содержать 1..N эл-тов.
    """
    results = []
    for f in files:
        data = await f.read()
        kind, text = sniff_and_read(f.filename, data)
        if not (text or "").strip():
            results.append({
                "filename": f.filename,
                "kind": kind,
                "ingested_chunks": 0,
                "approx_chars": 0
            })
            continue
        res = _ingest_text_payload(f.filename, text, tag)
        results.append({"kind": kind, **res})
    return {"status": "OK", "files": results}

@app.post("/ingest/url")
async def ingest_url(url: str = Form(...), tag: str = Form(default="generic")):
    """
    Подтягивает файл по URL, парсит и встраивает. Без внешних облаков.
    """
    import urllib.request
    from urllib.parse import urlparse
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = resp.read()
            # угадать имя файла из URL
            name = os.path.basename(urlparse(url).path) or "remote.bin"
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "url": url}

    kind, text = sniff_and_read(name, data)
    if not (text or "").strip():
        return {"status": "EMPTY", "kind": kind, "bytes": len(data), "filename": name}

    res = _ingest_text_payload(name, text, tag)
    return {"status": "OK", "kind": kind, **res}

@app.get("/memory/files/stats")
async def memory_files_stats():
    """Прокидываем статистику кластеров — реюзим MEMORY.stats()."""
    return MEMORY.stats()

# ---------- Entrypoint ----------
if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
# ...твой app.py код выше...

import pathlib

AUTO_PATHS = [
    pathlib.Path.home() / "Documents",
    pathlib.Path.home() / "Downloads",
    pathlib.Path.home() / "Pictures",
    pathlib.Path.home() / "Desktop"
]

@app.on_event("startup")
async def auto_bootstrap():
    print("📂 Scanning local storage for files...")
    for base in AUTO_PATHS:
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            try:
                data = f.read_bytes()
                kind, text = sniff_and_read(f.name, data)
                if (text or "").strip():
                    _ingest_text_payload(f.name, text, "auto")
                    print(f"  [+] Ingested {f}")
            except Exception as e:
                print(f"  [!] Skip {f}: {e}")
    print("✅ Bootstrap complete.")

# ---------- Entrypoint ----------
if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
