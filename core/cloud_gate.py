from future import annotations
from typing import List, Dict, Any, Tuple, Optional
import re, hashlib, os
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import tldextracttry:
    from .readers import sniff_and_read
except Exception:
    from readers import sniff_and_readdef _domain(url: str) -> str:
    ext = tldextract.extract(url)
    return ".".join([p for p in [ext.domain, ext.suffix] if p])def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()[:10]def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script","style","noscript"]): t.decompose()
    text = soup.get_text("\n", strip=True)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return textclass CloudGate:
    def init(self, embedder, allow_domains: Optional[List[str]] = None, timeout_s: float = 10.0):
        self.embed = embedder
        self.allow = set((allow_domains or []))
        self.timeout = timeout_sdef _allowed(self, url: str) -> bool:
    if not self.allow: return True
    d = _domain(url).lower()
    return any(d==a or d.endswith("."+a) for a in self.allow)

def search(self, q: str, k: int = 6) -> List[Dict[str, Any]]:
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(q, max_results=k*2):
            u = r.get("href") or r.get("link") or ""
            if u and self._allowed(u):
                out.append({"title": r.get("title") or "", "url": u, "snippet": r.get("body") or ""})
            if len(out) >= k: break
    return out

def fetch_text(self, url: str) -> Tuple[str, str]:
    try:
        with httpx.Client(timeout=self.timeout, headers={"User-Agent": "iamcore/1.0"}) as c:
            r = c.get(url, follow_redirects=True)
        ct = (r.headers.get("content-type") or "").lower()
        data = r.content
        if "pdf" in ct or url.lower().endswith(".pdf"):
            _, txt = sniff_and_read("remote.pdf", data); return ("pdf", txt)
        if any(url.lower().endswith(s) for s in (".docx",".xlsx",".csv",".txt",".png",".jpg",".jpeg",".webp",".tiff",".bmp")):
            _, txt = sniff_and_read(url.split("/")[-1] or "remote.bin", data); return ("bin", txt)
        return ("html", _strip_html(data.decode("utf-8", errors="ignore")))
    except Exception as e:
        return ("error", f"[fetch-error] {e}")try:
    from .resonance import EssenceDistiller
except Exception:
    from resonance import EssenceDistillerclass CloudGateEssence(CloudGate):
    def gate_essence(self, query: str, k_search: int = 6, k_docs: int = 3, top_k_sent: int = 6) -> Dict[str, Any]:
        hits = self.search(query, k=k_search)
        qv = self.embed(query)
        import numpy as np
        def _sim(t: str) -> float:
            hv = self.embed(t)
            return float((hv/(np.linalg.norm(hv)+1e-9) * (qv/(np.linalg.norm(qv)+1e-9))).sum())
        hits.sort(key=lambda h: _sim((h.get("title","")+" "+h.get("snippet","")).strip() or h["url"]), reverse=True)
        hits = hits[:k_docs]    distiller = EssenceDistiller(self.embed)
    distilled = []
    for h in hits:
        mime, text = self.fetch_text(h["url"])
        ess = distiller.distill(query, text or "", top_k=top_k_sent, max_chars=800)
        distilled.append({"url":h["url"], "title":h.get("title",""), "mime":mime,
                          "essence":ess["essence"], "snippets":ess["snippets"], "hash":_hash(h["url"])})
    return {"hits": hits, "distilled": distilled}

