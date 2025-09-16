from __future__ import annotations
import re

MASK_EMAIL = re.compile(r"[\w\.-]+@[\w\.-]+", re.I)
MASK_PHONE = re.compile(r"\+?\d[\d\s\-\(\)]{6,}\d", re.I)

def redact(text: str)->str:
    if not text: return text
    text = MASK_EMAIL.sub("<email>", text)
    text = MASK_PHONE.sub("<phone>", text)
    return text
