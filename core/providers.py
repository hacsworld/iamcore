from __future__ import annotations
import os, httpx

def use_generation()->str:
    return (os.getenv("USE_GENERATION","none") or "none").lower()

# ---- GROK
def _grok(system: str, question: str, context: str)->str:
    key = os.getenv("GROK_API_KEY","")
    if not key: return f"[grok-missing-key] essence:\n{context}"
    url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    payload = {"model": os.getenv("GROK_MODEL","grok-4-fast"),
               "messages":[{"role":"system","content":system},
                           {"role":"user","content":f"{question}\n\nEssence:\n{context}"}],
               "temperature":0.2}
    with httpx.Client(timeout=60) as c:
        r = c.post(url, headers=headers, json=payload); r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

# ---- OpenAI
def _openai(system: str, question: str, context: str)->str:
    key = os.getenv("OPENAI_API_KEY","")
    if not key: return f"[openai-missing-key] essence:\n{context}"
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}
    payload = {"model": os.getenv("OPENAI_MODEL","gpt-4o-mini"),
               "messages":[{"role":"system","content":system},
                           {"role":"user","content":f"{question}\n\nEssence:\n{context}"}],
               "temperature":0.2}
    with httpx.Client(timeout=60) as c:
        r = c.post(url, headers=headers, json=payload); r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

# ---- Ollama (локальный)
def _ollama(system: str, question: str, context: str)->str:
    url = "http://127.0.0.1:11434/api/generate"
    model = os.getenv("OLLAMA_MODEL","llama3.1:8b")
    prompt = f"{system}\n\nQuestion:\n{question}\n\nEssence:\n{context}\n\nAnswer briefly:"
    try:
        with httpx.Client(timeout=60) as c:
            r = c.post(url, json={"model": model, "prompt": prompt, "stream": False})
            r.raise_for_status(); return (r.json().get("response") or "").strip()
    except Exception as e:
        return f"[ollama-error: {e}] essence:\n{context}"

def ask(system: str, question: str, context: str)->str:
    m = use_generation()
    if m=="grok": return _grok(system, question, context)
    if m=="openai": return _openai(system, question, context)
    if m=="ollama": return _ollama(system, question, context)
    # none → отдаём essence как ответ (для оффлайна/тестов)
    return context or "..."
