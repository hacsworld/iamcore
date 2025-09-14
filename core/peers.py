from __future__ import annotations
from typing import List, Dict, Any

class PeerExchangeResult(Dict[str, Any]):
    pass

def resonant_exchange(query: str, topk_context: List[Dict[str, Any]], max_peers: int = 3) -> PeerExchangeResult:
    """
    Минимальный мок обмена с пирамии.
    Сейчас: имитируем ответ «пиров» на основе локального контекста (без внешней сети),
    чтобы фича работала сразу и не ломала CI.
    Возвращаем пустой список, если ничем не можем помочь.
    """
    # Идея: если похожесть слабая — попробуем «добавить» ещё 1-2 идеи из локального контекста.
    hints = []
    for item in topk_context:
        txt = item.get("text", "")
        sim = float(item.get("similarity", 0.0))
        if sim < 0.6 and len(hints) < max_peers:
            hints.append({"peer_id": "local-mock", "suggestion": f"Try: {txt}"})

    return PeerExchangeResult({
        "used_peers": len(hints),
        "hints": hints
    })
