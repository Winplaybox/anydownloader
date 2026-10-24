import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml
import httpx

SHORT_DOMAINS = {
    "youtu.be",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "pin.it",
    "redd.it",
    "fb.watch",
    "t.co",
    "instagr.am",
}

class PlatformRegistry:
    def __init__(self, yaml_path: Optional[str] = None):
        if not yaml_path:
            cand1 = Path(__file__).resolve().parent / "platforms.yaml"
            cand2 = Path(__file__).resolve().parent.parent / "platforms.yaml"
            yaml_path = str(cand1) if cand1.exists() else str(cand2)
        
        self.yaml_path = yaml_path
        self.platforms: List[Dict[str, Any]] = []
        self.platforms_by_id: Dict[str, Dict[str, Any]] = {}
        self.status_overrides: Dict[str, str] = {}
        self.load()

    def load(self):
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    self.platforms = data
                    self.platforms_by_id = {p["id"]: p for p in data if "id" in p}
        except Exception as e:
            print(f"[PlatformRegistry] Error loading {self.yaml_path}: {e}")

    async def resolve_short_link(self, url: str) -> str:
        """Resolves known short domains via HEAD request."""
        try:
            parsed = urllib.parse.urlparse(url)
            host = parsed.netloc.lower()
            if any(host == sd or host.endswith("." + sd) for sd in SHORT_DOMAINS):
                async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                    resp = await client.head(url, headers={"User-Agent": "Mozilla/5.0 (compatible; OVD-Downloader/3.0)"})
                    return str(resp.url)
        except Exception:
            pass
        return url

    def match(self, url: str) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
        """
        Matches a normalized URL against registry.
        Returns (platform_def, content_type, matched_id).
        """
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()

        # 1. Match Tier A platforms by domain & urlPatterns
        for p in self.platforms:
            if p.get("id") == "generic":
                continue
            
            domains = p.get("domains", [])
            host_matched = any(
                host == d.lower() or host.endswith("." + d.lower())
                for d in domains
                if d != "*"
            )

            if host_matched:
                patterns = p.get("urlPatterns", [])
                for pat in patterns:
                    regex_str = pat.get("regex")
                    if regex_str:
                        m = re.search(regex_str, url)
                        if m:
                            matched_id = m.group(1) if m.groups() else None
                            return p, pat.get("type", "video"), matched_id

                default_type = p.get("contentTypes", ["video"])[0]
                return p, default_type, None

        # 2. Tier B (Generic / Any Website) if enabled
        allow_generic = os.environ.get("ALLOW_GENERIC_URLS", "true").lower() in ("true", "1", "yes")
        if allow_generic:
            gen_p = self.platforms_by_id.get("generic")
            if gen_p:
                return gen_p, "video", None

        return None, "unknown", None

    def get_platform(self, platform_id: str) -> Optional[Dict[str, Any]]:
        return self.platforms_by_id.get(platform_id)

    def set_status(self, platform_id: str, status: str):
        """Set dynamic status: ok | degraded | down | beta"""
        self.status_overrides[platform_id] = status

    def get_platforms_api(self) -> List[Dict[str, Any]]:
        """Returns the public catalog for GET /api/platforms."""
        res = []
        for p in self.platforms:
            pid = p.get("id")
            tier = p.get("tier", "A")
            base_status = "beta" if tier == "B" else "ok"
            status = self.status_overrides.get(pid, base_status)

            res.append({
                "id": pid,
                "name": p.get("name"),
                "tier": tier,
                "status": status,
                "contentTypes": p.get("contentTypes", []),
                "needsCookies": p.get("needsCookies", "never"),
                "seo": p.get("seo", {})
            })
        return res

registry = PlatformRegistry()
