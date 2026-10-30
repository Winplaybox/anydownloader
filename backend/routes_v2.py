"""
/api/v2 - Zero-Trust gateway routes.

Public (no token):
  GET  /api/v2/gravityclaw/catalog     targets, presets, styles (ETag cached)
  GET  /api/v2/gravityclaw/health      provider + store status (no secrets)
Token:
  POST /api/v2/auth/token              issue single-use token (admin via X-Admin-Key / Supabase JWT)
Protected (single-use bearer token, scope gravityclaw:generate):
  POST /api/v2/gravityclaw/generate
  POST /api/v2/gravityclaw/refine
  POST /api/v2/gravityclaw/score
"""

from __future__ import annotations

import hashlib
import json

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

try:
    from backend.security.token_vault import store
    from backend.security.zero_trust import client_ip, error, issue_token_endpoint, rate_limit, request_id, require_token
    from backend.services.gravityclaw import GCError, gravityclaw_engine, public_catalog
    from backend.services.gravityclaw.agent_universe import universe
    from backend.services.llm_router import llm_router
except (ModuleNotFoundError, ImportError):
    from security.token_vault import store  # type: ignore
    from security.zero_trust import client_ip, error, issue_token_endpoint, rate_limit, request_id, require_token  # type: ignore
    from services.gravityclaw import GCError, gravityclaw_engine, public_catalog  # type: ignore
    from services.gravityclaw.agent_universe import universe  # type: ignore
    from services.llm_router import llm_router  # type: ignore

GC_SCOPES = {"gravityclaw:generate", "prompt:generate"}

_CATALOG = public_catalog()
_CATALOG_BYTES = json.dumps({"ok": True, **_CATALOG}, ensure_ascii=False, separators=(",", ":")).encode()
_CATALOG_ETAG = '"' + hashlib.sha256(_CATALOG_BYTES).hexdigest()[:20] + '"'


async def gc_catalog(request: Request) -> Response:
    headers = {"ETag": _CATALOG_ETAG, "Cache-Control": "public, max-age=300, stale-while-revalidate=3600"}
    if request.headers.get("if-none-match") == _CATALOG_ETAG:
        return Response(status_code=304, headers=headers)
    return Response(_CATALOG_BYTES, media_type="application/json", headers=headers)


_PUBLIC_CACHE = {"Cache-Control": "public, max-age=300, stale-while-revalidate=3600"}


def _public_limited(request: Request) -> bool:
    ok, _ = rate_limit("gcpub", client_ip(request), 120, 60)
    return ok


async def gc_agents(request: Request) -> Response:
    """GET /api/v2/gravityclaw/agents?q=&kind=agent|script&domain=&family=&function=&group=&limit=&offset="""
    if not _public_limited(request):
        return error(request, 429, "RateLimited", "Too many requests.")
    qp = request.query_params
    try:
        limit = max(1, min(int(qp.get("limit", 20)), 50))
        offset = max(0, min(int(qp.get("offset", 0)), 5000))
    except ValueError:
        return error(request, 400, "InvalidField", "limit/offset must be integers.")
    kind = qp.get("kind") or None
    if kind not in (None, "agent", "script"):
        return error(request, 400, "InvalidField", "kind must be 'agent' or 'script'.")
    res = universe().search((qp.get("q") or "")[:120], kind=kind, domain=qp.get("domain") or None,
                            family=qp.get("family") or None, function=qp.get("function") or None,
                            group=qp.get("group") or None, limit=limit, offset=offset)
    return JSONResponse({"ok": True, **res}, headers=_PUBLIC_CACHE)


async def gc_agent_facets(request: Request) -> Response:
    return JSONResponse({"ok": True, **universe().facets()}, headers=_PUBLIC_CACHE)


async def gc_agent_detail(request: Request) -> Response:
    u = universe()
    a = u.get(request.path_params["agent_id"][:20])
    if not a:
        return error(request, 404, "UnknownAgent", "Agent not found.")
    return JSONResponse({"ok": True, "agent": u.summary(a), "profile": u.profile(a)}, headers=_PUBLIC_CACHE)


async def gc_health(request: Request) -> Response:
    providers = llm_router.status()
    return JSONResponse({
        "ok": any(p["available"] for p in providers),
        "service": "gravityclaw", "version": _CATALOG["version"],
        "providers": [{"provider": p["provider"], "available": p["available"]} for p in providers],
        "token_store": getattr(store, "name", "unknown"),
    }, headers={"Cache-Control": "no-store"})


async def _json(request: Request):
    try:
        return json.loads(await request.body() or b"{}")
    except Exception:
        raise GCError("BadJSON", "Body must be valid JSON.")


def _respond(request: Request, payload: dict) -> JSONResponse:
    payload["request_id"] = request_id(request)
    return JSONResponse(payload, headers={"Cache-Control": "no-store"})


@require_token(GC_SCOPES, rate=("gc", 12, 60), daily=300, max_body=64 * 1024)
async def gc_generate(request: Request) -> Response:
    try:
        return _respond(request, await gravityclaw_engine.generate(await _json(request)))
    except GCError as e:
        return error(request, e.status, e.code, e.message)


@require_token(GC_SCOPES, rate=("gc", 12, 60), daily=300, max_body=64 * 1024)
async def gc_refine(request: Request) -> Response:
    try:
        return _respond(request, await gravityclaw_engine.refine(await _json(request)))
    except GCError as e:
        return error(request, e.status, e.code, e.message)


@require_token(GC_SCOPES, rate=("gcs", 60, 60), max_body=64 * 1024)
async def gc_score(request: Request) -> Response:
    try:
        return _respond(request, gravityclaw_engine.score(await _json(request)))
    except GCError as e:
        return error(request, e.status, e.code, e.message)


routes_v2 = [
    Route("/api/v2/auth/token", issue_token_endpoint, methods=["POST"]),
    Route("/api/v2/gravityclaw/catalog", gc_catalog, methods=["GET"]),
    Route("/api/v2/gravityclaw/health", gc_health, methods=["GET"]),
    Route("/api/v2/gravityclaw/agents", gc_agents, methods=["GET"]),
    Route("/api/v2/gravityclaw/agents/facets", gc_agent_facets, methods=["GET"]),
    Route("/api/v2/gravityclaw/agents/{agent_id}", gc_agent_detail, methods=["GET"]),
    Route("/api/v2/gravityclaw/generate", gc_generate, methods=["POST"]),
    Route("/api/v2/gravityclaw/refine", gc_refine, methods=["POST"]),
    Route("/api/v2/gravityclaw/score", gc_score, methods=["POST"]),
]
