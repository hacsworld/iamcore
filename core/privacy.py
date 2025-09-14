from __future__ import annotations
import re, yaml
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
    peers_resonance_threshold: float = 0.5
    peers_max_peers: int = 3

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
        peers_max_message_bytes = int(peers.get("max_message_bytes", 65536)),
        peers_resonance_threshold = float(peers.get("resonance_threshold", 0.5)),
        peers_max_peers = int(peers.get("max_peers", 3)),
    )

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
