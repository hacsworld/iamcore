from __future__ import annotations
from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional
import os, time

from sentence_transformers import SentenceTransformer
from .memory import ResonanceMemory
from .resonance import EssenceDistiller
from .router import route

API_KEY = os.getenv("API_KEY","changeme")

ALLOWED_ORIGINS = [
    "http://localhost","http://127.0.0.1","http://localhost:3000",
    "https://hacs.world","https://www.hacs.world","https://yourbrand.su","https://www.yourbrand.su"
]

app = FastAPI(title="HACS Core Lite", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def require_key(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        from fastapi import HTTPException
        raise HTTPException(401, detail="Invalid API key")
    return True

# Embeddings
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
MEMORY = ResonanceMemory(dim=len(model.encode("ok")))
DISTILLER = EssenceDistiller(embedder=lambda x: model.encode(x))

class DispatchReq(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class ChatReq(BaseModel):
    text: str
    humor: Optional[bool] = True
    spice: Optional[str] = None

@app.get("/ping")
async def ping(dep: bool = Depends(require_key)):
    return {"ok": True, "ts": int(time.time())}

@app.get("/capabilities")
async def caps(dep: bool = Depends(require_key)):
    return {
        "app":"HACS Core Lite","version":"0.1.0",
        "capabilities":[
            {"id":"g.chat","title":"Chat","commands":["/ask","/translate"]},
            {"id":"g.pay","title":"G-Pay","commands":["/wallet","/deposit","/withdraw"]},
            {"id":"g.market","title":"G-Market","commands":["/market","/search"]}
        ]
    }

@app.post("/events/dispatch")
async def events_dispatch(req: DispatchReq, dep: bool = Depends(require_key)):
    ctx = req.context or {}
    res = route(req.text, ctx, model, MEMORY, DISTILLER)
    return {"status":"OK", **res}

# совместимость: /chat → тот же роутер
@app.post("/chat")
async def chat(req: ChatReq, dep: bool = Depends(require_key)):
    res = route(req.text, {"lang":"ru"}, model, MEMORY, DISTILLER)
    text = ""
    for m in res["messages"]:
        if m.get("role")=="assistant": text = m["text"]; break
    return {"status":"OK","answer":text}
