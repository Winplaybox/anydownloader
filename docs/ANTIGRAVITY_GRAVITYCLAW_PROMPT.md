# Antigravity Task — GravityClaw v2 Frontend + Admin Security Update

You are a principal frontend engineer + product designer. The backend is DONE and tested — do not modify anything in `anydownloader/backend/` except if a test proves a bug (then report it, do not silently change contracts).

Read first:
- `anydownloader/docs/GRAVITYCLAW_V2.md` (API + security contract — source of truth)
- `anydownloader/docs/clients/wpb-gateway-client.js` (use this client; do not write your own token logic)
- `GET /api/v2/gravityclaw/catalog` response (drives the whole UI — never hard-code targets/presets)

Hard rules
1. Every POST goes through `gateway.post(path, body)` → fresh single-use token bound to path + exact body. Never reuse a token, never store tokens.
2. No fake data, no simulated responses, no placeholder "success" messages. If the API errors, show the real `error.message` + `request_id`.
3. Use Spectra UI (`@winplaybox/react`, `@winplaybox/tokens`, `@winplaybox/icons`) for all components and tokens. No hard-coded colors/spacing. No emojis in UI.
4. Zero console errors, zero ESLint errors, Lighthouse ≥ 95 (Performance, Accessibility, Best Practices, SEO), WCAG 2.1 AA, keyboard-only usable.
5. Mobile-first (360 px) → desktop. Dark + light themes.

---

## Task A — gravityclaw.winplaybox.in (repo `Winplaybox/gravityclaw`)

### Layout
- **Left / top: Builder**
  - Category tabs from `catalog.categories` (Image, Video, Chat/LLM, Code & App Agents, Music, Voice, Content, Design).
  - "Start from a preset" grid filtered by category (`catalog.presets`): card = name + description. Selecting a preset renders its `fields` as a form (text, textarea, select) with required markers.
  - Free-text "What do you want to create?" textarea (max 4000 chars, live counter) — always available; when a preset is chosen it becomes "Extra notes".
  - Target tool select ("Auto-detect" default + `catalog.targets` filtered by category, show tool name).
  - Mode toggle: Generate / Enhance my prompt.
  - Advanced (collapsible): variants 1-5, creativity slider 0-1, detail (concise/standard/max), style (combobox from `catalog.styles`, free text allowed), tone, language, explain_language (default "Hinglish" option available), aspect ratio (only if target has an aspect param), dynamic param controls generated from the selected target's `params` schema (int/float → slider+number with min/max, enum → select, bool → switch), seed.
  - Primary button "Generate" (Ctrl/Cmd+Enter). Disable while running; show elapsed time; allow Cancel (AbortController).
- **Right / bottom: Result**
  - Header: title, intent_summary, target badge with "Open in <tool>" link (`target.tool_url`, rel=noopener), engine badge (AI provider or "Offline template" warning when `engine.mode === "fallback"` with a Regenerate button).
  - Quality ring: `quality.score` + grade; expandable checklist (pass/fail) + suggestions.
  - Variant tabs (`variants[]`): each shows `copy_ready` in a monospace block with **Copy** (clipboard API + toast), prompt / negative / lyrics sub-sections, its own score.
  - Parameters table, structure breakdown chips, tips list, follow-up questions as clickable chips that append to the requirement and regenerate.
  - **Refine bar**: input "Change something…" + quick chips (Shorter, More detailed, Night time, More cinematic, Hindi text, Remove text) → `POST /api/v2/gravityclaw/refine` with current variant's prompt/negative/lyrics/target.
  - **Score my prompt** panel: paste any prompt + target → `/api/v2/gravityclaw/score`, live (debounced 600 ms, only on blur/explicit click to respect rate limits).
- **History**: last 30 results in IndexedDB (prompt text only, never tokens), searchable, re-open, delete, export JSON.
- Share: "Copy link" encodes requirement+target+preset in URL query (not the result).

### UX states
Loading skeletons; 401/403 → "Session check failed, retrying" with a single automatic retry (new token); 429 → show cooldown from message; 422 → policy message; 503 → engine busy with retry. Offline detection banner.

### SEO / content
SSR or pre-rendered landing with H1 "GravityClaw — AI Prompt Generator for Any Tool", sections per category, FAQ (FAQPage JSON-LD), SoftwareApplication JSON-LD, OG/Twitter cards, sitemap, robots, canonical. Pages per preset (`/presets/<id>`) pre-rendered for long-tail SEO. Legal pages: privacy, terms.

### Tests
Vitest + Testing Library for form generation from catalog schema, param controls, error states; Playwright e2e against a local backend (`uvicorn main:app --app-dir backend`) covering: preset → generate → copy, refine, replay protection (second call with same token must fail — assert by calling fetch manually), rate-limit message.

---

## Task B — winplaybox.in/admin.html security update (repo `Winplaybox/winplayboxsite`)

1. Add an **Admin unlock** modal on load: input for admin key → `gateway.setAdminKey(key)` (sessionStorage only). Validate by requesting an `admin:all` token; on 401 show error, on 429 show lockout message. Add "Lock" button that clears it.
2. Replace every existing `fetch(\`${BACKEND_BASE}/api/v1/auth/token\` …)` + Bearer pattern with `gateway.post(path, body, { scope: 'admin:all' })` (one token per request). Remove any `origin` field from token request bodies.
3. All calls to `/admin/*` must send `X-Admin-Key` (use `adminHeaders()` from the client).
4. Point the "GravityClaw Universal Script & Reasoning Studio" section to the new v2 endpoints (generate/refine) with the same UI contract as Task A (reuse components).
5. Remove `index.html` duplicate of `admin.html` (serve admin only at `/admin.html`, add `<meta name="robots" content="noindex,nofollow">`), add cache-busting `?v=<build hash>` to scripts/styles.
6. Remove every simulated value the admin shows as real (fake YouTube IDs, fake queue stats). If an endpoint is not implemented yet, show "Not connected yet" instead of fake success.

## Definition of done
- [ ] All flows work against production backend after env vars are set.
- [ ] No token ever reused; no secrets in localStorage, code or git.
- [ ] Lighthouse ≥ 95 ×4 on mobile; axe: 0 violations.
- [ ] Unit + e2e tests pass in CI (GitHub Actions).
- [ ] Short CHANGELOG entry + screenshots (mobile + desktop, light + dark).
