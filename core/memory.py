# core/memory.py
from __future__ import annotations

from typing import List, Dict, Any, Optional
import time
import json
import threading
import os
import numpy as np


def _norm(v: np.ndarray) -> np.ndarray:
    """L2-нормализация (без деления на ноль)."""
    n = float(np.linalg.norm(v) + 1e-9)
    return v / n


class ResonanceMemory:
    """
    Лёгкая векторная память (thread-safe), персистентность в JSON.
    - learn(): добавить элемент
    - search(): top-k по косинусной близости (с учётом score как веса)
    - save()/load_from_disk(): persistence
    """

    def __init__(self, dim: int, k: int = 8, save_every: int = 100):
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
        self._persist_path = os.getenv("MEMORY_PATH", "./state/memory.json")
        os.makedirs(os.path.dirname(self._persist_path) or ".", exist_ok=True)

    # ---------- Core API ----------

    def learn(
        self,
        label: str,
        vec: np.ndarray,
        score: float,
        tags: Optional[List[str]] = None,
    ):
        """Добавить запись в память."""
        with self._lock:
            v = np.asarray(vec, dtype=np.float32)
            if v.shape and v.ndim == 1 and v.size != self.dim:
                # мягкая защита от неверной размерности
                v = v.reshape(-1)[: self.dim]
            self._labels.append(str(label))
            self._vecs.append(v.astype(np.float32))
            self._scores.append(float(max(0.0, min(1.0, score))))
            self._tags.append(list(tags or []))
            self._ts.append(time.time())
            self._steps += 1

            if self.save_every and (self._steps % self.save_every == 0):
                try:
                    self.save()
                except Exception:
                    pass

    def search(self, query_vec: np.ndarray, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Вернуть top-k ближайших элементов (учитываем score как вес)."""
        with self._lock:
            if not self._vecs:
                return []
            k = int(k or self.k)

            q = _norm(np.asarray(query_vec, dtype=np.float32))
            M = np.vstack([_norm(v) for v in self._vecs])  # [N, dim]
            sims = M @ q  # косинусная близость
            # подмешиваем доверие score
            sims = sims * (0.5 + 0.5 * np.asarray(self._scores, dtype=np.float32))

            idx = np.argsort(sims)[-k:][::-1]
            out: List[Dict[str, Any]] = []
            for i in idx:
                out.append(
                    {
                        "label": self._labels[i],
                        "score": float(sims[i]),
                        "tags": self._tags[i],
                        "ts": float(self._ts[i]),
                    }
                )
            return out

    # ---------- Stats / Persistence ----------

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "items": len(self._labels),
                "dim": self.dim,
                "k": self.k,
                "recent": self._labels[-5:][::-1] if self._labels else [],
            }

    def dump(self) -> List[Dict[str, Any]]:
        with self._lock:
            data: List[Dict[str, Any]] = []
            for i in range(len(self._labels)):
                data.append(
                    {
                        "label": self._labels[i],
                        "score": self._scores[i],
                        "tags": self._tags[i],
                        "ts": self._ts[i],
                        "vec": self._vecs[i].astype(np.float32).tolist(),
                    }
                )
            return data

    def load(self, items: List[Dict[str, Any]]) -> int:
        """Загрузить записи (например, из файла/экспорта). Возвращает количество добавленных."""
        added = 0
        with self._lock:
            for it in items:
                try:
                    lbl = str(it.get("label", ""))
                    sc = float(it.get("score", 0.5))
                    tags = list(it.get("tags", []))
                    vec = np.asarray(it["vec"], dtype=np.float32)
                    if vec.size != self.dim:
                        vec = vec.reshape(-1)[: self.dim]
                    self._labels.append(lbl)
                    self._vecs.append(vec)
                    self._scores.append(sc)
                    self._tags.append(tags)
                    self._ts.append(float(it.get("ts", time.time())))
                    added += 1
                except Exception:
                    continue
        return added

    def save(self) -> int:
        """Сохранить в JSON (атомарная замена файла)."""
        data = self.dump()
        tmp = self._persist_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, self._persist_path)
        return len(data)

    def load_from_disk(self) -> int:
        """Загрузить из JSON, если файл существует."""
        path = self._persist_path
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                items = json.load(f)
            return self.load(items)
        except Exception:
            return 0
