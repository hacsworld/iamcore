from future import annotations
import os, httpxdef use_generation() -> str:
    return (os.getenv("USE_GENERATION","none") or "none").lower()def _gen_with_ollama(prompt: str, model: str) -> str:
    try:
        url = "http://127.0.0.1:11434/api/generate"
        with httpx.Client(timeout=60) as c:
            r = c.post(url, json={"model": model, "prompt": prompt, "stream": False})
        r.raise_for_status()
        return (r.json().get("response") or "").strip()
    except Exception as e:
        return f"[gen-error: {e}]"def _gen_with_grok(prompt: str, api_key: str) -> str:
    try:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        grok_model = os.getenv("GROK_MODEL", "grok-4-fast")
        payload = {"model": grok_model, "messages": [{"role":"user","content":prompt}], "temperature":0.3}
        with httpx.Client(timeout=60) as c:
            r = c.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[gen-error: {e}]"def generate_answer(system_hint: str, question: str, context: str) -> str:
    mode = use_generation()
    prompt = f"{system_hint}\n\nQuestion:\n{question}\n\nTrustworthy essence:\n{context}\n\nAnswer clearly:"
    if mode == "ollama":
        model = os.getenv("OLLAMA_MODEL","llama3.1:8b"); return _gen_with_ollama(prompt, model)
    if mode == "grok":
        key = os.getenv("GROK_API_KEY",""); 
        if not key: return "[gen-error: GROK_API_KEY missing]"
        return _gen_with_grok(prompt, key)
    return ""

