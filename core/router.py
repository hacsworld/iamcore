from __future__ import annotations
from typing import Dict, Any
from .policy import build_system_prompt
from .providers import ask as call_provider

ASK_HINT_RU = "Уточни, пожалуйста: что именно тебе нужно?"
ASK_HINT_EN = "Please clarify what exactly you need?"

def route(text: str, ctx: Dict[str, Any], model, memory, distiller) -> Dict[str, Any]:
    q = (text or "").strip()
    if not q:
        return {"messages":[{"role":"assistant","text":"Напиши запрос"}]}

    # 1) контекст из памяти
    qv = model.encode(q)
    hits = memory.search(qv, k=5)
    ctx_text = " ".join([h["label"] for h in hits[:3]])

    # 2) essence
    distilled = distiller.distill(q, ctx_text, top_k=4, max_chars=300)
    essence = (distilled.get("essence") or "").strip()

    # 3) policy → ask-first при слабой сути
    if len(essence) < 12:
        ask = ASK_HINT_RU if (ctx.get("lang","ru").startswith("ru")) else ASK_HINT_EN
        return {"messages":[{"role":"assistant","text":f"{ask} (Понял как: «{q[:64]}» )"}]}

    # 4) системный праймер + провайдер
    sys = build_system_prompt(profile=ctx.get("profile",""), lang=ctx.get("lang","ru"))
    answer = call_provider(system=sys, question=q, context=essence)

    # 5) простые ui-акции по шаблонам
    ui = None
    lq = q.lower()
    if lq.startswith("/wallet") or "balance" in lq:
        ui = {"open":"g.pay","tab":"crypto","focus":"balance"}
    elif lq.startswith("/market") or "catalog" in lq:
        ui = {"open":"g.market","tab":"catalog"}

    # 6) запись вопроса
    memory.learn(f"[chat] {q[:80]}", qv, 0.8)

    msgs = [{"role":"assistant","text":answer}]
    if ui: msgs.append({"role":"system","ui_action":ui})
    return {"messages": msgs}
