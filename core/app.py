from fastapi import FastAPI

app = FastAPI(title="HACS Core")

@app.get("/")
async def root():
    return {"message": "HACS Resonance AI Engine", "version": "2.2"}
