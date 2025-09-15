from dotenv import load_dotenv
load_dotenv()from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn, os, pathlib, time, hashlib, datetime, threading, json
import numpy as npfrom sentence_transformers import SentenceTransformer
from generation import generate_answer, use_generation
from humor import HumorEngineapp = FastAPI(title="Resonance Core (HACS)", version="3.4-prod")  # Grok: updated version===== Config & Auth =====API_KEY = os.getenv("API_KEY","")
ALLOWLIST = [d.strip() for d in (os.getenv("ALLOWLIST","") or "").split(",") if d.strip()]
AUTOSAVE_SEC = int(os.getenv("AUTOSAVE_SEC","30") or "30")
ps_start = time.time()def require_key(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, detail="Invalid API key")
    return True===== Embeddings =====model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')===== Memory =====try:
    from .memory import ResonanceMemory
except Exception:
    from memory import ResonanceMemory
MEMORY = ResonanceMemory(dim=len(model.encode("ok")), k=8, save_every=100)===== Readers / Essence / Cloud =====try:
    from .readers import sniff_and_read
except Exception:
    from readers import sniff_and_readtry:
    from .resonance import EssenceDistiller
except Exception:
    from resonance import EssenceDistiller
DISTILLER = EssenceDistiller(embedder=lambda x: model.encode(x))try:
    from .cloud_gate import CloudGateEssence
except Exception:
    from cloud_gate import CloudGateEssence
CLOUD_ALLOW = ALLOWLIST or ["wikipedia.org","docs.python.org","ffmpeg.org","arxiv.org","github.com","x.ai"]
CLOUD = CloudGateEssence(embedder=lambda x: model.encode(x), allow_domains=CLOUD_ALLOW, timeout_s=10.0)===== Vault / Video =====try:
    from .storage_vault import export_vault, import_vault
except Exception:
    from storage_vault import export_vault, import_vaulttry:
    from .video_tools import make_slideshow_from_images, concat_videos
except Exception:
    from video_tools import make_slideshow_from_images, concat_videos===== Simple KB =====KB = [
    "Open settings and configure preferences",
    "Create a new note or document",
    "Pay invoices and manage billing",
    "Control smart home devices and lights",
    "Schedule appointments and meetings",
    "Search the web for information",
    "Play music and control playback",
    "Set reminders and timers",
    "Send messages and emails",
    "Translate languages in real-time"
]
KB_EMB = np.vstack([model.encode(x) for x in KB]).astype(np.float32)
def _norm(v): return v / (np.linalg.norm(v)+1e-9)
def _kb_best(qv: np.ndarray) -> Dict[str, Any]:
    sims = (KB_EMB / (np.linalg.norm(KB_EMB, axis=1, keepdims=True)+1e-9)) @ _norm(qv)
    i = int(np.argmax(sims))
    return {"text": KB[i], "score": float(sims[i])}===== Policies =====TAU_ASK = 0.55
TAU_EXEC = 0.68
FACT_TRIGGERS = ["сегодня","вчера","цена","курс","версия","релиз","новости","deadline","срок","изменения","update",
                 "latest","today","yesterday","price","version","release","news"]---------- Health / Metrics ----------@app
.get("/health")
async def health(dep: bool = Depends(require_key)):
    return {
        "status":"OK","version":"3.4-prod","model":"paraphrase-multilingual-MiniLM-L12-v2",
        "mem": MEMORY.stats(), "allowlist": CLOUD_ALLOW, "uptime_sec": int(time.time()-ps_start),
        "gen": use_generation()
    }@app
.get("/metrics")
async def metrics(dep: bool = Depends(require_key)):
    s = MEMORY.stats()
    return {"items": s["items"], "recent": s["recent"], "gen_mode": use_generation(),
            "allowlist": CLOUD_ALLOW, "autosave_sec": AUTOSAVE_SEC}---------- Setup: Portfolio ----------@app
.post("/setup/portfolio")
async def setup_portfolio(
    profession: str = Form(...),
    interests: str = Form(default=""),
    use_cloud: bool = Form(default=False),
    note: str = Form(default=""),
    dep: bool = Depends(require_key)
):
    tags = ["core","profile"] + [s.strip() for s in interests.split(",") if s.strip()]
    base_text = f"User core: profession={profession}; interests={interests}; note={note}"
    MEMORY.learn(base_text, model.encode(base_text), 0.92, tags=tags)
    return {"status":"OK","message":"Portfolio seeded","tags":tags,"cloud_suggested":bool(use_cloud)}---------- Quick scan ----------AUTO_PATHS = [
    pathlib.Path.home() / "Documents",
    pathlib.Path.home() / "Downloads",
    pathlib.Path.home() / "Pictures",
    pathlib.Path.home() / "Desktop",
]@app
.post("/setup/portfolio/scan")
async def portfolio_scan(tag: str = Form(default="portfolio"), dep: bool = Depends(require_key)):
    scanned, ing = 0, 0
    for base in AUTO_PATHS:
        if not base.exists(): continue
        for f in base.rglob(""):
            if not f.is_file(): continue
            try:
                data = f.read_bytes()
                kind, text = sniff_and_read(f.name, data)
                if (text or "").strip():
                    raw = text.strip()
                    step = 1500
                    for i in range(0, len(raw), step):
                        ch = raw[i:i+step]
                        MEMORY.learn(f"[{tag}] {f.name}: {ch[:120]}", model.encode(ch), min(0.99,0.5+len(ch)/5000.0), tags=["file",tag])
                        ing += 1
                        if i > 150020: break
                scanned += 1
            except Exception:
                continue
    return {"status":"OK","scanned_files":scanned,"ingested_chunks":ing}---------- Ingest ----------@app
.post("/ingest")
async def ingest(file: UploadFile = File(...), tag: str = Form(default="generic"), dep: bool = Depends(require_key)):
    data = await file.read()
    kind, text = sniff_and_read(file.filename, data)
    if not (text or "").strip():
        return {"status": "EMPTY", "kind": kind, "bytes": len(data), "filename": file.filename}
    step = 1500; raw = text.strip(); ing = 0
    for i in range(0, len(raw), step):
        ch = raw[i:i+step]
        MEMORY.learn(f"[{tag}] {file.filename}: {ch[:120]}", model.encode(ch), min(0.99,0.5+len(ch)/5000.0), tags=["file", tag])
        ing += 1
        if i > 1500*20: break
    return {"status": "OK", "kind": kind, "filename": file.filename, "ingested_chunks": ing, "approx_chars": len(raw)}@app
.post("/ingest/batch")
async def ingest_batch(files: List[UploadFile] = File(...), tag: str = Form(default="generic"), dep: bool = Depends(require_key)):
    res = []
    for f in files:
        data = await f.read()
        kind, text = sniff_and_read(f.filename, data)
        ing = 0
        if (text or "").strip():
            raw = text.strip(); step = 1500
            for i in range(0, len(raw), step):
                ch = raw[i:i+step]
                MEMORY.learn(f"[{tag}] {f.filename}: {ch[:120]}", model.encode(ch), min(0.99,0.5+len(ch)/5000.0), tags=["file", tag])
                ing += 1
                if i > 1500*20: break
        res.append({"filename": f.filename, "kind": kind, "ingested_chunks": ing, "approx_chars": len(text or "")})
    return {"status": "OK", "files": res}@app
.post("/ingest/url")
async def ingest_url(url: str = Form(...), tag: str = Form(default="generic"), dep: bool = Depends(require_key)):
    import urllib.request
    from urllib.parse import urlparse
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            data = resp.read()
            name = os.path.basename(urlparse(url).path) or "remote.bin"
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "url": url}
    kind, text = sniff_and_read(name, data)
    if not (text or "").strip():
        return {"status": "EMPTY", "kind": kind, "bytes": len(data), "filename": name}
    step = 1500; raw = text.strip(); ing = 0
    for i in range(0, len(raw), step):
        ch = raw[i:i+step]
        MEMORY.learn(f"[{tag}] {name}: {ch[:120]}", model.encode(ch), min(0.99,0.5+len(ch)/5000.0), tags=["file", tag])
        ing += 1
        if i > 1500*20: break
    return {"status":"OK","kind":kind,"filename":name,"ingested_chunks":ing,"approx_chars":len(raw)}---------- Chat (ask-first / humor / gen / cloud) ----------class ChatRequest(BaseModel):
    text: str
    target_lang: Optional[str] = None
    humor: Optional[bool] = True
    spice: Optional[str] = None  # None|friendly|spicydef _needs_fresh(q: str) -> bool:
    ql = q.lower()
    return any(t in ql for t in FACT_TRIGGERS)def _clarify(q: str, kb_hit: str) -> str:
    return f"Уточни, пожалуйста: где/когда/какой именно? (Понял как: «{kb_hit}»)"def maybe_humorize(text: str, req: ChatRequest) -> str:
    mode_env = os.getenv("HUMOR_MODE","friendly").lower()
    if not req.humor or mode_env == "off": return text
    mode = (req.spice or mode_env).lower()
    region = os.getenv("REGION","ru-RU")
    h = HumorEngine(region=region, mode=("spicy" if mode=="spicy" else "friendly"),
                    name=os.getenv("HUMOR_USER_NAME","друг"))
    return h.decorate(text)@app
.post("/chat")
async def chat(req: ChatRequest, dep: bool = Depends(require_key)):
    try:
        q = req.text.strip()
        if not q: return {"status":"ASK","ask":"Напиши запрос"}
        qv = model.encode(q)    kb = _kb_best(qv)
    mem_hits = MEMORY.search(qv, k=5)

    rmax = max(kb["score"], float(mem_hits[0]["score"]) if mem_hits else 0.0)

    if rmax < TAU_ASK:
        out = _clarify(q, kb["text"])
        return {"status":"ASK","ask": maybe_humorize(out, req), "why":{"rmax":rmax,"policy":"ask-first"}}

    if _needs_fresh(q):
        ce = CLOUD.gate_essence(q, k_search=6, k_docs=3, top_k_sent=6)
        ess_context = "\n".join([f"- {d['title']}: {d['essence']}" for d in ce["distilled"] if d.get("essence")])
        for d in ce["distilled"]:
            ess = (d.get("essence") or "").strip()
            if ess: MEMORY.learn(f"[essence] {d['hash']} {d.get('title','')[:60]}", model.encode(ess), 0.8, tags=["cloud","essence"])
        base = (ce["distilled"][0]["essence"] if ce["distilled"] and ce["distilled"][0]["essence"]
                else f"Источники подтверждены ({len(ce['distilled'])}); суть сохранена.")
        final = base
        if use_generation() != "none":
            sys_hint = "Be concise and accurate. Use only the provided essence; do not fabricate."
            gen = generate_answer(sys_hint, q, ess_context[:2000])
            if gen and not gen.startswith("[gen-error"): final = gen
        return {
            "status":"CLOUD",
            "answer": maybe_humorize(final, req),
            "sources":[{"url":d["url"],"title":d["title"]} for d in ce["distilled"]],
            "why":{"rmax":rmax,"policy":"essence-only+gen" if use_generation()!="none" else "essence-only"}
        }

    ctx_text = " ".join([h["label"] for h in mem_hits[:3]]) or kb["text"]
    distilled = DISTILLER.distill(q, ctx_text, top_k=4, max_chars=400)
    answer = distilled["essence"] or kb["text"]
    if use_generation() != "none" and rmax >= TAU_EXEC:
        sys_hint = "You answer briefly and clearly. Use the provided essence faithfully. If unsure, say you are unsure."
        gen = generate_answer(sys_hint, q, answer)
        if gen and not gen.startswith("[gen-error"): answer = gen
    MEMORY.learn(f"[chat] {q[:80]}", qv, min(0.99, rmax), tags=["chat"])
    status = "EXECUTE" if rmax >= TAU_EXEC else "REFINE"
    return {"status":status, "answer": maybe_humorize(answer, req), "why":{"rmax":rmax,"policy":"local","kb":kb,"mem_top":mem_hits[:3]}}
except Exception as e:
    return {"status":"ERROR","error":str(e)}    ---------- Cloud Essence (manual) ----------class CloudReq(BaseModel):
    text: str
    allow: Optional[List[str]] = None
    k_docs: int = 3
    top_k_sent: int = 6@app
.post("/cloud/accelerate")
async def cloud_accelerate(req: CloudReq, dep: bool = Depends(require_key)):
    cg = CloudGateEssence(embedder=lambda x: model.encode(x), allow_domains=(req.allow or CLOUD_ALLOW))
    res = cg.gate_essence(req.text, k_search=max(3,req.k_docs*2), k_docs=req.k_docs, top_k_sent=req.top_k_sent)
    ing = 0
    for d in res["distilled"]:
        ess = (d.get("essence") or "").strip()
        if not ess: continue
        MEMORY.learn(f"[essence] {d['hash']} {d.get('title','')[:60]}", model.encode(ess), 0.8, tags=["cloud","essence"])
        ing += 1
    return {"status":"OK","ingested":ing,"sources":[{"url":d["url"],"title":d["title"]} for d in res["distilled"]]}---------- Vault ----------class VaultExportReq(BaseModel):
    passphrase: str
    path: Optional[str] = None@app
.post("/vault/export")
async def vault_export(req: VaultExportReq, dep: bool = Depends(require_key)):
    dump = MEMORY.dump()
    path = req.path or "./vault/vault.zip"
    p = export_vault(path, req.passphrase, dump, meta={"version":1,"count":len(dump)})
    def _iter():
        with open(p, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk: break
                yield chunk
    headers = {"Content-Disposition": f'attachment; filename="{os.path.basename(p)}"'}
    return StreamingResponse(_iter(), media_type="application/zip", headers=headers)class VaultImportReq(BaseModel):
    passphrase: str
    path: str@app
.post("/vault/import")
async def vault_import(req: VaultImportReq, dep: bool = Depends(require_key)):
    items = import_vault(req.path, req.passphrase)
    added = MEMORY.load(items); MEMORY.save()
    return {"status":"OK","imported":added}---------- Video ----------class SlideShowReq(BaseModel):
    images: List[str]
    out_path: Optional[str] = None
    duration_per_image: float = 2.0
    kenburns: bool = True
    captions: Optional[List[str]] = None
    bgm_path: Optional[str] = Noneclass ConcatReq(BaseModel):
    videos: List[str]
    out_path: Optional[str] = Noneimport cv2, sounddevice as sd, soundfile as sf, threading as _t@app
.post("/video/make/slideshow")
async def video_make_slideshow(req: SlideShowReq, dep: bool = Depends(require_key)):
    try:
        out = req.out_path or f"./outputs/VID_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
        path = make_slideshow_from_images(images=req.images, out_path=out,
                                          duration_per_image=req.duration_per_image,
                                          kenburns=req.kenburns, captions=req.captions, bgm_path=req.bgm_path)
        return {"status":"OK","path":str(path)}
    except Exception as e:
        return {"status":"ERROR","error":str(e)}@app
.post("/video/make/concat")
async def video_make_concat(req: ConcatReq, dep: bool = Depends(require_key)):
    try:
        out = req.out_path or f"./outputs/VID_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
        path = concat_videos(req.videos, out)
        return {"status":"OK","path":str(path)}
    except Exception as e:
        return {"status":"ERROR","error":str(e)}_REC_STATE = {
    "camera": {"thread": None, "stop": False, "path": None, "fps": 30, "size": (1280,720)},
    "mic":    {"thread": None, "stop": False, "path": None, "rate": 48000, "channels": 1}
}def _record_camera_worker(device_index: int, out_path: str, fps: int, size: tuple):
    cap = cv2.VideoCapture(device_index)
    if size:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0]); cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
    cap.set(cv2.CAP_PROP_FPS, fps)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    writer = cv2.VideoWriter(out_path, fourcc, fps, size)
    try:
        while not _REC_STATE["camera"]["stop"]:
            ret, frame = cap.read()
            if not ret: break
            frame = cv2.resize(frame, size)
            writer.write(frame)
    finally:
        writer.release(); cap.release()@app
.post("/video/record/camera/start")
async def camera_start(device_index: int = 0, fps: int = 30, width: int = 1280, height: int = 720,
                       out_path: str = Form(default=""), dep: bool = Depends(require_key)):
    cap = cv2.VideoCapture(device_index)
    ok = bool(cap and cap.isOpened())
    if cap: cap.release()
    if not ok:
        return {"status":"ERROR","error":f"Camera device {device_index} busy/unavailable"}
    if REC_STATE["camera"]["thread"] and REC_STATE["camera"]["thread"].is_alive():
        return {"status":"ERROR","error":"Camera is already recording"}
    path = out_path or f"./outputs/CAM{datetime.datetime.now():%Y%m%d%H%M%S}.mp4"
    _REC_STATE["camera"].update({"stop": False, "path": path, "fps": fps, "size": (width, height)})
    t = _t.Thread(target=_record_camera_worker, args=(device_index, path, fps, (width, height)), daemon=True)
    _REC_STATE["camera"]["thread"] = t; t.start()
    return {"status":"OK","path":path,"fps":fps,"size":[width,height]}@app
.post("/video/record/camera/stop")
async def camera_stop(dep: bool = Depends(require_key)):
    if not _REC_STATE["camera"]["thread"]:
        return {"status":"ERROR","error":"Camera recorder not running"}
    _REC_STATE["camera"]["stop"] = True
    _REC_STATE["camera"]["thread"].join(timeout=5)
    path = _REC_STATE["camera"]["path"]
    _REC_STATE["camera"]["thread"] = None; _REC_STATE["camera"]["stop"] = False
    return {"status":"OK","path":path}def _record_mic_worker(out_path: str, rate: int, channels: int):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with sf.SoundFile(out_path, mode='w', samplerate=rate, channels=channels, subtype='PCM_16') as file:
        def callback(indata, frames, time, status):
            if _REC_STATE["mic"]["stop"]:
                raise sd.CallbackStop
            file.write(indata.copy())
        with sd.InputStream(samplerate=rate, channels=channels, callback=callback):
            while not _REC_STATE["mic"]["stop"]:
                sd.sleep(100)@app
.post("/video/record/mic/start")
async def mic_start(rate: int = 48000, channels: int = 1, out_path: str = Form(default=""), dep: bool = Depends(require_key)):
    if REC_STATE["mic"]["thread"] and REC_STATE["mic"]["thread"].is_alive():
        return {"status":"ERROR","error":"Mic is already recording"}
    path = out_path or f"./outputs/MIC{datetime.datetime.now():%Y%m%d%H%M%S}.wav"
    _REC_STATE["mic"].update({"stop": False, "path": path, "rate": rate, "channels": channels})
    t = _t.Thread(target=_record_mic_worker, args=(path, rate, channels), daemon=True)
    _REC_STATE["mic"]["thread"] = t; t.start()
    return {"status":"OK","path":path,"rate":rate,"channels":channels}@app
.post("/video/record/mic/stop")
async def mic_stop(dep: bool = Depends(require_key)):
    if not _REC_STATE["mic"]["thread"]:
        return {"status":"ERROR","error":"Mic recorder not running"}
    _REC_STATE["mic"]["stop"] = True
    _REC_STATE["mic"]["thread"].join(timeout=5)
    path = _REC_STATE["mic"]["path"]
    _REC_STATE["mic"]["thread"] = None; _REC_STATE["mic"]["stop"] = False
    return {"status":"OK","path":path}@app
.get("/video/status")
async def video_status(dep: bool = Depends(require_key)):
    def _alive(name):
        th = _REC_STATE[name]["thread"]
        return bool(th and th.is_alive())
    return {"camera":{"recording":_alive("camera"),"path":_REC_STATE["camera"]["path"]},
            "mic":{"recording":_alive("mic"),"path":_REC_STATE["mic"]["path"]}}---------- Memory stats ----------@app
.get("/memory/stats")
async def mem_stats(dep: bool = Depends(require_key)):
    return MEMORY.stats()---------- Mini UI ----------@app
.get("/ui/chat", response_class=HTMLResponse)
async def ui_chat():
    return """
<!doctype html><html><head><meta charset="utf-8"><title>Resonance Chat</title></head><body style="font-family:system-ui;margin:24px;max-width:840px">
<h2>Resonance Chat (3.4 Prod)</h2>  <!-- Grok: updated version -->
<form onsubmit="send(event)">
  <textarea id="q" rows="4" style="width:100%" placeholder="Напишите запрос..."></textarea><br/>
  <label><input type="checkbox" id="humor" checked> Humor</label>
  <select id="spice"><option value="">auto</option><option>friendly</option><option>spicy</option></select>
  <button>Отправить</button>
</form>
<pre id="out" style="white-space:pre-wrap;background:#111;color:#0f0;padding:12px;border-radius:8px;margin-top:12px"></pre>
<script>
async function send(e){e.preventDefault();
  let q = document.getElementById('q').value;
  let humor = document.getElementById('humor').checked;
  let spice = document.getElementById('spice').value;
  let r = await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json','X-API-Key':'changeme'},
    body: JSON.stringify({text:q, humor:humor, spice:spice||null})});
  let t = await r.json();
  document.getElementById('out').textContent = JSON.stringify(t,null,2);
}
</script>
</body></html>
    """

---------- Startup ----------@app
.on_event("startup")
async def bootstrap():
    os.makedirs("./outputs", exist_ok=True)
    os.makedirs("./vault", exist_ok=True)
    os.makedirs("./state", exist_ok=True)
    n = MEMORY.load_from_disk()
    print(f" memory loaded: {n} items")
    def autosaver():
        while True:
            time.sleep(max(5, AUTOSAVE_SEC))
            try: MEMORY.save()
            except Exception: pass
    threading.Thread(target=autosaver, daemon=True).start()
    print(" Resonance Core ready. http://127.0.0.1:8000/docs  |  /ui/chat")if name == "main":
    print(" Starting Resonance Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
