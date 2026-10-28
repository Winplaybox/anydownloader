"""
Zero-Trust Ephemeral Token Security Vault
-----------------------------------------
Features:
1. Strict Domain / Origin Whitelisting.
2. Single-Use Tokens (Burned immediately upon first consumption).
3. 60-Second Time-To-Live (TTL).
4. Granular Scope Enforcement.
5. Replay Attack Prevention (jti tracking with automated cleanup).
"""

import os
import time
import uuid
import hmac
import hashlib
import json
import base64
from typing import Dict, Any, Optional, Set, Tuple

# Secret key for HMAC signing (can be overridden by environment variable)
VAULT_SECRET = os.environ.get("WPB_VAULT_SECRET", "winplaybox_sovereign_zero_trust_vault_key_2026_x99")

# Whitelist of approved domains allowed to request and use tokens
APPROVED_DOMAINS = {
    "ovd.winplaybox.in",
    "winplaybox.in",
    "admin.winplaybox.in",
    "pricewatch.winplaybox.in",
    "latestnewsnx.winplaybox.in",
    "gravityclaw.winplaybox.in",
    "omni.winplaybox.in",
    "localhost",
    "127.0.0.1",
    "anydownloader-backend-vvbj.onrender.com"
}

# Granular capabilities / scopes map
VALID_SCOPES = {
    "subtitles:generate",
    "audio:extract",
    "voice:tts",
    "visuals:search",
    "video:master",
    "social:publish",
    "prompt:generate",
    "workflow:execute",
    "price:read",
    "blog:cron",
    "admin:all"
}

class TokenVault:
    def __init__(self):
        # In-memory storage for consumed tokens: { jti: expiry_timestamp }
        self._consumed_tokens: Dict[str, float] = {}
        # Clean up interval tracking
        self._last_cleanup = time.time()

    def _cleanup_expired(self):
        """Purge expired token records to prevent memory leak."""
        now = time.time()
        if now - self._last_cleanup < 30:
            return
        self._last_cleanup = now
        expired_jtis = [jti for jti, exp in self._consumed_tokens.items() if exp < now]
        for jti in expired_jtis:
            del self._consumed_tokens[jti]

    def _clean_domain(self, origin_or_domain: str) -> str:
        """Extract clean hostname from origin or domain URL."""
        if not origin_or_domain:
            return ""
        d = origin_or_domain.strip().lower()
        if "://" in d:
            d = d.split("://", 1)[1]
        if "/" in d:
            d = d.split("/", 1)[0]
        if ":" in d:
            d = d.split(":", 1)[0]
        return d

    def is_domain_allowed(self, domain: str) -> bool:
        clean = self._clean_domain(domain)
        if not clean:
            return False
        # Direct match or subdomain of winplaybox.in
        if clean in APPROVED_DOMAINS:
            return True
        if clean.endswith(".winplaybox.in"):
            return True
        return False

    def issue_token(self, origin: str, scope: str, client_ip: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Issues an ephemeral single-use token valid for 60 seconds.
        """
        self._cleanup_expired()
        clean_domain = self._clean_domain(origin)
        
        if not self.is_domain_allowed(clean_domain):
            return False, {
                "error": "ForbiddenDomain",
                "message": f"Domain '{clean_domain}' is not authorized to access Winplaybox Sovereign Gateway."
            }

        # Check scope validity
        scopes_requested = [s.strip() for s in scope.split(",") if s.strip()]
        for s in scopes_requested:
            if s not in VALID_SCOPES:
                return False, {
                    "error": "InvalidScope",
                    "message": f"Requested scope '{s}' is not recognized."
                }

        now = time.time()
        jti = str(uuid.uuid4())
        payload = {
            "jti": jti,
            "domain": clean_domain,
            "scopes": scopes_requested,
            "iat": int(now),
            "exp": int(now + 60),  # strictly 60 seconds
            "ip": client_ip or "unknown"
        }

        # Serialize payload
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode('utf-8').rstrip('=')

        # Sign payload with HMAC-SHA256
        sig = hmac.new(VAULT_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')

        token = f"wpb_{payload_b64}.{sig_b64}"

        return True, {
            "token": token,
            "expires_in": 60,
            "single_use": True,
            "scopes": scopes_requested,
            "domain": clean_domain
        }

    def verify_and_burn_token(self, token: str, required_scope: str, request_origin: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Verifies cryptographic integrity, checks origin match, validates scope,
        and IMMEDIATELY BURNS the token so it cannot ever be used again.
        """
        self._cleanup_expired()

        if not token or not token.startswith("wpb_"):
            return False, "Malformed token structure.", None

        raw = token[4:]
        parts = raw.split('.')
        if len(parts) != 2:
            return False, "Invalid token format.", None

        payload_b64, sig_b64 = parts[0], parts[1]

        # Verify Signature
        expected_sig = hmac.new(VAULT_SECRET.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return False, "Invalid cryptographic token signature.", None

        # Decode Payload
        try:
            # Re-pad base64
            padded = payload_b64 + '=' * (-len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode('utf-8'))
        except Exception:
            return False, "Corrupted token payload.", None

        now = time.time()
        # 1. Expiration check
        if payload.get("exp", 0) < now:
            return False, "Token has expired (60s lifetime exceeded).", None

        # 2. Replay check (Single-Use enforcement)
        jti = payload.get("jti")
        if not jti or jti in self._consumed_tokens:
            return False, "Token has already been consumed (Replay attack blocked).", None

        # 3. Domain / Origin match check
        clean_req_origin = self._clean_domain(request_origin)
        token_domain = payload.get("domain", "")
        if clean_req_origin and token_domain != clean_req_origin:
            return False, f"Origin mismatch: token was issued for '{token_domain}', but requested from '{clean_req_origin}'.", None

        # 4. Scope verification
        scopes = payload.get("scopes", [])
        if "admin:all" not in scopes and required_scope not in scopes:
            return False, f"Forbidden: token lacks required scope '{required_scope}'.", None

        # === IMMEDIATELY BURN TOKEN ===
        self._consumed_tokens[jti] = payload.get("exp", now + 60)

        return True, "Authorized and token burned.", payload

token_vault = TokenVault()
