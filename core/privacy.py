# core/privacy.py
"""
Лёгкий приватный «файрвол» для локального ИИ.
Сейчас — только функции и загрузка политики.
Позже подключим к /act и к любым исходящим вызовам.
"""

from __future__ import annotations
import re
import yaml
from dataclasses import dataclass, field
from typing import List

_POLICY_PATH = "core/policies.yaml"

@dataclass
class PIIPattern:
    name: str
    regex: str
    replace: str

@dataclass
class PrivacyPolicy:
    egress_default: str = "deny"
    cloud_allowlist: List[str] = field(default_factory=list)
    cloud_partner_allowlist: List[str] = field(default_factory=list)
    pii_enabled: bool = True
    pii_patterns: List[PIIPattern] = field(default_factory=list)
    peers_enabled: bool = False
    peers_allowlist: List[str] = field(default_factory=list)
    peers_max_message_bytes: int = 65536

def load_policy(path: str = _POLICY_PATH) -> PrivacyPolicy:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    privacy = (raw.get("privacy") or {})
    peers   = (raw.get("peers") or {})

    patterns = []
    pii = (privacy.get("pii_redaction") or {})
    if pii.get("enable", True):
        for p in pii.get("patterns", []):
            patterns.append(PIIPattern(
                name=p.get("name", "pii"),
                regex=p.get("regex", ""),
                replace=p.get("replace", "[redacted]"),
            ))

    return PrivacyPolicy(
        egress_default = privacy.get("egress_default", "deny"),
        cloud_allowlist = privacy.get("cloud_allowlist", []) or [],
        cloud_partner_allowlist = privacy.get("cloud_partner_allowlist", []) or [],
        pii_enabled = pii.get("enable", True),
        pii_patterns = patterns,
        peers_enabled = peers.get("enabled", False),
        peers_allowlist = peers.get("allowlist", []) or [],
        peers_max_message_bytes = peers.get("max_message_bytes", 65536),
    )

def redact_pii(text: str, policy: PrivacyPolicy) -> str:
    """Грубая маскировка PII — достаточно для первого шага."""
    if not policy.pii_enabled or not text:
        return text
    out = text
    for p in policy.pii_patterns:
        try:
            out = re.sub(p.regex, p.replace, out, flags=re.IGNORECASE)
        except re.error:
            # плохая регулярка не должна ронять ядро
            continue
    return out

def egress_allowed(host: str, policy: PrivacyPolicy) -> bool:
    """Проверка, можно ли идти наружу на хост (только чтение)."""
    allow = set(policy.cloud_allowlist) | set(policy.cloud_partner_allowlist)
    if host in allow:
        return True
    return policy.egress_default == "allow"

def peer_allowed(peer_id: str, policy: PrivacyPolicy) -> bool:
    """Взаимодействие с другим локальным ИИ — по allowlist и флагу."""
    if not policy.peers_enabled:
        return False
    return peer_id in set(policy.peers_allowlist)
