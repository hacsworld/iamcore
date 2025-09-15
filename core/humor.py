from __future__ import annotations
from typing import Optional
import os, re, random

SAFE_BAN = [
    r"\b(идиот|дурак|дебил|кретин)\b",
    r"\b(урод|калека|сумасшедш\w*)\b",
    r"\b(жирн\w*|тощ\w*)\b",
    r"\b(нищ\w*|бедн\w*)\b",
]
SAFE_RE = [re.compile(p, re.IGNORECASE) for p in SAFE_BAN]

REGIONAL_TEASE = {
    "ru-RU": {
        "friendly": [
            "Ну ты, {name}, конечно, хитрец: спросил — и сам же всё понял. Я только подпишусь 😏",
            "Ладно-ладно, {name}, я сделаю. А ты пока сделай вид, что это была твоя идея 🤝",
            "Это звучит просто… почти как твой будильник в понедельник: громко, но без давления 😅",
        ],
        "spicy": [
            "Ох, {name}, план хорош. Почти как диета после 23:00 — верится, но холодильник знает правду 🤌",
            "Сделаю. А ты пока потренируйся делать вид, что это заняло 'две минуты' ⏱️",
            "Запрос огонь. Ну или пожар — разберёмся на месте, я с огнетушителем 🔥",
        ],
    },
    "en-US": {
        "friendly": [
            "Alright {name}, smooth move. I’ll do the heavy lifting, you take the credit 😉",
            "Sounds easy—like Monday alarms: loud, unavoidable, mildly painful 😅",
        ],
        "spicy": [
            "Bold plan, {name}. Almost as realistic as 'just one last tweak' at 2 AM 😏",
            "I’ll build it. You practice saying ‘took five minutes’ with a straight face ⏱️",
        ],
    }
}

def _clean(j: str) -> str:
    for rx in SAFE_RE:
        if rx.search(j): return ""
    return j

class HumorEngine:
    def __init__(self, region: str = "ru-RU", mode: str = "friendly", name: Optional[str] = None):
        self.region = (region or "ru-RU")
        self.mode = (mode or "friendly")
        self.name = name or os.getenv("HUMOR_USER_NAME","друг")

    def one_liner(self) -> str:
        bank = REGIONAL_TEASE.get(self.region, REGIONAL_TEASE["ru-RU"])
        pool = bank.get(self.mode, bank["friendly"])
        if not pool: pool = REGIONAL_TEASE["ru-RU"]["friendly"]
        random.shuffle(pool)
        for cand in pool:
            j = _clean(cand.format(name=self.name))
            if j: return j
        return ""

    def decorate(self, answer: str) -> str:
        joke = self.one_liner()
        if not joke: return answer
        return f"{answer}\n\n— {joke}"

