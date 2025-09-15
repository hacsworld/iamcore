# core/app.py
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
import uvicorn
from typing import List, Dict, Any, Optional
import os, pathlib, time

app = FastAPI(title="HACS Core (Local)", version="2.4")

# ===== Embedding model (multilingual) =====
# Поддерживает 50+ языков: один векторное пространство для всех
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# ===== Built-in simple KB =====
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
knowledge_embeddings = np.array([model.encode(item["text"]) for item in KNOWLEDGE_BASE])

# ===== Resonance Memory =====
try:
    from .self_learn import ResonanceMemory
except ImportError:
    from self_learn import ResonanceMemory

MEMORY = ResonanceMemory(dim=knowledge_embeddings.shape[1], k=8, save_every=5)

# ===== Readers (files → text) =====
try:
    from .readers import sniff_and_read
except Exception:
    from readers import sniff_and_read

# ===== Utils =====
def cosine_similarity(query_embedding, knowledge_embeddings):
    qn = query_embedding / (np.linalg.norm(query_embedding) + 1e-9)
    kn = knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9)
    return np.dot(kn, qn)

def _ingest_text_payload(filename: str, raw_text: str, tag: str) -> Dict[str, Any]:
    """
    Режем текст на чанки и кладём в локальную память.
    Без лимитов на смысл, но чтобы не взорвать RAM, делаем разумный шаг.
    При желании можешь убрать ограничение limit.
    """
    raw = (raw_text or "").strip()
    if not raw:
        return {"filename": filename, "ingested_chunks": 0, "approx_chars": 0}

    step = 1500
    limit = max(len(raw), 1500)  # по сути — весь текст
    ingested = 0

    for i in range(0, min(len(raw), limit), step):
        ch = raw[i:i+step]
        emb = model.encode(ch)
        score = min(0.99, 0.5 + len(ch) / 5000.0)
        MEMORY.learn(f"[{tag}] {filename}: {ch[:120]}", emb, score)
        ingested += 1

    return {"filename": filename, "ingested_chunks": ingested, "approx_chars": len(raw)}

# ===== Classic intent endpoint (/act) =====
class IntentRequest(BaseModel):
    text: str

@app.post("/act")
async def process_intent(request: IntentRequest):
    try:
        q_emb = model.encode(request.text)
        sims = cosine_similarity(q_emb, knowledge_embeddings)
        top_indices = np.argsort(sims)[-3:][::-1]

        results = [{"text": KNOWLEDGE_BASE[i]["text"], "similarity": float(sims[i])} for i in top_indices]
        best = float(sims[top_indices[0]]) if len(top_indices) else 0.0
        status = "EXECUTE" if best > 0.6 else "REFINE"

        MEMORY.learn(request.text, q_emb, best)

        return {
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
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "local": True}

# ===== Health & memory =====
@app.get("/health")
async def health_check():
    return {"status": "OK", "service": "HACS Local Core", "version": "2.4",
            "model": "paraphrase-multilingual-MiniLM-L12-v2"}

@app.get("/memory/stats")
async def memory_stats():
    return MEMORY.stats()

# ===== Multilingual chat (/chat) =====
# Язык входа → детект, ответ → язык пользователя (или target_lang)
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 42

# Оффлайн-перевод (опционально)
_HAS_ARGOS = False
try:
    import argostranslate.package as argos_pkg
    import argostranslate.translate as argos_tr
    _HAS_ARGOS = True
except Exception:
    _HAS_ARGOS = False

def _ensure_argos_pair(src: str, tgt: str):
    if not _HAS_ARGOS:
        return
    try:
        pairs = argos_tr.get_installed_languages()
        for L in pairs:
            if L.code == src:
                for to in L.translation_languages:
                    if to.code == tgt:
                        return
        available = argos_pkg.get_available_packages()
        for p in available:
            if p.from_code == src and p.to_code == tgt:
                argos_pkg.install_from_path(p.download())
                break
    except Exception:
        pass

def _translate(text: str, src: str, tgt: str) -> str:
    if not _HAS_ARGOS or src == tgt or not text.strip():
        return text
    try:
        _ensure_argos_pair(src, tgt)
        langs = argos_tr.get_installed_languages()
        Lsrc = next((L for L in langs if L.code == src), None)
        if not Lsrc:
            return text
        translator = next((t for t in Lsrc.translation_languages if t.code == tgt), None)
        if not translator:
            return text
        return translator.translate(text)
    except Exception:
        return text

# Каталог команд (интенты) — для действий
COMMANDS = [
    {"id": "open_settings", "text": "Open settings and configure preferences"},
    {"id": "create_note", "text": "Create a new note or document"},
    {"id": "pay_billing", "text": "Pay invoices and manage billing"},
    {"id": "control_smart_home", "text": "Control smart home devices and lights"},
    {"id": "schedule_meeting", "text": "Schedule appointments and meetings"},
    {"id": "web_search", "text": "Search the web for information"},
    {"id": "play_music", "text": "Play music and control playback"},
    {"id": "set_reminder", "text": "Set reminders and timers"},
    {"id": "send_message", "text": "Send messages and emails"},
    {"id": "translate_rt", "text": "Translate languages in real time"},
]
_command_embeddings = np.array([model.encode(c["text"]) for c in COMMANDS])

def _top_command(query: str):
    q = model.encode(query)
    qn = q / (np.linalg.norm(q) + 1e-9)
    kn = _command_embeddings / (np.linalg.norm(_command_embeddings, axis=1, keepdims=True) + 1e-9)
    sims = np.dot(kn, qn)
    idx = int(np.argmax(sims))
    return COMMANDS[idx], float(sims[idx]), q

class ChatRequest(BaseModel):
    text: str
    target_lang: Optional[str] = None

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        # входной язык
        try:
            src_lang = (detect(req.text) or "en").split("-")[0]
        except Exception:
            src_lang = "en"

        # ближайший интент и эмбеддинг запроса
        cmd, score, q_emb = _top_command(req.text)

        # топ-3 из KB
        sims_kb = np.dot(
            knowledge_embeddings / (np.linalg.norm(knowledge_embeddings, axis=1, keepdims=True) + 1e-9),
            q_emb / (np.linalg.norm(q_emb) + 1e-9)
        )
        top_kb_idx = np.argsort(sims_kb)[-3:][::-1]
        kb_hits = [{"text": KNOWLEDGE_BASE[i]["text"], "similarity": float(sims_kb[i])} for i in top_kb_idx]

        # поиск по памяти, если есть
        memory_hits = []
        try:
            if hasattr(MEMORY, "search"):
                for r in MEMORY.search(q_emb, k=5):
                    memory_hits.append({
                        "label": r.get("label") or r.get("text") or "",
                        "score": float(r.get("score", 0.0))
                    })
        except Exception:
            pass

        # базовый ответ (англ), затем переводим
        answer_en = (
            f"Intent: {cmd['id']} (score={score:.2f}).\n"
            f"I understood your request and can act accordingly.\n"
            f"Closest knowledge:\n- " + "\n- ".join(h['text'] for h in kb_hits)
        )
        tgt_lang = (req.target_lang or src_lang or "en").split("-")[0]
        answer_out = _translate(answer_en, "en", tgt_lang)

        # учимся на сообщении
        MEMORY.learn(req.text, q_emb, max(0.0, min(1.0, score)))

        return {
            "status": "OK",
            "lang_in": src_lang,
            "lang_out": tgt_lang,
            "intent": {"id": cmd["id"], "score": score},
            "answer": answer_out,
            "kb": kb_hits,
            "memory_hits": memory_hits,
            "local": True,
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "local": True}

# ===== Ingest endpoints =====
@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...), tag: str = Form(default="generic")):
    data = await file.read()
    kind, text = sniff_and_read(file.filename, data)
    if not (text or "").strip():
        return {"status": "EMPTY", "kind": kind, "bytes": len(data), "filename": file.filename}
    res = _ingest_text_payload(file.filename, text, tag)
    return {"status": "OK", "kind": kind, **res}

@app.post("/ingest/batch")
async def ingest_batch(files: List[UploadFile] = File(...), tag: str = Form(default="generic")):
    results = []
    for f in files:
        data = await f.read()
        kind, text = sniff_and_read(f.filename, data)
        if not (text or "").strip():
            results.append({"filename": f.filename, "kind": kind, "ingested_chunks": 0, "approx_chars": 0})
            continue
        res = _ingest_text_payload(f.filename, text, tag)
        results.append({"kind": kind, **res})
    return {"status": "OK", "files": results}

@app.post("/ingest/url")
async def ingest_url(url: str = Form(...), tag: str = Form(default="generic")):
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
    res = _ingest_text_payload(name, text, tag)
    return {"status": "OK", "kind": kind, **res}

# ===== Auto-scan helpers & endpoints =====
AUTO_PATHS = [
    pathlib.Path.home() / "Documents",
    pathlib.Path.home() / "Downloads",
    pathlib.Path.home() / "Pictures",
    pathlib.Path.home() / "Desktop",
]
INDEX_CACHE: Dict[str, tuple[int, float]] = {}  # path -> (size, mtime)

def _should_ingest(path: pathlib.Path) -> bool:
    try:
        st = path.stat()
        key = str(path.resolve())
        cur = (st.st_size, st.st_mtime)
        prev = INDEX_CACHE.get(key)
        if prev == cur:
            return False
        INDEX_CACHE[key] = cur
        return True
    except Exception:
        return False

def _iter_files(base: pathlib.Path, recursive: bool) -> List[pathlib.Path]:
    if not base.exists() or not base.is_dir():
        return []
    return [p for p in (base.rglob("*") if recursive else base.iterdir()) if p.is_file()]

def _scan_one_file(fpath: pathlib.Path, tag: str) -> Dict[str, Any]:
    try:
        data = fpath.read_bytes()
        kind, text = sniff_and_read(fpath.name, data)
        if not (text or "").strip():
            return {"filename": str(fpath), "kind": kind, "ingested_chunks": 0, "approx_chars": 0}
        res = _ingest_text_payload(fpath.name, text, tag)
        return {"filename": str(fpath), "kind": kind, **res}
    except Exception as e:
        return {"filename": str(fpath), "error": str(e), "kind": "unknown", "ingested_chunks": 0, "approx_chars": 0}

@app.on_event("startup")
async def auto_bootstrap():
    print("📂 Scanning local storage for files...")
    for base in AUTO_PATHS:
        if not base.exists():
            continue
        for f in _iter_files(base, recursive=True):
            if not _should_ingest(f):
                continue
            r = _scan_one_file(f, tag="auto")
            if r.get("ingested_chunks", 0) > 0:
                print(f"  [+] Ingested {f}")
    print("✅ Bootstrap complete.")

@app.post("/ingest/scan")
async def ingest_scan(
    path: str = Form(default=""),       # пусто → AUTO_PATHS
    tag: str = Form(default="auto"),
    recursive: bool = Form(default=True)
):
    started = time.time()
    if path.strip():
        base = pathlib.Path(path).expanduser()
        if not base.exists() or not base.is_dir():
            return {"status": "ERROR", "error": f"Path not found or not a directory: {base}"}
        bases = [base]
    else:
        bases = [p for p in AUTO_PATHS if p.exists()]

    scanned_files = 0
    processed: List[Dict[str, Any]] = []
    for base in bases:
        for f in _iter_files(base, recursive=recursive):
            scanned_files += 1
            if not _should_ingest(f):
                continue
            processed.append(_scan_one_file(f, tag))

    took = round(time.time() - started, 3)
    ingested = sum(1 for r in processed if r.get("ingested_chunks", 0) > 0)
    errors = [r for r in processed if "error" in r]

    return {
        "status": "OK",
        "scanned_dirs": [str(b) for b in bases],
        "scanned_files": scanned_files,
        "ingested_files": ingested,
        "errors": len(errors),
        "took_sec": took,
        "details": processed[:100],  # можно убрать лимит
    }

@app.get("/ingest/autopaths")
async def list_autopaths():
    present = [str(p) for p in AUTO_PATHS if p.exists()]
    missing = [str(p) for p in AUTO_PATHS if not p.exists()]
    return {"present": present, "missing": missing}

# ===== Entrypoint =====
# ====== VIDEO: generation & real-time capture ======
from typing import Optional
import threading, queue, datetime
from pydantic import BaseModel

try:
    from .video_tools import make_slideshow_from_images, concat_videos
except Exception:
    from video_tools import make_slideshow_from_images, concat_videos

# ---------- Models for requests ----------
class SlideShowReq(BaseModel):
    images: List[str]               # список локальных путей к фото
    out_path: Optional[str] = None  # куда сохранить mp4 (по умолчанию core/outputs/VID_YYYYmmdd_HHMMSS.mp4)
    duration_per_image: float = 2.0
    kenburns: bool = True
    captions: Optional[List[str]] = None
    bgm_path: Optional[str] = None  # путь к аудио

class ConcatReq(BaseModel):
    videos: List[str]               # список локальных путей к видео
    out_path: Optional[str] = None

@app.post("/video/make/slideshow")
async def video_make_slideshow(req: SlideShowReq):
    try:
        out = req.out_path or f"./outputs/VID_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
        path = make_slideshow_from_images(
            images=req.images,
            out_path=out,
            duration_per_image=req.duration_per_image,
            kenburns=req.kenburns,
            captions=req.captions,
            bgm_path=req.bgm_path
        )
        return {"status": "OK", "path": str(path)}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

@app.post("/video/make/concat")
async def video_make_concat(req: ConcatReq):
    try:
        out = req.out_path or f"./outputs/VID_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
        path = concat_videos(req.videos, out)
        return {"status": "OK", "path": str(path)}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

# ---------- Camera recorder ----------
import cv2
_REC_STATE = {
    "camera": {"thread": None, "stop": False, "path": None, "fps": 30, "size": (1280,720)},
    "mic":    {"thread": None, "stop": False, "path": None, "rate": 48000, "channels": 1}
}

def _record_camera_worker(device_index: int, out_path: str, fps: int, size: tuple):
    cap = cv2.VideoCapture(device_index)
    if size:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
    cap.set(cv2.CAP_PROP_FPS, fps)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    writer = cv2.VideoWriter(out_path, fourcc, fps, size)

    try:
        while not _REC_STATE["camera"]["stop"]:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, size)
            writer.write(frame)
    finally:
        writer.release()
        cap.release()

@app.post("/video/record/camera/start")
async def camera_start(
    device_index: int = 0,
    fps: int = 30,
    width: int = 1280,
    height: int = 720,
    out_path: str = Form(default="")
):
    if _REC_STATE["camera"]["thread"] and _REC_STATE["camera"]["thread"].is_alive():
        return {"status": "ERROR", "error": "Camera is already recording"}
    path = out_path or f"./outputs/CAM_{datetime.datetime.now():%Y%m%d_%H%M%S}.mp4"
    _REC_STATE["camera"].update({"stop": False, "path": path, "fps": fps, "size": (width, height)})
    t = threading.Thread(target=_record_camera_worker, args=(device_index, path, fps, (width, height)), daemon=True)
    _REC_STATE["camera"]["thread"] = t
    t.start()
    return {"status": "OK", "path": path, "fps": fps, "size": [width, height]}

@app.post("/video/record/camera/stop")
async def camera_stop():
    if not _REC_STATE["camera"]["thread"]:
        return {"status": "ERROR", "error": "Camera recorder not running"}
    _REC_STATE["camera"]["stop"] = True
    _REC_STATE["camera"]["thread"].join(timeout=5)
    path = _REC_STATE["camera"]["path"]
    _REC_STATE["camera"]["thread"] = None
    _REC_STATE["camera"]["stop"] = False
    return {"status": "OK", "path": path}

# ---------- Mic recorder ----------
import sounddevice as sd
import soundfile as sf

def _record_mic_worker(out_path: str, rate: int, channels: int):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with sf.SoundFile(out_path, mode='w', samplerate=rate, channels=channels, subtype='PCM_16') as file:
        def callback(indata, frames, time, status):
            if _REC_STATE["mic"]["stop"]:
                raise sd.CallbackStop
            file.write(indata.copy())
        with sd.InputStream(samplerate=rate, channels=channels, callback=callback):
            while not _REC_STATE["mic"]["stop"]:
                sd.sleep(100)

@app.post("/video/record/mic/start")
async def mic_start(
    rate: int = 48000,
    channels: int = 1,
    out_path: str = Form(default="")
):
    if _REC_STATE["mic"]["thread"] and _REC_STATE["mic"]["thread"].is_alive():
        return {"status": "ERROR", "error": "Mic is already recording"}
    path = out_path or f"./outputs/MIC_{datetime.datetime.now():%Y%m%d_%H%M%S}.wav"
    _REC_STATE["mic"].update({"stop": False, "path": path, "rate": rate, "channels": channels})
    t = threading.Thread(target=_record_mic_worker, args=(path, rate, channels), daemon=True)
    _REC_STATE["mic"]["thread"] = t
    t.start()
    return {"status": "OK", "path": path, "rate": rate, "channels": channels}

@app.post("/video/record/mic/stop")
async def mic_stop():
    if not _REC_STATE["mic"]["thread"]:
        return {"status": "ERROR", "error": "Mic recorder not running"}
    _REC_STATE["mic"]["stop"] = True
    _REC_STATE["mic"]["thread"].join(timeout=5)
    path = _REC_STATE["mic"]["path"]
    _REC_STATE["mic"]["thread"] = None
    _REC_STATE["mic"]["stop"] = False
    return {"status": "OK", "path": path}

@app.get("/video/status")
async def video_status():
    def _alive(name):
        th = _REC_STATE[name]["thread"]
        return bool(th and th.is_alive())
    return {
        "camera": {"recording": _alive("camera"), "path": _REC_STATE["camera"]["path"]},
        "mic": {"recording": _alive("mic"), "path": _REC_STATE["mic"]["path"]}
    }
if __name__ == "__main__":
    print("🚀 Starting HACS Local Core on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
