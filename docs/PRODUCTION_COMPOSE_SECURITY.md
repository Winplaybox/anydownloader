# Production Compose security configuration

## Required environment variables
Set these in the deployment environment; do not commit a populated `.env` file:

- `ADMIN_API_KEY`: high-entropy admin key (at least 32 characters).
- `TOKEN_HMAC_SECRET`: signing secret for legacy token flows.
- `EXTENSION_SECRET_KEY`: extension signing secret.
- `WPB_VAULT_SECRET`: token vault key(s); production keys must be at least 32 characters.
- `EXTENSION_SECRET_KEY`: extension signing secret. The API no longer ships a source-code fallback; if missing, extension-key authentication will fail closed.
- `PUBLIC_BASE_URL`: canonical HTTPS base URL used when generating temporary public-media links (for example, `https://api.example.com`). In production, this is mandatory; the API will not derive public URLs from request Host or forwarded headers.

Generate a secret locally with:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Generate distinct secrets for each variable. Do not put secret values in logs, pull requests, or source control.

## Network changes

- Redis no longer publishes port 6379 to the host. It is accessible only from the Compose network.
- API binds to localhost by default, suitable for a host reverse proxy.
- Set `API_BIND_ADDRESS=0.0.0.0` only if direct host exposure is intentional; secure it with firewall and TLS configuration.

## Rollout

This Compose file fails when required secrets are missing. Before deploying, back up the current environment and verify the reverse proxy's upstream port. This change has not been deployed.

## Forwarded client IP headers

The API does not trust forwarded IP headers by default (`WPB_TRUST_PROXY=0`). Set `WPB_TRUST_PROXY=1` only when the public reverse proxy overwrites `X-Forwarded-For`, `X-Real-IP`, and related client-IP headers and direct access to the API is blocked. This affects IP-based rate limits, admin lockout, and IP-bound token checks.

## Temporary media public URL

Set `PUBLIC_BASE_URL` to the canonical public HTTPS host. Temporary-media uploads return links from this value and never use client-supplied forwarded-host headers. Production upload requests fail with `503` when the value is missing or invalid.
