# GravityClaw v2 + Zero-Trust Gateway

Backend: `anydownloader/backend` (Render: `anydownloader-backend-vvbj.onrender.com`).
Frontend: `gravityclaw.winplaybox.in` (repo `Winplaybox/gravityclaw`) — UI is built per `ANTIGRAVITY_GRAVITYCLAW_PROMPT.md`.

## 1. Security model (applies to every endpoint, v1 + v2)

| Rule | How |
|---|---|
| Every protected call needs a fresh token | `POST /api/v2/auth/token` → `wpb2_…` token |
| Token dies after ONE use | atomic burn on first accepted request (Redis `SET NX`, Upstash, or memory) — replay = 401 |
| Short life | 60 s default (`WPB_TOKEN_TTL`, max 300) |
| Bound to caller | scopes · Origin header domain · client IP fingerprint · optional endpoint (`aud`) · optional SHA-256 of exact body (`body_sha256`) |
| Admin power is never free | `admin:all`, `social:publish`, `blog:cron`, `video:master`, `workflow:execute` only with `X-Admin-Key` (≥32 chars) or Supabase admin JWT |
| Origin from headers only | body `origin` field is ignored (old S1 hole closed) |
| No hard-coded secrets | missing `WPB_VAULT_SECRET` on Render → server refuses to boot |
| Key rotation | `WPB_VAULT_SECRET=new,old` |
| Brute-force | 5 failed admin attempts / 15 min / IP → 429 lockout |
| Rate limits | token issue 40/min/IP · generate+refine 12/min & 300/day/IP · score 60/min |
| Admin routes | `/admin/*`, `/api/v1/system/*` require admin key |
| CORS | only `*.winplaybox.in`, latestnewsnx.com, buzzstormnow.com, Chrome extension ids (+ `WPB_CORS_EXTRA_ORIGINS`) |
| Headers | nosniff, X-Frame-Options DENY, Referrer-Policy, Permissions-Policy, HSTS (prod), `X-Request-ID` on every response |
| SSRF | `/api/proxy-image` only fetches allow-listed CDN hosts, no redirects |
| Body limits | 64 KB on GravityClaw, 256 KB default on decorated routes |

Token anatomy: `wpb2_<header>.<claims>.<HMAC-SHA256>`; claims = `jti, sub, adm, dom, scp, iat, nbf, exp, ipf, aud?, bh?`.

### Public scopes (any approved origin, rate limited)
`gravityclaw:generate prompt:generate workflow:generate subtitles:generate audio:extract voice:tts visuals:search visuals:generate price:read`

## 2. GravityClaw API

### `GET /api/v2/gravityclaw/catalog` (public, ETag)
Categories (8), targets (31 tools: Midjourney, FLUX, SDXL/ComfyUI, GPT-Image, Gemini Image, Ideogram, Leonardo, Veo 3, Sora 2, Kling, Runway, Hailuo, Wan, system/task prompts, Custom GPT, coding agent, app builder, n8n, Suno, Udio, ElevenLabs SFX, voice-over, Shorts script, YouTube long, SEO blog, captions, ad copy, email, logo, UI screen, thumbnail), 23 presets with form fields, styles, tones, languages.

### `POST /api/v2/auth/token`
```json
{ "scope": "gravityclaw:generate", "aud": "/api/v2/gravityclaw/generate", "body_sha256": "<hex of exact body>" }
```
→ `{ "token": "wpb2_…", "expires_in": 60, "single_use": true }`

### `POST /api/v2/gravityclaw/generate`  (Bearer token)
```json
{
  "requirement": "neon samurai on a rainy Mumbai rooftop",
  "target": "auto | midjourney | veo3 | suno | coding_agent | …",
  "preset_id": "product_photo", "fields": { "product": "steel bottle" },
  "mode": "generate | enhance",
  "variants": 3, "creativity": 0.7, "detail": "concise | standard | max",
  "style": "cinematic photorealism", "tone": "dramatic",
  "language": "Hindi", "explain_language": "Hinglish",
  "aspect_ratio": "9:16", "params": { "stylize": 300 }, "seed": 42, "nocache": false
}
```
Response: `title, intent_summary, target{id,name,category,tool_url}, prompt, negative_prompt, lyrics, parameters (validated), copy_ready (paste-ready incl. --flags / Style+Lyrics / Negative), structure, variants[{id,label,prompt,negative_prompt,copy_ready,quality}], quality{score,grade,checks,suggestions}, tips, follow_up_questions, engine{mode: ai|fallback, provider, model, latency_ms, cached}, request_id`.

### `POST /api/v2/gravityclaw/refine`
`{ "prompt", "instruction": "make it night time", "target", "negative_prompt?", "lyrics?" }` → same shape + `refined_from`.

### `POST /api/v2/gravityclaw/score`
`{ "prompt", "target" }` → local quality score + suggestions (no LLM, instant).

### `GET /api/v2/gravityclaw/health`
Provider availability + token store backend (no secrets).

Errors are always `{ "ok": false, "error": { "code", "message" }, "request_id" }`.

## 3. Engine
- LLM router: Gemini → Groq → OpenRouter → Cerebras → Pollinations (no key) with circuit breaker (3 fails → 90 s cooldown), 55 s budget, 8 concurrent calls.
- Strict JSON contract, one auto-repair retry, prompt-injection fencing (`<requirement>` treated as data), policy refusals.
- Parameters are re-validated by code (ranges, enums, aspect ratios); Midjourney `--flags` built by code, LLM-written flags stripped.
- Local scorer (target-specific checklist + length fit) blended 65/35 with model self-score.
- LRU cache (300 entries, 1 h); offline template fallback if every provider fails (never cached).

## 4. Deploy (Render)
1. Env vars: `WPB_VAULT_SECRET` (48+ chars), `WPB_ADMIN_KEY` (40+ chars), `WPB_ENV=production`, at least one of `GEMINI_API_KEY` / `GROQ_API_KEY` / `OPENROUTER_API_KEY`.
2. Free burn store for multiple workers: Upstash Redis → `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`. (Render free = 1 worker, memory store is OK.)
3. `pip install -r backend/requirements.txt` (adds `redis`).
4. Tests: `pytest backend/tests_v2 -q` (25 tests).
5. Admin panel must now send `X-Admin-Key` when requesting `admin:all` tokens (see Antigravity prompt, Task B).

## 5. Breaking changes
- `/api/v1/auth/token` with `scope: admin:all` now needs `X-Admin-Key` → admin.html must be updated.
- Old `wpb_` tokens are no longer accepted (new prefix `wpb2_`).
- `/admin/*` and `/api/v1/system/diag` need `X-Admin-Key`.
- CORS no longer `*`.

## 6. AI Agent Universe (added 2026-10-30)
Source: `AI_Agent_Universe_Master_Catalog.xlsx` → `python backend/scripts/build_agent_universe.py <xlsx>` → `backend/data/agent_universe_v3.json` (1,000 domain agents = 100 domains × 10 functions, 200 script agents in 22 families, 100 domains, 30 output types, workflows, config lists).
Expertise comes from playbooks in `services/gravityclaw/agent_universe.py` (10 function playbooks, 22 script-family craft rules, regulated-domain guardrails for Healthcare/Wellness/Finance/Legal/Public Services, output-type → target mapping).

- `GET /api/v2/gravityclaw/agents?q=&kind=agent|script&domain=&family=&function=&group=&limit<=50&offset=` (public, 120/min/IP)
- `GET /api/v2/gravityclaw/agents/facets`, `GET /api/v2/gravityclaw/agents/{id}` (summary + full profile)
- `POST /api/v2/gravityclaw/generate|refine` accept `agent_id`, `output_type`, `workflow`, `platform`, `audience`; with `target: "auto"` the agent's default tool is used and its profile is injected into the system prompt.
- `POST /api/v1/gravityclaw/prompt`:
  - Mode A (`target` / `preset_id` / `engine: "prompt"`): returns the v2 prompt result + legacy fields.
  - Mode B (default): topic → AI script written by the chosen agent (`agent_id`, else best match for `domain`, else SCR-0002 Shorts writer) → Antigravity storyboard pipeline. Adds `agent`, `ai_script`, `script_engine` (`ai | user_script | template`), AI hook + hashtags, fact-check warnings.
