"""
/admin/autopilot - admin API for the video Autopilot (admin key or Supabase admin JWT; the admin page's
fetch bridge adds X-Admin-Key automatically for /admin/ paths).

Light work only happens here (Render free: 0.1 CPU / 512 MB): ideas, scripts, CRUD, the job queue.
Rendering and publishing run on the separate worker (AI Video Editor repo: python -m autopilot worker),
which reads the same Supabase tables (winplayboxsite/supabase/autopilot_schema.sql).

  GET  /admin/autopilot/catalog                 styles, caption styles, moods, niches
  GET  /admin/autopilot/voices?language=        free neural voices (edge-tts list)
  POST /admin/autopilot/ideas                   {niche, language, count}
  POST /admin/autopilot/script                  {topic, language, seconds, niche}
  GET  /admin/autopilot/autopilots
  POST /admin/autopilot/autopilots              create, or update when "id" is given
  POST /admin/autopilot/autopilots/{id}/delete
  GET  /admin/autopilot/jobs?limit=&autopilot=
  GET  /admin/autopilot/jobs/{id}               with signed video/thumbnail URLs
  POST /admin/autopilot/jobs                    {spec, story?} make a video now
  POST /admin/autopilot/jobs/{id}/regen         {scene, say?, image?, new_picture?}
  POST /admin/autopilot/jobs/{id}/publish       {platforms}
  POST /admin/autopilot/jobs/{id}/cancel
  GET  /admin/autopilot/status                  queue counts + workers seen in the last 10 minutes
  GET  /admin/autopilot/accounts                connected social accounts + per-platform setup state
  POST /admin/autopilot/accounts/connect/{platform}   -> {url} to the platform's sign-in page
  POST /admin/autopilot/accounts/{id}/delete
  GET  /oauth/autopilot/{platform}/callback     public OAuth redirect target (signed, expiring state)

Env: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, WPB_VAULT_SECRET (signs OAuth state).
YouTube connect: YT_CLIENT_ID, YT_CLIENT_SECRET (Google OAuth client, type "Web application").
Tokens are stored encrypted in Supabase Vault (supabase/autopilot_accounts.sql), never returned to the browser.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Route

try:
    from backend.security.zero_trust import authenticate_admin, error, rate_limit
    from backend.services.llm_router import LLMError, llm_router
except (ModuleNotFoundError, ImportError):
    from security.zero_trust import authenticate_admin, error, rate_limit  # type: ignore
    from services.llm_router import LLMError, llm_router  # type: ignore

# Keep in sync with autopilot/styles.py in the AI Video Editor repo.
STYLES = {
    "flat": "Flat Explainer", "cinematic": "Cinematic", "anime": "Anime", "painted-anime": "Painted Anime",
    "realistic": "Realistic", "3d-cartoon": "3D Cartoon", "cyberpunk": "Cyberpunk", "fantasy": "Fantasy",
    "noir": "Noir", "watercolor": "Watercolor", "comic": "Comic Book", "storybook": "Kids Storybook",
    "claymation": "Claymation", "pixel": "Pixel Art", "oil-painting": "Oil Painting", "minimal": "Minimal Vector",
    "horror": "Dark / Horror",
}
CAPTION_STYLES = {"pill": "Yellow pill", "bold": "Bold outline", "karaoke": "Karaoke fill", "minimal": "Minimal",
                  "neon": "Neon glow", "boxed": "Dark box"}
MOODS = ["upbeat", "calm", "inspiring", "dramatic", "mysterious", "happy", "dark", "epic", "lofi"]
NICHES = {
    "health": "Health & everyday science", "finance": "Personal finance", "facts": "Mind-blowing facts",
    "motivation": "Motivation & self-improvement", "history": "History stories", "horror": "Scary stories",
    "tech": "Tech & AI explained", "kids": "Kids stories with a moral", "mythology": "Mythology stories",
    "psychology": "Psychology facts", "business": "Business stories", "travel": "Travel & places",
}
PLATFORMS = {"youtube": "ready", "instagram": "planned", "facebook": "planned", "threads": "planned",
             "tiktok": "planned", "x": "planned"}

AUTOPILOT_FIELDS = {"name", "active", "niche", "topics", "style", "language", "voice", "rate", "seconds", "captions",
                    "caption_style", "caption_position", "watermark", "music", "quality", "aspect", "platforms",
                    "schedule", "timezone"}
SPEC_FIELDS = {"topic", "script", "niche", "style", "language", "voice", "rate", "seconds", "captions",
               "caption_style", "caption_position", "watermark", "music", "quality", "aspect", "platforms"}


# --------------------------------------------------------------------------- helpers

def _ok(data: Any, status: int = 200) -> JSONResponse:
    return JSONResponse({"ok": True, "data": data}, status_code=status, headers={"Cache-Control": "no-store"})


class _DB:
    def __init__(self) -> None:
        self._c: httpx.AsyncClient | None = None

    @property
    def configured(self) -> bool:
        return bool(os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

    @property
    def url(self) -> str:
        return os.environ.get("SUPABASE_URL", "").rstrip("/")

    def client(self) -> httpx.AsyncClient:
        if self._c is None:
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
            self._c = httpx.AsyncClient(headers={"apikey": key, "Authorization": f"Bearer {key}"},
                                        timeout=httpx.Timeout(30, connect=10))
        return self._c

    async def select(self, table: str, params: Dict[str, str]) -> List[Dict[str, Any]]:
        r = await self.client().get(f"{self.url}/rest/v1/{table}", params=params)
        r.raise_for_status()
        return r.json()

    async def insert(self, table: str, row: Dict[str, Any]) -> Dict[str, Any]:
        r = await self.client().post(f"{self.url}/rest/v1/{table}", json=row, headers={"Prefer": "return=representation"})
        r.raise_for_status()
        return r.json()[0]

    async def update(self, table: str, row_id: str, fields: Dict[str, Any]) -> Dict[str, Any] | None:
        r = await self.client().patch(f"{self.url}/rest/v1/{table}", params={"id": f"eq.{row_id}"}, json=fields,
                                      headers={"Prefer": "return=representation"})
        r.raise_for_status()
        rows = r.json()
        return rows[0] if rows else None

    async def delete(self, table: str, row_id: str) -> None:
        r = await self.client().delete(f"{self.url}/rest/v1/{table}", params={"id": f"eq.{row_id}"})
        r.raise_for_status()

    async def rpc(self, fn: str, **args: Any) -> Any:
        r = await self.client().post(f"{self.url}/rest/v1/rpc/{fn}", json=args)
        r.raise_for_status()
        return r.json() if r.content else None

    async def sign(self, path: str | None, seconds: int = 3600) -> str | None:
        if not path:
            return None
        r = await self.client().post(f"{self.url}/storage/v1/object/sign/autopilot/{path}", json={"expiresIn": seconds})
        if r.status_code != 200:
            return None
        return f"{self.url}/storage/v1{r.json()['signedURL']}"


db = _DB()


def admin_route(fn):
    async def wrapper(request: Request) -> Response:
        if not authenticate_admin(request):
            return error(request, 401, "AdminRequired", "Admin key required")
        ok, _ = rate_limit("autopilot", "admin", 240, 60)
        if not ok:
            return error(request, 429, "RateLimited", "Too many autopilot requests")
        if not db.configured and fn.__name__ not in ("catalog", "voices", "ideas", "script"):
            return error(request, 503, "NotConfigured", "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the backend")
        try:
            return await fn(request)
        except httpx.HTTPStatusError as e:
            return error(request, 502, "DatabaseError", e.response.text[:300])
        except LLMError as e:
            return error(request, 503, "LLMUnavailable", str(e))
        except (ValueError, KeyError, TypeError) as e:
            return error(request, 400, "BadRequest", str(e))
    wrapper.__name__ = fn.__name__
    return wrapper


async def _body(request: Request) -> Dict[str, Any]:
    raw = await request.body()
    if len(raw) > 256 * 1024:
        raise ValueError("request too large")
    import json
    data = json.loads(raw or b"{}")
    if not isinstance(data, dict):
        raise ValueError("JSON object expected")
    return data


# --------------------------------------------------------------------------- catalog, voices, AI helpers

@admin_route
async def catalog(request: Request) -> Response:
    return _ok({"styles": STYLES, "caption_styles": CAPTION_STYLES, "caption_positions": ["top", "middle", "bottom"],
                "moods": MOODS, "niches": NICHES, "platforms": PLATFORMS})


_voices: Dict[str, Any] = {"at": 0, "list": []}


@admin_route
async def voices(request: Request) -> Response:
    if time.time() - _voices["at"] > 86400 or not _voices["list"]:
        import edge_tts
        raw = await edge_tts.list_voices()
        out = []
        for v in raw:
            friendly = v.get("FriendlyName", "")
            out.append({"id": v["ShortName"], "name": v["ShortName"].split("-")[-1].replace("Neural", ""),
                        "gender": v.get("Gender", ""), "locale": v["Locale"],
                        "language": friendly.split(" - ", 1)[1] if " - " in friendly else v["Locale"]})
        _voices.update(at=time.time(), list=sorted(out, key=lambda x: (x["language"], x["id"])))
    q = (request.query_params.get("language") or "").lower()
    items = [v for v in _voices["list"] if not q or v["language"].lower().startswith(q) or v["locale"].lower() == q]
    return _ok({"count": len(items), "languages": len({v["language"] for v in _voices["list"]}), "voices": items})


IDEAS_SYSTEM = ("You are a short-form video strategist who finds ideas that get views on YouTube Shorts, Instagram "
                "Reels and TikTok. Ideas must be specific, have a curiosity gap, be factually safe, and fit in under "
                "a minute. Reply with JSON only.")


@admin_route
async def ideas(request: Request) -> Response:
    b = await _body(request)
    niche = str(b.get("niche") or "interesting facts")[:300]
    lang = str(b.get("language") or "English")[:40]
    n = max(1, min(int(b.get("count") or 10), 20))
    obj, res = await llm_router.complete_json(
        IDEAS_SYSTEM,
        f"Niche: {niche}\nAudience language: {lang}\nGive {n} fresh video ideas. Write title and hook in {lang}.\n"
        'Return {"ideas": [{"title": "...", "hook": "first spoken line", "why": "why it will get views"}]}',
        temperature=0.9, max_tokens=3000, budget_s=110.0)
    return _ok({"ideas": obj.get("ideas", [])[:n], "provider": res.provider})


SCRIPT_SYSTEM = ("You write narration for short vertical videos: a hook in the first two seconds, one idea per line, "
                 "concrete examples, a payoff and a short call to action. Facts must be accurate and mainstream; never "
                 "invent study names or numbers. Each line is 1-2 short spoken sentences (5-7 seconds). Reply with JSON only.")


@admin_route
async def script(request: Request) -> Response:
    b = await _body(request)
    topic = str(b.get("topic") or "").strip()[:500]
    if not topic:
        raise ValueError("topic is required")
    lang = str(b.get("language") or "English")[:40]
    seconds = max(15, min(int(b.get("seconds") or 60), 600))
    note = ("Hindi in Devanagari with common English words in English" if lang.lower() == "hindi" else
            "Hinglish: Hindi in Devanagari mixed with English words" if lang.lower() == "hinglish" else
            f"{lang}, natural spoken style, in its own script")
    obj, res = await llm_router.complete_json(
        SCRIPT_SYSTEM,
        f"Topic: {topic}\nNiche: {b.get('niche') or 'general'}\nLanguage: {note}\n"
        f"Length: about {seconds} seconds ({max(4, round(seconds / 6.5))} lines).\n"
        'Return {"title": "...", "lines": ["...", "..."], "description": "...", "hashtags": ["#..."]}',
        temperature=0.85, max_tokens=6000, budget_s=110.0)
    return _ok({**obj, "provider": res.provider})


# --------------------------------------------------------------------------- autopilots

@admin_route
async def autopilots_list(request: Request) -> Response:
    rows = await db.select("ap_autopilots", {"select": "*", "order": "created_at.desc"})
    return _ok(rows)


@admin_route
async def autopilots_save(request: Request) -> Response:
    b = await _body(request)
    row = {k: v for k, v in b.items() if k in AUTOPILOT_FIELDS}
    if b.get("id"):
        saved = await db.update("ap_autopilots", str(b["id"]), row)
        if not saved:
            return error(request, 404, "NotFound", "autopilot not found")
        return _ok(saved)
    if not row.get("name"):
        raise ValueError("name is required")
    return _ok(await db.insert("ap_autopilots", row), 201)


@admin_route
async def autopilots_delete(request: Request) -> Response:
    await db.delete("ap_autopilots", request.path_params["id"])
    return _ok({"deleted": request.path_params["id"]})


# --------------------------------------------------------------------------- jobs

JOB_LIST_COLUMNS = ("id,autopilot_id,kind,status,progress,stage,error,spec->>topic,spec->>style,spec->>language,"
                    "result->>title,result->>duration,publish,thumb_path,created_at,finished_at,attempts,worker_id")


@admin_route
async def jobs_list(request: Request) -> Response:
    limit = max(1, min(int(request.query_params.get("limit") or 50), 200))
    params = {"select": JOB_LIST_COLUMNS, "order": "created_at.desc", "limit": str(limit)}
    if request.query_params.get("autopilot"):
        params["autopilot_id"] = f"eq.{request.query_params['autopilot']}"
    rows = await db.select("ap_jobs", params)
    for r in rows:
        r["thumb_url"] = await db.sign(r.pop("thumb_path", None))
    return _ok(rows)


@admin_route
async def job_get(request: Request) -> Response:
    rows = await db.select("ap_jobs", {"id": f"eq.{request.path_params['id']}", "select": "*"})
    if not rows:
        return error(request, 404, "NotFound", "job not found")
    job = rows[0]
    job["video_url"] = await db.sign(job.get("video_path"))
    job["thumb_url"] = await db.sign(job.get("thumb_path"))
    return _ok(job)


@admin_route
async def jobs_create(request: Request) -> Response:
    b = await _body(request)
    spec = {k: v for k, v in (b.get("spec") or {}).items() if k in SPEC_FIELDS}
    if not spec.get("topic") and not spec.get("niche") and not b.get("story"):
        raise ValueError("give a topic, a niche or a story")
    row = {"kind": "make", "spec": spec}
    if b.get("story"):
        row["story"] = b["story"]
    return _ok(await db.insert("ap_jobs", row), 201)


@admin_route
async def job_regen(request: Request) -> Response:
    b = await _body(request)
    src = request.path_params["id"]
    regen = {k: b[k] for k in ("scene", "say", "image", "new_picture") if k in b}
    row: Dict[str, Any] = {"kind": "regen", "spec": {"source_job": src, "regen": regen,
                                                    "overrides": {k: v for k, v in (b.get("overrides") or {}).items() if k in SPEC_FIELDS}}}
    if b.get("story"):
        row["story"] = b["story"]
    return _ok(await db.insert("ap_jobs", row), 201)


@admin_route
async def job_publish(request: Request) -> Response:
    b = await _body(request)
    platforms = b.get("platforms") or {}
    if not isinstance(platforms, dict) or not platforms:
        raise ValueError("platforms is required, e.g. {\"youtube\": {\"privacy\": \"public\"}}")
    row = {"kind": "publish", "spec": {"source_job": request.path_params["id"], "platforms": platforms}}
    return _ok(await db.insert("ap_jobs", row), 201)


@admin_route
async def job_cancel(request: Request) -> Response:
    rows = await db.select("ap_jobs", {"id": f"eq.{request.path_params['id']}", "select": "status"})
    if not rows:
        return error(request, 404, "NotFound", "job not found")
    if rows[0]["status"] != "queued":
        return error(request, 409, "NotQueued", "only queued jobs can be canceled")
    return _ok(await db.update("ap_jobs", request.path_params["id"], {"status": "canceled"}))


@admin_route
async def status(request: Request) -> Response:
    rows = await db.select("ap_jobs", {"select": "status,worker_id,heartbeat_at", "order": "created_at.desc", "limit": "500"})
    counts: Dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    since = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(time.time() - 600))
    recent = await db.select("ap_jobs", {"select": "worker_id,heartbeat_at", "heartbeat_at": f"gte.{since}",
                                         "worker_id": "not.is.null"})
    return _ok({"counts": counts, "workers": sorted({r["worker_id"] for r in recent})})


# --------------------------------------------------------------------------- connected accounts (OAuth)

API_BASE = os.environ.get("AP_PUBLIC_API_BASE", "https://anydownloader-backend-vvbj.onrender.com").rstrip("/")
DASHBOARD = os.environ.get("AP_DASHBOARD_URL", "https://winplaybox.in/autopilot")


def _redirect_uri(platform: str) -> str:
    return f"{API_BASE}/oauth/autopilot/{platform}/callback"


def _env(*names: str) -> str:
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""


# What each platform needs. "connect" is True once its OAuth flow is implemented here.
PLATFORM_SETUP: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "label": "YouTube", "connect": True, "env": ["YT_CLIENT_ID", "YT_CLIENT_SECRET"],
        "steps": [
            "Google Cloud console: create a project and enable \"YouTube Data API v3\".",
            "OAuth consent screen: External; add your Google account as a test user.",
            "Credentials > Create OAuth client ID > Web application; add the redirect URI shown here.",
            "Put the client ID and secret on Render as YT_CLIENT_ID and YT_CLIENT_SECRET.",
        ],
        "note": "About 6 uploads/day on the default quota. Uploads stay private until Google audits the project.",
    },
    "instagram": {
        "label": "Instagram", "connect": False, "env": ["META_APP_ID", "META_APP_SECRET"],
        "steps": ["Meta for Developers: create a Business app with the Instagram API (Instagram Login).",
                  "Needs an Instagram Professional (Business or Creator) account.",
                  "Add the redirect URI shown here, then put META_APP_ID / META_APP_SECRET on Render."],
        "note": "Reels are published from a public video URL; the worker hosts it in Supabase Storage.",
    },
    "facebook": {
        "label": "Facebook Page", "connect": False, "env": ["META_APP_ID", "META_APP_SECRET"],
        "steps": ["Same Meta app as Instagram, with Facebook Login for Business.",
                  "Posts go to a Facebook Page you manage (not a personal profile)."],
        "note": "Your own Pages work in development mode without app review.",
    },
    "threads": {
        "label": "Threads", "connect": False, "env": ["THREADS_APP_ID", "THREADS_APP_SECRET"],
        "steps": ["Meta for Developers: add the Threads API use case to your app.",
                  "Add the redirect URI shown here, then put THREADS_APP_ID / THREADS_APP_SECRET on Render."],
        "note": "",
    },
    "tiktok": {
        "label": "TikTok", "connect": False, "env": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"],
        "steps": ["TikTok for Developers: create an app with Login Kit + Content Posting API.",
                  "Add the redirect URI shown here, then put TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET on Render."],
        "note": "Until TikTok audits the app, posts can only be private.",
    },
    "x": {
        "label": "X (Twitter)", "connect": False, "env": ["X_CLIENT_ID", "X_CLIENT_SECRET"],
        "steps": ["developer.x.com: create a project and app with OAuth 2.0 (read + write).",
                  "Add the redirect URI shown here, then put X_CLIENT_ID / X_CLIENT_SECRET on Render."],
        "note": "The free X API tier is very limited for posting video.",
    },
}


def _state_key() -> bytes:
    return (_env("WPB_VAULT_SECRET", "WPB_ADMIN_KEY") or "dev-only-state-key").encode()


def _sign(body: str) -> str:
    return base64.urlsafe_b64encode(hmac.new(_state_key(), body.encode(), hashlib.sha256).digest()).decode().rstrip("=")


def _make_state(platform: str) -> str:
    body = base64.urlsafe_b64encode(json.dumps(
        {"p": platform, "exp": int(time.time()) + 600, "n": secrets.token_urlsafe(8)}).encode()).decode().rstrip("=")
    return f"{body}.{_sign(body)}"


def _check_state(state: str, platform: str) -> bool:
    try:
        body, sig = state.split(".", 1)
        if not hmac.compare_digest(sig, _sign(body)):
            return False
        data = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        return data.get("p") == platform and data.get("exp", 0) > time.time()
    except Exception:
        return False


@admin_route
async def accounts_list(request: Request) -> Response:
    rows = await db.select("ap_social_accounts", {
        "select": "id,platform,external_id,name,avatar,status,error,created_at,updated_at", "order": "created_at.asc"})
    platforms = {}
    for k, v in PLATFORM_SETUP.items():
        platforms[k] = {"label": v["label"], "can_connect": v["connect"], "configured": all(_env(e) for e in v["env"]),
                        "env": v["env"], "steps": v["steps"], "note": v["note"], "redirect_uri": _redirect_uri(k),
                        "publishing": PLATFORMS.get(k) == "ready"}
    return _ok({"accounts": rows, "platforms": platforms})


@admin_route
async def accounts_connect(request: Request) -> Response:
    platform = request.path_params["platform"]
    setup = PLATFORM_SETUP.get(platform)
    if not setup:
        return error(request, 404, "NotFound", "unknown platform")
    if not setup["connect"]:
        return error(request, 501, "NotAvailable", f"{setup['label']} connect is coming next")
    if not all(_env(e) for e in setup["env"]):
        return error(request, 503, "NotConfigured", f"Set {' and '.join(setup['env'])} on the backend first")
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": _env("YT_CLIENT_ID"), "redirect_uri": _redirect_uri("youtube"), "response_type": "code",
        "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
        "access_type": "offline", "prompt": "consent select_account", "include_granted_scopes": "true",
        "state": _make_state("youtube")})
    return _ok({"url": url})


@admin_route
async def accounts_delete(request: Request) -> Response:
    await db.rpc("ap_delete_account", p_id=request.path_params["id"])
    return _ok({"deleted": request.path_params["id"]})


def _back(platform: str, ok: bool, msg: str = "") -> Response:
    q = urlencode({"connected" if ok else "connect_error": platform, **({"msg": msg[:200]} if msg else {})})
    return RedirectResponse(f"{DASHBOARD}?{q}#accounts", status_code=302)


async def oauth_callback(request: Request) -> Response:
    """Public: the platform sends the admin's browser here after sign-in. Trust comes from the signed state."""
    platform = request.path_params["platform"]
    q = request.query_params
    if not _check_state(q.get("state", ""), platform):
        return _back(platform, False, "Sign-in link expired or invalid. Try Connect again.")
    if q.get("error"):
        return _back(platform, False, q.get("error_description") or q["error"])
    if platform != "youtube":
        return _back(platform, False, "not available yet")
    if not db.configured:
        return _back(platform, False, "Backend is missing Supabase settings.")
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            tok = (await c.post("https://oauth2.googleapis.com/token", data={
                "code": q.get("code", ""), "client_id": _env("YT_CLIENT_ID"), "client_secret": _env("YT_CLIENT_SECRET"),
                "redirect_uri": _redirect_uri("youtube"), "grant_type": "authorization_code"})).json()
            if "access_token" not in tok:
                return _back(platform, False, tok.get("error_description") or tok.get("error") or "token exchange failed")
            me = (await c.get("https://www.googleapis.com/youtube/v3/channels", params={"part": "snippet", "mine": "true"},
                              headers={"Authorization": f"Bearer {tok['access_token']}"})).json()
        items = me.get("items") or []
        if not items:
            return _back(platform, False, "This Google account has no YouTube channel.")
        ch = items[0]
        # The worker refreshes access tokens itself, so it needs the client pair alongside the refresh token.
        token = {"client_id": _env("YT_CLIENT_ID"), "client_secret": _env("YT_CLIENT_SECRET"),
                 "token_uri": "https://oauth2.googleapis.com/token"}
        if tok.get("refresh_token"):
            token["refresh_token"] = tok["refresh_token"]
        await db.rpc("ap_save_account", p_owner=None, p_platform="youtube", p_external_id=ch["id"],
                     p_name=ch["snippet"].get("title", ch["id"]),
                     p_avatar=ch["snippet"].get("thumbnails", {}).get("default", {}).get("url"), p_token=token)
        return _back(platform, True)
    except httpx.HTTPError as e:
        return _back(platform, False, f"network error: {type(e).__name__}")


routes_autopilot = [
    Route("/admin/autopilot/catalog", catalog, methods=["GET"]),
    Route("/admin/autopilot/voices", voices, methods=["GET"]),
    Route("/admin/autopilot/ideas", ideas, methods=["POST"]),
    Route("/admin/autopilot/script", script, methods=["POST"]),
    Route("/admin/autopilot/autopilots", autopilots_list, methods=["GET"]),
    Route("/admin/autopilot/autopilots", autopilots_save, methods=["POST"]),
    Route("/admin/autopilot/autopilots/{id}/delete", autopilots_delete, methods=["POST"]),
    Route("/admin/autopilot/jobs", jobs_list, methods=["GET"]),
    Route("/admin/autopilot/jobs", jobs_create, methods=["POST"]),
    Route("/admin/autopilot/jobs/{id}", job_get, methods=["GET"]),
    Route("/admin/autopilot/jobs/{id}/regen", job_regen, methods=["POST"]),
    Route("/admin/autopilot/jobs/{id}/publish", job_publish, methods=["POST"]),
    Route("/admin/autopilot/jobs/{id}/cancel", job_cancel, methods=["POST"]),
    Route("/admin/autopilot/status", status, methods=["GET"]),
    Route("/admin/autopilot/accounts", accounts_list, methods=["GET"]),
    Route("/admin/autopilot/accounts/connect/{platform}", accounts_connect, methods=["POST"]),
    Route("/admin/autopilot/accounts/{id}/delete", accounts_delete, methods=["POST"]),
    Route("/oauth/autopilot/{platform}/callback", oauth_callback, methods=["GET"]),
]
