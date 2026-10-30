"""
LLM Router - free-tier-first, multi-provider, circuit-broken.

Order (override with LLM_PROVIDER_ORDER="gemini,groq,openrouter,cerebras,pollinations"):
  gemini      GEMINI_API_KEY        (model: GEMINI_MODEL, default gemini-2.5-flash)
  groq        GROQ_API_KEY          (GROQ_MODEL, default llama-3.3-70b-versatile)
  openrouter  OPENROUTER_API_KEY    (OPENROUTER_MODEL, default meta-llama/llama-3.3-70b-instruct:free)
  cerebras    CEREBRAS_API_KEY      (CEREBRAS_MODEL, default llama-3.3-70b)
  pollinations (no key, last-resort; disable with LLM_DISABLE_POLLINATIONS=1)

Keys are read from env only and never logged or returned.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

log = logging.getLogger("wpb.llm")


class LLMError(Exception):
    pass


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: int


@dataclass
class _Provider:
    name: str
    kind: str            # "gemini" | "openai"
    url: str
    model: str
    key_env: Optional[str]
    json_mode: bool = True

    @property
    def key(self) -> str:
        return os.environ.get(self.key_env, "").strip() if self.key_env else ""

    @property
    def configured(self) -> bool:
        if self.name == "pollinations":
            return os.environ.get("LLM_DISABLE_POLLINATIONS", "0") != "1"
        return bool(self.key)


def _providers() -> Dict[str, _Provider]:
    e = os.environ.get
    return {
        "gemini": _Provider("gemini", "gemini",
                            "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                            e("GEMINI_MODEL", "gemini-2.5-flash"), "GEMINI_API_KEY"),
        "groq": _Provider("groq", "openai", "https://api.groq.com/openai/v1/chat/completions",
                          e("GROQ_MODEL", "llama-3.3-70b-versatile"), "GROQ_API_KEY"),
        "openrouter": _Provider("openrouter", "openai", "https://openrouter.ai/api/v1/chat/completions",
                                e("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free"), "OPENROUTER_API_KEY"),
        "cerebras": _Provider("cerebras", "openai", "https://api.cerebras.ai/v1/chat/completions",
                              e("CEREBRAS_MODEL", "llama-3.3-70b"), "CEREBRAS_API_KEY"),
        "pollinations": _Provider("pollinations", "openai", "https://text.pollinations.ai/openai",
                                  e("POLLINATIONS_MODEL", "openai"), None, json_mode=False),
    }


class _Breaker:
    def __init__(self, threshold: int = 3, cooldown: int = 90):
        self.threshold, self.cooldown = threshold, cooldown
        self.fails: Dict[str, int] = {}
        self.open_until: Dict[str, float] = {}

    def available(self, name: str) -> bool:
        return self.open_until.get(name, 0) < time.time()

    def success(self, name: str) -> None:
        self.fails[name] = 0
        self.open_until.pop(name, None)

    def failure(self, name: str) -> None:
        self.fails[name] = self.fails.get(name, 0) + 1
        if self.fails[name] >= self.threshold:
            self.open_until[name] = time.time() + self.cooldown
            self.fails[name] = 0


class LLMRouter:
    def __init__(self) -> None:
        self.breaker = _Breaker()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0),
                                             limits=httpx.Limits(max_connections=20))
        return self._client

    def order(self) -> List[_Provider]:
        provs = _providers()
        names = [n.strip() for n in os.environ.get(
            "LLM_PROVIDER_ORDER", "gemini,groq,openrouter,cerebras,pollinations").split(",") if n.strip()]
        return [provs[n] for n in names if n in provs]

    def status(self) -> List[Dict[str, Any]]:
        return [{"provider": p.name, "model": p.model, "configured": p.configured,
                 "available": p.configured and self.breaker.available(p.name)} for p in self.order()]

    async def _call(self, p: _Provider, system: str, user: str, temperature: float, max_tokens: int) -> str:
        if p.kind == "gemini":
            r = await self.client.post(
                p.url.format(model=p.model),
                headers={"x-goog-api-key": p.key, "Content-Type": "application/json"},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens,
                                         "responseMimeType": "application/json"},
                    "safetySettings": [{"category": c, "threshold": "BLOCK_MEDIUM_AND_ABOVE"} for c in (
                        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                        "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")],
                },
            )
            r.raise_for_status()
            data = r.json()
            cands = data.get("candidates") or []
            if not cands:
                raise LLMError(f"gemini blocked: {data.get('promptFeedback', {}).get('blockReason', 'empty')}")
            return "".join(part.get("text", "") for part in cands[0].get("content", {}).get("parts", []))

        headers = {"Content-Type": "application/json"}
        if p.key:
            headers["Authorization"] = f"Bearer {p.key}"
        if p.name == "openrouter":
            headers["HTTP-Referer"] = "https://gravityclaw.winplaybox.in"
            headers["X-Title"] = "GravityClaw"
        body: Dict[str, Any] = {
            "model": p.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if p.json_mode:
            body["response_format"] = {"type": "json_object"}
        r = await self.client.post(p.url, headers=headers, json=body)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"] or ""

    async def complete_json(self, system: str, user: str, *, temperature: float = 0.7,
                            max_tokens: int = 2500, budget_s: float = 55.0) -> tuple[Dict[str, Any], LLMResult]:
        """Try providers in order until one returns parseable JSON."""
        deadline = time.monotonic() + budget_s
        errors: List[str] = []
        for p in self.order():
            if not p.configured or not self.breaker.available(p.name):
                continue
            if time.monotonic() > deadline:
                break
            t0 = time.monotonic()
            try:
                text = await self._call(p, system, user, temperature, max_tokens)
                obj = extract_json(text)
                self.breaker.success(p.name)
                res = LLMResult(text, p.name, p.model, int((time.monotonic() - t0) * 1000))
                log.info(json.dumps({"llm": p.name, "model": p.model, "ms": res.latency_ms}))
                return obj, res
            except Exception as e:
                self.breaker.failure(p.name)
                status = getattr(getattr(e, "response", None), "status_code", None)
                errors.append(f"{p.name}:{status or type(e).__name__}")
                log.warning("llm provider failed %s %s", p.name, status or type(e).__name__)
        raise LLMError("all providers failed: " + ", ".join(errors or ["none configured"]))


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def extract_json(text: str) -> Dict[str, Any]:
    t = _FENCE.sub("", (text or "").strip())
    try:
        obj = json.loads(t)
    except json.JSONDecodeError:
        start = t.find("{")
        if start < 0:
            raise LLMError("no JSON object in response")
        depth, in_str, esc = 0, False, False
        for i in range(start, len(t)):
            ch = t[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    obj = json.loads(t[start:i + 1])
                    break
        else:
            raise LLMError("unterminated JSON object")
    if not isinstance(obj, dict):
        raise LLMError("JSON root must be an object")
    return obj


llm_router = LLMRouter()
