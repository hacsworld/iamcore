from future import annotations
from typing import List, Dict, Any, Optional
import time, json, threading, os
import numpy as npdef _norm(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v) + 1e-9)
    return v / nclass ResonanceMemory:
    """Лёгкая векторная память (thread-safe), персистентность в JSON."""
    def init(self, dim: int, k: int = 8, save_every: int = 100):
        self.dim = dim
        self.k = k
        self.save_every = save_every
        self._labels: List[str] = []
        self._vecs: List[np.ndarray] = []
        self._scores: List[float] = []
        self._tags: List[List[str]] = []
        self._ts: List[float] = []
        self._steps = 0
        self._lock = threading.RLock()
        self._persist_path = os.getenv("MEMORY_PATH","./state/memory.json")
        os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)def learn(self, label: str, vec: np.ndarray, score: float, tags: Optional[List[str]] = None):
    with self._lock:
        self._labels.append(str(label))
        self._vecs.append(vec.astype(np.float32))
        self._scores.append(float(max(0.0, min(1.0, score))))
        self._tags.append(list(tags or []))
        self._ts.append(time.time())
        self._steps += 1

def search(self, query_vec: np.ndarray, k: Optional[int] = None) -> List[Dict[str, Any]]:
    with self._lock:
        if not self._vecs:
            return []
        k = k or self.k
        q = _norm(query_vec.astype(np.float32))
        M = np.vstack([_norm(v) for v in self._vecs])
        sims = (M @ q) * (0.5 + 0.5 * np.array(self._scores, dtype=np.float32))
        idx = np.argsort(sims)[-k:][::-1]
        return [{
            "label": self._labels[i],
            "score": float(sims[i]),
            "tags": self._tags[i],
            "ts": float(self._ts[i]),
        } for i in idx]

def stats(self) -> Dict[str, Any]:
    with self._lock:
        return {
            "items": len(self._labels), "dim": self.dim, "k": self.k,
            "recent": self._labels[-5:][::-1] if self._labels else [],
        }

def dump(self) -> List[Dict[str, Any]]:
    with self._lock:
        return [{
            "label": self._labels[i],
            "score": self._scores[i],
            "tags": self._tags[i],
            "ts": self._ts[i],
            "vec": self._vecs[i].astype(np.float32).tolist()
        } for i in range(len(self._labels))]

def load(self, items: List[Dict[str, Any]]) -> int:
    added = 0
    with self._lock:
        for it in items:
            try:
                lbl = str(it.get("label",""))
                sc  = float(it.get("score",0.5))
                tags= list(it.get("tags", []))
                vec = np.array(it["vec"], dtype=np.float32)
                self._labels.append(lbl); self._vecs.append(vec)
                self._scores.append(sc);  self._tags.append(tags)
                self._ts.append(float(it.get("ts", time.time())))
                added += 1
            except Exception:
                continue
    return added

def save(self) -> int:
    data = self.dump()
    tmp = self._persist_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, self._persist_path)
    return len(data)

def load_from_disk(self) -> int:
    if not os.path.exists(self._persist_path): return 0
    try:
        with open(self._persist_path, "r", encoding="utf-8") as f:
            items = json.load(f)
        return self.load(items)
    except Exception:
        return 0

