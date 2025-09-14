# core/privacy.py
from __future__ import annotations
import os, re, yaml
from dataclasses import dataclass, field
from typing import List

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
    peers_enabled: bool = True
    peers_allowlist: List[str] = field(default_factory=list)
    peers_max_message_bytes: int = 65536
    peers_resonance_threshold: float = 0.45
    peers_max_peers: int = 3

# ---- defaults, если policies.yaml отсутствует
_DEFAULT = PrivacyPolicy(
    egress_default="deny",
    cloud_allowlist=["api.github.com", "docs.hacs.world", "ws.hacs.world"],
    cloud_partner_allowlist=[],
    pii_enabled=True,
    pii_patterns=[
        PIIPattern(name="email", regex=r"(?i)[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", replace="[email]"),
        PIIPattern(name="phone", regex=r"(\+?\d[\d\-\s]{7,}\d)", replace="[phone]"),
    ],
    peers_enabled=True,
    peers_allowlist=["*"],
    peers_max_message_bytes=65536,
    peers_resonance_threshold=0.45,
    peers_max_peers=3,
)

def _load_yaml(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return None

def load_policy() -> PrivacyPolicy:
    """
    Ищем policies.yaml рядом с этим файлом.
    Если файл не найден/битый — возвращаем безопасные дефолты (_DEFAULT).
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, "policies.yaml"),
        os.path.join(os.getcwd(), "core", "policies.yaml"),
        os.path.join(os.getcwd(), "policies.yaml"),
    ]
    raw = None
    for p in candidates:
        raw = _load_yaml(p)
        if raw is not None:
            break
    if raw is None:
        return _DEFAULT  # тихий fallback

    try:
        privacy = raw.get("privacy") or {}
        peers   = raw.get("peers") or {}

        patterns = []
        pii = privacy.get("pii_redaction") or {}
        if pii.get("enable", True):
            for item in pii.get("patterns", []):
                patterns.append(PIIPattern(
                    name=item.get("name", "pii"),
                    regex=item.get("regex", ""),
                    replace=item.get("replace", "[redacted]"),
                ))

        return PrivacyPolicy(
            egress_default = privacy.get("egress_default", _DEFAULT.egress_default),
            cloud_allowlist = privacy.get("cloud_allowlist", _DEFAULT.cloud_allowlist),
            cloud_partner_allowlist = privacy.get("cloud_partner_allowlist", _DEFAULT.cloud_partner_allowlist),
            pii_enabled = pii.get("enable", _DEFAULT.pii_enabled),
            pii_patterns = patterns or _DEFAULT.pii_patterns,
            peers_enabled = (peers.get("enabled", _DEFAULT.peers_enabled)),
            peers_allowlist = peers.get("allowlist", _DEFAULT.peers_allowlist),
            peers_max_message_bytes = int(peers.get("max_message_bytes", _DEFAULT.peers_max_message_bytes)),
            peers_resonance_threshold = float(peers.get("resonance_threshold", _DEFAULT.peers_resonance_threshold)),
            peers_max_peers = int(peers.get("max_peers", _DEFAULT.peers_max_peers)),
        )
    except Exception:
        # любой парсинг-фейл => безопасные дефолты
        return _DEFAULT

def redact_pii(text: str, policy: PrivacyPolicy) -> str:
    if not policy.pii_enabled or not text:
        return text
    out = text
    for p in policy.pii_patterns:
        try:
            out = re.sub(p.regex, p.replace, out, flags=re.IGNORECASE)
        except re.error:
            continue
    return out

   
