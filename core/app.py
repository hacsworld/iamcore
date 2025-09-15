from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import os, time

APP_VERSION = "3.4.0-prod-lite"
START_TS = time.time()

app = FastAPI(title="Resonance Core", version=APP_VERSION)

API_KEY = os.getenv("API_KEY", "changeme")

def guard(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "Invalid API key")

class ChatReq(BaseModel):
    text: str

@app.get("/health")
def health(_: bool = guard()):
    return {
        "status": "OK",
        "version": APP_VERSION,
        "uptime_sec": int(time.time() - START_TS),
    }

@app.get("/metrics")
def metrics(_: bool = guard()):
    return {"items": 0, "recent": []}

@app.post("/chat")
def chat(req: ChatReq, _: bool = guard()):
    # простой эхо-ответ, чтобы smoke-тестам было с чем поговорить
    txt = (req.text or "").strip()
    return {"status": "EXECUTE", "answer": f"_echo_: {txt}"}

