from __future__ import annotations
from typing import List, Dict, Any
import re, numpy as np

STOP = set("и а но или если то тогда иначе для от из в на при с без как это тот те что их ваш мой наш ты мы они не ни yes no the a an and or".split())

def _norm(v: np.ndarray)->np.ndarray:
    n = float(np.linalg.norm(v) + 1e-9); return v / n

def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[\.\!\?\n])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]

class EssenceDistiller:
    def __init__(self, embedder, alpha=0.65, beta=0.45, gamma=0.35):
        self.embed = embedder
        self.alpha, self.beta, self.gamma = alpha, beta, gamma
        self.core_vec = self.embed("Law of Core Resonance. Focus on signal, strip noise, compress to essence, then act.")

    def _cos(self, a,b): return float((_norm(a)*_norm(b)).sum())

    def _noise(self, s:str)->float:
        words = re.findall(r"\w+", s.lower())
        if not words: return 1.0
        stop_frac = sum(1 for w in words if w in STOP)/max(1,len(words))
        return 0.7*stop_frac + 0.3*min(1.0, len(s)/3000.0)

    def score_sentence(self, qv: np.ndarray, s: str) -> float:
        sv = self.embed(s)
        return self.alpha*self._cos(qv, sv) + self.beta*self._cos(self.core_vec, sv) - self.gamma*self._noise(s)

    def distill(self, query: str, text: str, top_k=4, max_chars=400) -> Dict[str, Any]:
        sents = split_sentences(text)
        if not sents: return {"essence":"","snippets":[]}
        qv = self.embed(query)
        scored = sorted(sents, key=lambda s: self.score_sentence(qv,s), reverse=True)
        out, total = [], 0
        for s in scored:
            if s in out: continue
            if total + len(s) > max_chars: continue
            out.append(s); total += len(s)
            if len(out) >= top_k: break
        return {"essence": " ".join(out).strip(), "snippets": out}
