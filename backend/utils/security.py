import os
import re
import time
import hmac
import hashlib
import json
import base64
import socket
import ipaddress
import urllib.parse
from typing import Dict, Any, Optional

DOWNLOAD_SECRET = (
    os.environ.get("DOWNLOAD_SIGNING_SECRET", "").strip()
    or os.environ.get("TOKEN_HMAC_SECRET", "").strip()
    or (os.environ.get("WPB_VAULT_SECRET", "").split(",")[0].strip() if os.environ.get("WPB_VAULT_SECRET") else "")
)
# Only configured environment secrets are accepted for signature verification.
POSSIBLE_DOWNLOAD_SECRETS = list(dict.fromkeys([
    s for s in [
        DOWNLOAD_SECRET,
        os.environ.get("DOWNLOAD_SIGNING_SECRET", "").strip(),
        os.environ.get("TOKEN_HMAC_SECRET", "").strip(),
        os.environ.get("WPB_VAULT_SECRET", "").split(",")[0].strip() if os.environ.get("WPB_VAULT_SECRET") else "",
    ] if s
]))
# Allowed CDN Domains for Upstream Streaming (SSRF Guard)
ALLOWED_CDN_DOMAINS = [
    "twimg.com",
    "video.twimg.com",
    "pbs.twimg.com",
    "twitter.com",
    "x.com",
    "googlevideo.com",
    "ytimg.com",
    "youtube.com",
    "ggpht.com",
    "googleusercontent.com",
    "fbcdn.net",
    "cdninstagram.com",
    "instagram.com",
    "facebook.com",
    "fbsbx.com",
    "tiktokcdn.com",
    "tiktokcdn-us.com",
    "tiktokcdn-eu.com",
    "tiktokcdn-in.com",
    "tiktokv.com",
    "tiktok.com",
    "ibytedtos.com",
    "byteoversea.com",
    "byteimg.com",
    "snssdk.com",
    "redd.it",
    "reddit.com",
    "redditmedia.com",
    "pinimg.com",
    "pinterest.com",
    "vimeocdn.com",
    "vimeo.com",
    "sndcdn.com",
    "soundcloud.com",
    "akamaized.net",
    "cloudfront.net",
    "fastly.net",
]

# Blocked Private & Link-Local IP Networks
PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

def is_safe_cdn_host(hostname: str) -> bool:
    """Checks if the hostname matches allowed media CDN domains."""
    if not hostname:
        return False
    host_lower = hostname.lower()
    return any(host_lower == d or host_lower.endswith("." + d) for d in ALLOWED_CDN_DOMAINS)

def is_ip_allowed(ip_str: str) -> bool:
    """Returns False if IP is private, loopback, link-local, or reserved."""
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            return False
        for net in PRIVATE_NETWORKS:
            if ip in net:
                return False
        return True
    except Exception:
        return False

def verify_safe_upstream_url(target_url: str) -> bool:
    """Reject malformed URLs and obvious local/private destinations before fetching.

    This is a static validation layer. DNS resolution and connection-time IP pinning
    must also be enforced by the HTTP client to fully prevent DNS-rebinding SSRF.
    """
    if not isinstance(target_url, str) or not target_url:
        return False
    target_clean = target_url.strip()
    if target_clean != target_url or any(ord(ch) < 32 for ch in target_url):
        return False

    # Allow only explicit application-relative API paths (not protocol-relative URLs).
    if target_clean.startswith("/"):
        if target_clean.startswith("//") or "\\" in target_clean:
            return False
        path = urllib.parse.urlsplit(target_clean).path
        return path.startswith("/api/") and not any(seg in (".", "..") for seg in path.split("/"))

    try:
        parsed = urllib.parse.urlsplit(target_clean)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        # urlsplit.hostname handles bracketed IPv6 correctly; accessing port also
        # validates malformed/out-of-range ports.
        host = parsed.hostname
        _ = parsed.port
        if not host:
            return False
        host = host.rstrip(".").lower()
        if not host or "%" in host or not host.isascii():
            return False

        # Reject ambiguous numeric host representations (e.g. 127.1, octal, hex).
        try:
            ip = ipaddress.ip_address(host)
            return is_ip_allowed(str(ip))
        except ValueError:
            if re.fullmatch(r"[0-9.]+", host) or host.startswith("0x"):
                return False

        if host in ("localhost", "metadata.google.internal", "instance-data"):
            return False
        if host.endswith((".local", ".internal", ".lan", ".localhost")):
            return False

        # Hostname syntax: valid DNS labels, no empty labels or underscores.
        labels = host.split(".")
        if len(labels) < 2 or any(
            not label or len(label) > 63
            or not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?", label)
            for label in labels
        ):
            return False
        return True
    except (ValueError, UnicodeError):
        return False

def sign_download_token(variant_url: str, filename: str, ttl_seconds: int = 86400) -> str:
    """
    Signs variant download info into a tamper-proof HMAC token.
    TTL defaults to 24 hours (86400 seconds) so users can download files without early expiration.
    """
    if not DOWNLOAD_SECRET:
        raise RuntimeError("Download signing secret is not configured.")
    exp = int(time.time()) + ttl_seconds
    payload = {
        "u": variant_url,
        "f": filename,
        "exp": exp
    }
    raw_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    b64_payload = base64.urlsafe_b64encode(raw_json).decode('ascii').rstrip('=')

    sig = hmac.new(
        DOWNLOAD_SECRET.encode('utf-8'),
        b64_payload.encode('ascii'),
        hashlib.sha256
    ).hexdigest()

    return f"{b64_payload}.{sig}"

def verify_download_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify HMAC signatures, expiry, and upstream URL safety for signed tokens."""
    if not token or not isinstance(token, str):
        return None
    token = token.strip()
    # Legacy direct URLs are retained for compatibility; validate their scheme and host.
    if token.startswith(("http://", "https://", "/api/")):
        if verify_safe_upstream_url(token):
            return {"variant_url": token, "filename": "download.mp4", "exp": int(time.time()) + 86400}
        return None
    if token.count(".") != 1:
        return None
    b64_payload, signature = token.split(".", 1)
    if not b64_payload or not signature:
        return None
    secrets_to_check = [s for s in POSSIBLE_DOWNLOAD_SECRETS if s]
    if not secrets_to_check:
        return None
    valid_signature = False
    for secret in secrets_to_check:
        expected = hmac.new(secret.encode("utf-8"), b64_payload.encode("ascii"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(expected, signature):
            valid_signature = True
            break
    if not valid_signature:
        return None
    padding = "=" * (-len(b64_payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(b64_payload + padding).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    variant_url = data.get("u")
    exp = data.get("exp")
    if not isinstance(variant_url, str) or not exp:
        return None
    try:
        exp = int(exp)
    except (TypeError, ValueError):
        return None
    if exp <= int(time.time()) or not verify_safe_upstream_url(variant_url):
        return None
    return {"variant_url": variant_url, "filename": data.get("f", "download.mp4"), "exp": exp}
