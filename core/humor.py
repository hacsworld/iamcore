# core/humor.py
from __future__ import annotations

import os
import re
import random
from typing import Optional, List

# Список мягких запретов (регэкспы) — чтобы шутки не уходили в токсик
SAFE_BAN: List[str] = [
    r"\b(идиот|дурак|дебил|кретин)\b",
    r"\b(урод|калека|сумасшедш\w*)\b",
    r"\b(жирн\w*|тощ\w*)\b",
    r"\b(нищ\w*|бедн\w*)\b",
]
SAFE_RE = [re.compile(p, re.IGNORECASE) for p in SAFE_BAN]

# Набор региональных подколов
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
    },
}

def _clean(line: str) -> str:
    """Отсекать строки, которые триггерят бан-списки."""
    for rx in SAFE_RE:
        if rx.search(line):
            return ""
    return line

class HumorEngine:
    """
    Лёгкий движок «подколов»: region-aware, режимы friendly/spicy,
    безопасные формулировки.
    """
    def __init__(self, region: str = "ru-RU", mode: str = "friendly", name: Optional[str] = None):
        self.region = (region or "ru-RU")
        self.mode = (mode or "friendly")
        self.name = name or os.getenv("HUMOR_USER_NAME", "друг")

    def one_liner(self) -> str:
        bank = REGIONAL_TEASE.get(self.region, REGIONAL_TEASE["ru-RU"])
        pool = bank.get(self.mode, bank["friendly"])
        if not pool:
            pool = REGIONAL_TEASE["ru-RU"]["friendly"]
        # Случайный, но безопасный выбор
        random.shuffle(pool)
        for template in pool:
            j = _clean(template.format(name=self.name))
            if j:
                return j
        return ""  # если все варианты зарезал фильтр

    def decorate(self, answer: str) -> str:
        """Приклеить шутку к ответу (после сути)."""
        joke = self.one_liner()
        if not joke:
            return answer
        return f"{answer}\n\n— {joke}"

    if not joke: return answer
    # лёгкая подача: сначала ответ по делу, в конце — подкол
    return f"{answer}\n\n— {joke}"

