# core/generation.py
from __future__ import annotations

import os
import json
import httpx

"""
Lightweight text generation adapter for local (Ollama) and Grok (xAI).

ENV:
  USE_GENERATION = none|ollama|grok
  OLLAMA_MODEL   = llama3.1:8b
  GROK_API_KEY   = sk-...
  GROK_MODEL     = grok-4-fast
"""

def use_generation() -> str:
    """Return normalized generation backend name."""
    return (os.getenv("USE_GENERATION", "none") or "none").strip().lower()


# -------- Ollama --------
def _gen_with_ollama(prompt: str, model: str, timeout_s: float = 60.0) -> str:
    url = "http://127.0.0.1:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        with httpx.Client(timeout=timeout_s) as c:
            r = c.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        return (data.get("response") or "").strip()
    except Exception as e:
        return f"[gen-error: ollama: {e}]"


# -------- Grok (xAI) --------
def _gen_with_grok(prompt: str, api_key: str, model: str, timeout_s: float = 60.0) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    try:
        with httpx.Client(timeout=timeout_s) as c:
            r = c.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        # expected shape: {"choices":[{"message":{"content": "..."}}, ...]}
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception as e:
        # include minimal debug info but avoid leaking secrets
        try:
            err_detail = r.text[:200] if "r" in locals() and isinstance(r.text, str) else ""
        except Exception:
            err_detail = ""
        return f"[gen-error: grok: {e}; {err_detail}]"


# -------- Public API --------
def generate_answer(system_hint: str, question: str, context: str) -> str:
    """
    Compose a single prompt and call the configured backend.
    Returns "" if USE_GENERATION=none.
    """
    backend = use_generation()
    if backend == "none":
        return ""

    # unified prompt
    prompt = (
        f"{system_hint}\n\n"
        f"Question:\n{question}\n\n"
        f"Trustworthy essence:\n{context}\n\n"
        f"Answer clearly:"
    )

    if backend == "ollama":
        model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        return _gen_with_ollama(prompt, model)

    if backend == "grok":
    api_key = os.getenv("GROK_API_KEY", "")
    if not api_key:
        return "[gen-error: GROK_API_KEY missing]"
    model = os.getenv("GROK_MODEL", "grok-4-fast")
    return _gen_with_grok(prompt, api_key, model)

    # unknown backend value: behave as none
    return ""

        if not key: return "[gen-error: GROK_API_KEY missing]"
        return _gen_with_grok(prompt, key)
    return ""

