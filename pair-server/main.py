from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import os, time, json, secrets, jwt, redis

# ------------------------ Config ------------------------
JWT_SECRET = os.getenv("PAIR_JWT_SECRET", "dev-secret")
JWT_TTL    = int(os.getenv("PAIR_JWT_TTL", "3600"))  # seconds
WS_URL     = os.getenv("WS_URL", "wss://ws.hacs.world/agent")
REDIS_URL  = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.from_url(REDIS_URL, decode_responses=True)

app = FastAPI(title="HACS Pair Server", version="2.0")

# ------------------------ Models ------------------------
def _alias(field_name: str):  # принимает и lower, и CamelCase ключи
    return Field(alias=field_name)

class PairStartRequest(BaseModel):
    # можно расширить (например, user_id), пока пусто
    pass

class PairFinishRequest(BaseModel):
    code: str = _alias("Code")
    pubkey: str = _alias("PubKey")
    platform: str = _alias("Platform")

    class Config:
        populate_by_name = True
        extra = "ignore"

class PairFinishResponse(BaseModel):
    device_id: str
    token: str
    ws_url: str
    expires_in: Optional[int] = None

# ------------------------ Helpers ------------------------
def _redis_key(code: str) -> str:
    return f"pair:code:{code}"

def _mk_device_id(pubkey_hex: str) -> str:
    return f"dev_{pubkey_hex[:12]}"

def _sign_jwt(device_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": device_id,
        "iat": now,
        "exp": now + JWT_TTL,
        "scope": "agent"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

# ------------------------ API ------------------------
@app.post("/pair/start")
def pair_start(_: PairStartRequest):
    code = f"{secrets.randbelow(10**6):06d}"  # 6-значный
    # храним «пустышку» (или user context) с TTL 5 минут
    r.setex(_redis_key(code), 300, json.dumps({"issued_at": int(time.time())}))
    return {"code": code, "ttl": 300}

@app.post("/pair/finish", response_model=PairFinishResponse)
def pair_finish(req: PairFinishRequest):
    if len(req.code) != 6 or not req.code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pairing code")

    key = _redis_key(req.code)
    data = r.get(key)
    if not data:
        raise HTTPException(status_code=400, detail="Code expired or invalid")

    # одноразовый — удаляем
    r.delete(key)

    device_id = _mk_device_id(req.pubkey)
    token = _sign_jwt(device_id)
    return PairFinishResponse(
        device_id=device_id,
        token=token,
        ws_url=WS_URL,
        expires_in=JWT_TTL
    )

@app.get("/health")
def health():
    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {
        "status": "OK" if redis_ok else "DEGRADED",
        "redis": redis_ok,
        "ws_url": WS_URL,
        "jwt_ttl": JWT_TTL
    }

        Token=token,
        WSURL=ws_url,
        ExpiresIn=3600,
    )
