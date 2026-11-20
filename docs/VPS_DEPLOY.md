# OVD on the Hostinger VPS (KVM 2) — go-live runbook

Stack (one `docker compose`): **caddy** (TLS for `api.winplaybox.in`) → **api** (FastAPI/Starlette) →
**redis** (private, password) ← **editor-worker** (FFmpeg / Whisper / Kokoro renders). The frontend
`ovd.winplaybox.in` stays a static site and calls `https://api.winplaybox.in`.

There is no public `workers.winplaybox.in`: workers only pull jobs from Redis and need no inbound port.

## 1. DNS (Hostinger hPanel → DNS)

| Type | Name | Value |
|---|---|---|
| A | `api` | VPS IPv4 |

Leave `ovd` pointing at the current static frontend host.

## 2. One-time server setup (as root over SSH)

```sh
apt-get update && apt-get -y upgrade
curl -fsSL https://get.docker.com | sh
ufw default deny incoming && ufw allow OpenSSH && ufw allow 80/tcp && ufw allow 443/tcp && ufw allow 443/udp && ufw --force enable
git clone https://github.com/Winplaybox/anydownloader /opt/ovd
cd /opt/ovd
cp deploy/env.production.example .env && chmod 600 .env
nano .env        # fill every secret (one `python3 -c "import secrets;print(secrets.token_urlsafe(48))"` each)
mkdir -p cookies # optional yt-dlp cookies, read-only in the container
```

No container publishes a port except Caddy (80/443), so Docker's iptables rules cannot expose Redis or the API.

## 3. Start

```sh
docker compose up -d --build
docker compose ps                          # all healthy
curl -fsS https://api.winplaybox.in/health
curl -fsS https://api.winplaybox.in/api/editor/health   # ffmpeg:true, fonts listed, queue_mode:redis
docker compose logs -f editor-worker       # "editor worker ... started"
```

The API refuses to start in production if a required secret is missing or weak (see logs).

## 4. Google Sign-In

Google Cloud Console → Credentials → OAuth client (Web) → *Authorized JavaScript origins*:
`https://ovd.winplaybox.in`. Put the same client id in `.env` as `GOOGLE_CLIENT_ID`
(the frontend already uses `259545227984-…apps.googleusercontent.com`). The server rejects Google tokens
issued for any other client id and any unverified email.

## 5. Dodo Payments LIVE

1. Dodo dashboard → switch to **Live mode**.
2. Create the live products (plans, yearly plans, day pass, packs) and copy each `pdt_…` into
   `DODO_PRODUCT_*` in `.env`. A plan without a live id cannot be bought (the checkout says so).
3. Developer → API keys → live key → `DODO_PAYMENTS_API_KEY`.
4. Developer → Webhooks → Add endpoint `https://api.winplaybox.in/api/payments/dodo/webhook` with the events
   listed in `deploy/env.production.example`; copy the `whsec_…` into `DODO_PAYMENTS_WEBHOOK_SECRET`.
5. `docker compose up -d` to reload env, then in Dodo send a test event → API logs show
   `Dodo webhook … -> …`. A bad signature returns 401, a replay returns `duplicate`.
6. Make one real small purchase (e.g. the cheapest pack) with your own account and verify the credits,
   then refund it from Dodo and verify the credits are clawed back.

Payment rules the code enforces: credits are granted only by a verified `payment.succeeded`, exactly once per
payment id; subscription events only change plan status; refunds/disputes reverse the grant once; buying
requires a signed-in account (a guest cookie can be lost).

## 6. Integration tokens (Make.com, n8n, Colab, cron)

Never use `ADMIN_API_KEY` in an integration. Create a scoped, revocable token:

```sh
curl -s -X POST https://api.winplaybox.in/admin/ovd/service-tokens \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"name":"make.com dhrusa","scopes":["media:resolve","media:download"],"ttl_days":365}'
```

Use it as `X-API-Key: ovd_st_…`. Scopes: `media:resolve`, `media:download`, `media:upload`, `editor:render`,
`editor:read`, `admin:read`. List: `GET /admin/ovd/service-tokens`; revoke: `POST /admin/ovd/service-tokens/{id}/revoke`.
Signing in on OVD with a Google-verified email listed in `WPB_ADMIN_EMAILS` also counts as admin.

Other admin endpoints: `POST /admin/ovd/credits/grant` (`{"user":"email|username|id","amount":10,"reason":"…"}`),
`GET /admin/ovd/payments` (grants, webhook log, subscriptions).

## 7. Backups and updates

```sh
crontab -e   # 17 3 * * * /opt/ovd/deploy/backup.sh >> /var/log/ovd-backup.log 2>&1
```

Update: `cd /opt/ovd && git pull && docker compose up -d --build`. Rollback: `git checkout <previous-sha> && docker compose up -d --build`.
Restore: stop the stack, copy the `.db` files from a backup tarball into the `ovd_data` volume (`/data/db`, `/data/jobs`), start.

## 8. Capacity on KVM 2

Two vCPUs: one render at a time (`EDITOR_CONCURRENCY=1`), up to `EDITOR_MAX_PENDING=25` jobs queued; beyond that
uploads get a clear "busy, try again" (503) instead of piling up. Watch `docker stats`; raise concurrency only
after measuring a render's real CPU/RAM.

## 9. After go-live

- Render.com service: suspend it once `api.winplaybox.in` is healthy (the keep-alive workflow is retired).
- The hourly health monitor now checks `https://api.winplaybox.in`.
