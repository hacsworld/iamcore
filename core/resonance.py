from future import annotations
from typing import List, Dict, Any
import re
import numpy as npSTOP_EN = set("""a an the and or but if then else for to from of in on at by with without as is are was were be been being do does did
this that these those it its their your my our you we they i me him her his hers them us not no nor so very just""".split())
STOP_RU = set("""и а но или если то тогда иначе для от из в на при с без как это тот те что их ваш мой наш ты мы они
не ни да нет так очень лишь просто""".split())CORE_SEED = ("Law of Core Resonance: Focus on signal, strip noise, compress to essence, then act. "
             "Ask first when uncertain. Fly to cloud only for essence.")def _norm(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v) + 1e-9); return v / ndef cos(a: np.ndarray, b: np.ndarray) -> float:
    return float((_norm(a) * _norm(b)).sum())def noise_score(text: str) -> float:
    words = re.findall(r"\w+", text.lower())
    if not words: return 1.0
    L = len(words)
    stop_frac = (sum(1 for w in words if w in STOP_EN or w in STOP_RU) / max(1, L))
    avg_len = sum(len(w) for w in words) / max(1, L)
    from collections import Counter
    c = Counter(words); repet = max(c.values()) / max(1, L)
    return 0.6stop_frac + 0.2(avg_len/8.0) + 0.4*repetdef split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]class EssenceDistiller:
    def init(self, embedder, alpha: float = 0.65, beta: float = 0.45, gamma: float = 0.35):
        self.embed = embedder; self.alpha, self.beta, self.gamma = alpha, beta, gamma
        self.core_vec = self.embed(CORE_SEED)def score_sentence(self, q_vec: np.ndarray, s: str) -> float:
    sv = self.embed(s)
    return self.alpha*cos(q_vec, sv) + self.beta*cos(self.core_vec, sv) - self.gamma*noise_score(s)

def distill(self, query: str, text: str, top_k: int = 6, max_chars: int = 800) -> Dict[str, Any]:
    sents = split_sentences(text)
    if not sents: return {"essence": "", "snippets": [], "scores": []}
    qv = self.embed(query)
    scored = [(s, self.score_sentence(qv, s)) for s in sents]
    scored.sort(key=lambda x: x[1], reverse=True)
    out, scs, total = [], [], 0
    for s, sc in scored:
        if s in out or total + len(s) > max_chars: continue
        out.append(s); scs.append(sc); total += len(s)
        if len(out) >= top_k: break
    return {"essence":" ".join(out).strip(), "snippets":out, "scores":scs}

