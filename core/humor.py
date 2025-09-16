from __future__ import annotations
import os, re, random

SAFE_BAN = [r"\b(идиот|дурак|дебил|кретин)\b", r"\b(урод|калека|сумасшедш\w*)\b",
            r"\b(жирн\w*|тощ\w*)\b", r"\b(нищ\w*|бедн\w*)\b"]
SAFE_RE = [re.compile(p, re.IGNORECASE) for p in SAFE_BAN]

LINES = {
    "ru": ["Ладно, бро, сделаю. А ты пока сделай вид, что это заняло 5 минут 😅"],
    "en": ["Alright, I’ll lift; you take the credit 😉"],
}

def one_liner(lang="ru"):
    pool = LINES.get("ru" if lang.startswith("ru") else "en", [])
    random.shuffle(pool)
    for cand in pool:
        if not any(rx.search(cand) for rx in SAFE_RE): return cand
    return ""
