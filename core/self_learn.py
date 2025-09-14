from __future__ import annotations
import os
import time
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np

# Хранилище по умолчанию: ~/.hacs/
HOME = os.path.expanduser("~")
HACS_DIR = os.path.join(HOME, ".hacs")
os.makedirs(HACS_DIR, exist_ok=True)

MEM_NPZ = os.path.join(HACS_DIR, "memory_embeddings.npz")  # векторы (np.float32)
MEM_JSONL = os.path.join(HACS_DIR, "memory_events.jsonl")  # сырые тексты+метаданные

# Небольший набор стоп-слов, чтобы без внешних NLP-зависимостей
_STOP = {
    "the", "and", "for", "with", "that", "this", "you", "your", "from", "have", "has", "are", "was", "were",
    "but", "not", "all", "any", "can", "could", "will", "would", "about", "into", "onto", "over", "under",
    "open", "create", "new", "note", "document", "pay", "manage", "control", "smart", "home", "devices",
    "lights", "schedule", "appointments", "meetings", "search", "web", "information", "play", "music",
    "set", "reminders", "timers", "send", "messages", "emails", "translate", "languages", "real", "time",
}

@dataclass
class Cluster:
    centroid: np.ndarray
    count: int = 0
    keywords: Counter = field(default_factory=Counter)

class ResonanceMemory:
    """
    Лёгкая онлайновая память резонанса:
      - накапливает эмбеддинги и события
      - поддерживает K «тем» (online k-means на косинусе)
      - вытаскивает топ-слова на кластер
    Без внешних зависимостей, всё на numpy.
    """
    def __init__(self, dim: int, k: int = 8, save_every: int = 5):
        self.dim = dim
        self.k = k
        self.save_every = save_every
        self.events_seen = 0
        self.clusters: List[Cluster] = []
        self._load_npz()

    # ---------- public API ----------
    def learn(self, text: str, emb: np.ndarray, score: float) -> None:
        """Добавить пример и обновить кластеры."""
        emb = self._norm(emb.astype(np.float32))
        self._ensure_seed(emb)
        idx = self._closest_cluster(emb)
        self._update_cluster(idx, emb, text)
        self._append_event(text, score, idx)
        self.events_seen += 1
        if self.events_seen % self.save_every == 0:
            self._save_npz()

    def stats(self) -> Dict[str, Any]:
        """Сводная статистика: размеры кластеров, топ-слова."""
        out = []
        for i, c in enumerate(self.clusters):
            out.append({
                "cluster": i,
                "count": c.count,
                "top_keywords": [w for w, _ in c.keywords.most_common(8)]
            })
        return {"clusters": out, "total_events": self.events_seen, "k": self.k, "dim": self.dim}

    def suggest_keywords(self, top_n: int = 10) -> List[str]:
        """Глобальные подсказки-ключи (для подсветки интентов/скиллов)."""
        g = Counter()
        for c in self.clusters:
            g.update(c.keywords)
        return [w for w, _ in g.most_common(top_n)]

    # ---------- internals ----------
    def _ensure_seed(self, emb: np.ndarray):
        if not self.clusters:
            self.clusters.append(Cluster(centroid=emb.copy(), count=0))

    def _closest_cluster(self, emb: np.ndarray) -> int:
        best_idx, best_sim = 0, -1.0
        for i, c in enumerate(self.clusters):
            sim = float(np.dot(self._norm(c.centroid), emb))
            if sim > best_sim:
                best_sim, best_idx = sim, i
        if best_sim < 0.55 and len(self.clusters) < self.k:
            # низкая похожесть — рождаем новый «резонансный» кластер
            self.clusters.append(Cluster(centroid=emb.copy(), count=0))
            return len(self.clusters) - 1
        return best_idx

    def _update_cluster(self, idx: int, emb: np.ndarray, text: str):
        c = self.clusters[idx]
        # online-усреднение (эксп. сглаживание по счётчику)
        c.count += 1
        alpha = 1.0 / float(c.count)
        c.centroid = self._norm((1 - alpha) * c.centroid + alpha * emb)
        for tok in self._tokens(text):
            c.keywords[tok] += 1

    def _tokens(self, text: str) -> List[str]:
        toks = []
        for raw in text.lower().replace("/", " ").replace("-", " ").split():
            t = "".join(ch for ch in raw if ch.isalnum())
            if len(t) >= 3 and t not in _STOP:
                toks.append(t)
        return toks

    def _append_event(self, text: str, score: float, cluster_idx: int):
        evt = {
            "ts": int(time.time()),
            "text": text,
            "score": float(score),
            "cluster": int(cluster_idx),
        }
        with open(MEM_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    def _save_npz(self):
        # сохраняем только центроиды + счётчики + топ-слова (облегчённо)
        data = {
            "dim": np.array([self.dim], dtype=np.int32),
            "k": np.array([self.k], dtype=np.int32),
            "counts": np.array([c.count for c in self.clusters], dtype=np.int32),
            "centroids": np.stack([c.centroid for c in self.clusters], axis=0) if self.clusters else np.zeros((0, self.dim), np.float32),
        }
        np.savez_compressed(MEM_NPZ, **data)
        # keywords храним рядом (json), чтобы не городить сложные структуры в npz
        kw_path = MEM_NPZ + ".keywords.json"
        kw = [{"cluster": i, "keywords": dict(c.keywords)} for i, c in enumerate(self.clusters)]
        with open(kw_path, "w", encoding="utf-8") as f:
            json.dump(kw, f, ensure_ascii=False)

    def _load_npz(self):
        if not os.path.exists(MEM_NPZ):
            return
        try:
            blob = np.load(MEM_NPZ, allow_pickle=False)
            dim = int(blob["dim"][0])
            k = int(blob["k"][0])
            centroids = blob["centroids"].astype(np.float32)
            counts = blob["counts"].astype(np.int32)
            self.dim = dim
            self.k = k
            self.clusters = []
            for i in range(centroids.shape[0]):
                self.clusters.append(Cluster(centroid=self._norm(centroids[i]), count=int(counts[i])))
            # keywords
            kw_path = MEM_NPZ + ".keywords.json"
            if os.path.exists(kw_path):
                data = json.load(open(kw_path, "r", encoding="utf-8"))
                for item in data:
                    idx = int(item.get("cluster", -1))
                    if 0 <= idx < len(self.clusters):
                        self.clusters[idx].keywords.update(item.get("keywords", {}))
        except Exception:
            # повреждённое хранилище не должно ломать ядро
            self.clusters = []

    @staticmethod
    def _norm(v: np.ndarray) -> np.ndarray:
        n = float(np.linalg.norm(v) + 1e-9)
        return (v / n).astype(np.float32)

