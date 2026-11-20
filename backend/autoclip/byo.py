"""Bring-your-own AI key.

Users paste their own key (Gemini, OpenAI, Groq, OpenRouter, Anthropic). Rules this module enforces:
  * The key lives in the browser; it reaches us once per job over HTTPS in the request body.
  * Server side it is kept in RAM only (never in SQLite, never on disk, never in logs, never in job JSON),
    and dropped as soon as the job ends (or after TTL).
  * Only fixed provider URLs are called, so a key field can never be used for SSRF.
"""
from __future__ import annotations

import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

try:
    from backend.services.llm_router import LLMError, extract_json
except (ModuleNotFoundError, ImportError):  # pragma: no cover
    from services.llm_router import LLMError, extract_json  # type: ignore

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "gemini": {"name": "Google Gemini", "model": "gemini-2.5-flash",
               "fallbacks": ["gemini-2.0-flash", "gemini-2.5-flash-lite"], "kind": "gemini"},
    "openai": {"name": "OpenAI", "model": "gpt-4o-mini", "fallbacks": ["gpt-4.1-mini"], "kind": "openai",
               "url": "https://api.openai.com/v1/chat/completions", "json_mode": True},
    "groq": {"name": "Groq", "model": "llama-3.3-70b-versatile", "fallbacks": ["llama-3.1-8b-instant"],
             "kind": "openai", "url": "https://api.groq.com/openai/v1/chat/completions", "json_mode": True},
    "openrouter": {"name": "OpenRouter", "model": "google/gemini-2.5-flash", "fallbacks": ["openai/gpt-4o-mini"],
                   "kind": "openai", "url": "https://openrouter.ai/api/v1/chat/completions", "json_mode": False},
    "anthropic": {"name": "Anthropic Claude", "model": "claude-haiku-4-5", "fallbacks": [], "kind": "anthropic",
                  "url": "https://api.anthropic.com/v1/messages"},
}
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

_KEY_RE = re.compile(r"^[A-Za-z0-9_\-\.:~+/=]{16,300}$")
_MODEL_RE = re.compile(r"^[A-Za-z0-9_\-\.:/]{2,80}$")
TTL_SECONDS = 3 * 3600


class KeyError_(ValueError):
    """Bad provider/key/model supplied by the user. Message is safe to show."""


class UserAI:
    def __init__(self, provider: str, key: str, model: Optional[str] = None) -> None:
        self.provider = provider
        self._key = key
        spec = PROVIDERS[provider]
        self.models: List[str] = [model] if model else [spec["model"], *spec["fallbacks"]]
        self.usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
        self.used_model: Optional[str] = None

    def __repr__(self) -> str:  # never leak the key through logs / tracebacks
        return f"<UserAI {self.provider} key=***>"

    __str__ = __repr__

    # ------------------------------------------------------------------ calls
    async def complete_json(self, system: str, user: str, *, temperature: float = 0.4, max_tokens: int = 4096,
                            budget_s: float = 90.0) -> Dict[str, Any]:
        deadline = time.monotonic() + budget_s
        last: Optional[str] = None
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=8.0), follow_redirects=False) as c:
            for model in self.models:
                if time.monotonic() > deadline:
                    break
                try:
                    text = await self._call(c, model, system, user, temperature, max_tokens)
                    obj = extract_json(text)
                    self.used_model = model
                    return obj
                except httpx.HTTPStatusError as e:
                    code = e.response.status_code
                    last = _http_message(self.provider, code)
                    if code in (400, 401, 403):  # wrong/blocked key or bad request: other models won't help
                        if code != 400:
                            break
                except (httpx.HTTPError, LLMError, ValueError, KeyError, IndexError) as e:
                    last = f"{self.provider} returned an unusable answer ({type(e).__name__})"
        raise LLMError(last or f"{self.provider} did not answer in time")

    async def _call(self, c: httpx.AsyncClient, model: str, system: str, user: str, temperature: float,
                    max_tokens: int) -> str:
        spec = PROVIDERS[self.provider]
        kind = spec["kind"]
        if kind == "gemini":
            cfg: Dict[str, Any] = {"temperature": temperature, "maxOutputTokens": max_tokens,
                                   "responseMimeType": "application/json"}
            if "2.5" in model:
                cfg["thinkingConfig"] = {"thinkingBudget": min(1024, max_tokens // 4)}
            r = await c.post(GEMINI_URL.format(model=model),
                             headers={"x-goog-api-key": self._key, "Content-Type": "application/json"},
                             json={"systemInstruction": {"parts": [{"text": system}]},
                                   "contents": [{"role": "user", "parts": [{"text": user}]}],
                                   "generationConfig": cfg})
            r.raise_for_status()
            d = r.json()
            u = d.get("usageMetadata") or {}
            self._count(u.get("promptTokenCount"), u.get("candidatesTokenCount"))
            cands = d.get("candidates") or []
            if not cands:
                raise LLMError("blocked: " + str((d.get("promptFeedback") or {}).get("blockReason", "empty")))
            return "".join(p.get("text", "") for p in cands[0].get("content", {}).get("parts", []))
        if kind == "anthropic":
            r = await c.post(spec["url"], headers={"x-api-key": self._key, "anthropic-version": "2023-06-01",
                                                   "Content-Type": "application/json"},
                             json={"model": model, "max_tokens": max_tokens, "temperature": temperature,
                                   "system": system, "messages": [{"role": "user", "content": user}]})
            r.raise_for_status()
            d = r.json()
            u = d.get("usage") or {}
            self._count(u.get("input_tokens"), u.get("output_tokens"))
            return "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
        body: Dict[str, Any] = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
                                "messages": [{"role": "system", "content": system},
                                             {"role": "user", "content": user}]}
        if spec.get("json_mode"):
            body["response_format"] = {"type": "json_object"}
        hdr = {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"}
        if self.provider == "openrouter":
            hdr["X-Title"] = "AutoClip AI"
        r = await c.post(spec["url"], headers=hdr, json=body)
        r.raise_for_status()
        d = r.json()
        u = d.get("usage") or {}
        self._count(u.get("prompt_tokens"), u.get("completion_tokens"))
        return d["choices"][0]["message"]["content"] or ""

    def _count(self, tin: Any, tout: Any) -> None:
        self.usage["calls"] += 1
        self.usage["input_tokens"] += int(tin or 0)
        self.usage["output_tokens"] += int(tout or 0)

    def public(self) -> Dict[str, Any]:
        return {"provider": self.provider, "model": self.used_model or self.models[0], **self.usage}


def _http_message(provider: str, code: int) -> str:
    name = PROVIDERS[provider]["name"]
    if code in (401, 403):
        return f"{name} rejected the API key. Check that it is correct and enabled."
    if code == 429:
        return f"{name} says the key is out of quota or rate-limited. Wait a minute or use another key."
    if code == 404:
        return f"{name} does not have that model on this key."
    if code == 400:
        return f"{name} refused the request."
    return f"{name} had a problem (HTTP {code})."


def build(provider: Any, key: Any, model: Any = None) -> Optional[UserAI]:
    """None when the user supplied nothing; KeyError_ when what they supplied is unusable."""
    provider = str(provider or "").strip().lower()
    key = str(key or "").strip()
    model = str(model or "").strip() or None
    if not provider and not key:
        return None
    if provider not in PROVIDERS:
        raise KeyError_("Choose an AI provider.")
    if not _KEY_RE.match(key):
        raise KeyError_("That API key looks wrong. Copy it again without spaces.")
    if model and not _MODEL_RE.match(model):
        raise KeyError_("That model name looks wrong.")
    return UserAI(provider, key, model)


async def test(ai: UserAI) -> Dict[str, Any]:
    t0 = time.monotonic()
    obj = await ai.complete_json('Reply with JSON only: {"ok": true}', 'Return {"ok": true}.', temperature=0,
                                 max_tokens=64, budget_s=25)
    return {"ok": bool(obj), "provider": ai.provider, "model": ai.used_model,
            "ms": int((time.monotonic() - t0) * 1000)}


# --------------------------------------------------------------------------- #
# RAM-only vault: job_id -> UserAI
# --------------------------------------------------------------------------- #
_vault: Dict[str, Tuple[UserAI, float]] = {}
_lock = threading.Lock()


def put(job_id: str, ai: UserAI) -> None:
    now = time.time()
    with _lock:
        for k in [k for k, (_, exp) in _vault.items() if exp < now]:
            _vault.pop(k, None)
        _vault[job_id] = (ai, now + TTL_SECONDS)


def get(job_id: str) -> Optional[UserAI]:
    with _lock:
        item = _vault.get(job_id)
    return item[0] if item and item[1] > time.time() else None


def drop(job_id: str) -> None:
    with _lock:
        _vault.pop(job_id, None)
