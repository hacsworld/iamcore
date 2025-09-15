# core/cloud_gate.py

import os
import re
import tldextract   

class CloudGateEssence:
    def __init__(self):
        self.allowlist = os.getenv("ALLOWLIST", "").split(",")

    def is_allowed(self, url: str) -> bool:
        """
        Проверка, что домен в allowlist.
        """
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}" if ext.suffix else ext.domain
        return domain in self.allowlist

    def clean_url(self, url: str) -> str:
        """
        Убираем http:// и https://, нормализуем строку.
        """
        return re.sub(r"^https?://", "", url).strip()
