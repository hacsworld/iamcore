from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
from typing import List, Dict, Any

app = FastAPI(title="HACS Core (Local)", version="2.2")

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

class IntentRequest(BaseModel):
    text: str

def cosine_similarity(query_embedding, knowledge_embeddings):
    """Compute cosine similarity between query and knowledge base"""
    query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    knowledge_norm = knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9)
    similarities = np.dot(knowledge_norm, query_norm)
    return similarities

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
        best_match = similarities[top_indices[0]] if len(top_indices) > 0 else 0
        status = "EXECUTE" if best_match > 0.6 else "REFINE"
        
        # Learn from this interaction
        MEMORY.learn(request.text, query_embedding, best_match)
        
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
        "version": "2.2",
        "model": "all-MiniLM-L6-v2"
    }

@app.get("/memory/stats")
async def memory_stats():
    """Get resonance memory statistics"""
    return MEMORY.stats()

if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

