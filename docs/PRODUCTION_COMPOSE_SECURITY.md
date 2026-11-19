# Production Compose security configuration

## Required environment variables

Set these in the deployment environment; do not commit a populated `.env` file:

- `ADMIN_API_KEY`: high-entropy admin key (at least 32 characters).
- `TOKEN_HMAC_SECRET`: signing secret for legacy token flows.
- `EXTENSION_SECRET_KEY`: extension signing secret.
- `WPB_VAULT_SECRET`: token vault key(s); production keys must be at least 32 characters.
- `EXTENSION_SECRET_KEY`: extension signing secret. The API no longer ships a source-code fallback; if missing, extension-key authentication will fail closed.

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
