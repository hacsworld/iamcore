from __future__ import annotations
from .providers import ask, use_generation

def generate_answer(system_hint: str, question: str, context: str) -> str:
    return ask(system_hint, question, context)
