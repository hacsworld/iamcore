from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import time

app = FastAPI(title="HACS Pair Server", version="1.0")

PAIR_SECRET = os.getenv("PAIR_SECRET", "dev-secret")

class PairRequest(BaseModel):
    Code: str
    PubKey: str
    Platform: str

class PairResponse(BaseModel):
    DeviceID: str
    Token: str
    WSURL: str
    ExpiresIn: int | None = None

@app.post("/pair/finish", response_model=PairResponse)
def pair_finish(req: PairRequest):
    if len(req.Code) != 6 or not req.Code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pairing code")

    device_id = f"dev_{req.PubKey[:12]}"
    token = f"token_{int(time.time())}"
    ws_url = os.getenv("WS_URL", "wss://ws.hacs.world/agent")

    return PairResponse(
        DeviceID=device_id,
        Token=token,
        WSURL=ws_url,
        ExpiresIn=3600,
    )
