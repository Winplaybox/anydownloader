import os
import time
import hmac
import hashlib
import json
import base64
import socket
import ipaddress
import urllib.parse
from typing import Dict, Any, Optional

DOWNLOAD_SECRET = os.environ.get("DOWNLOAD_SIGNING_SECRET", "wpb_ovd_secure_hmac_sign_key_9f83e2a74c10")

# Allowed CDN Domains for Upstream Streaming (SSRF Guard)
ALLOWED_CDN_DOMAINS = [
    "twimg.com",
    "video.twimg.com",
    "pbs.twimg.com",
    "googlevideo.com",
    "ytimg.com",
    "fbcdn.net",
    "cdninstagram.com",
    "tiktokcdn.com",
    "tiktokcdn-us.com",
    "tiktokv.com",
    "akamaized.net",
    "cloudfront.net",
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
    """
    Comprehensive SSRF Protection:
    1. Validates URL scheme is http or https.
    2. Validates hostname is in the CDN allowlist.
    3. Resolves DNS to check all IPs are public (not intranet/loopback).
    """
    try:
        parsed = urllib.parse.urlparse(target_url)
        if parsed.scheme not in ("http", "https"):
            return False

        host = (parsed.netloc or "").split(":")[0].lower()
        if not is_safe_cdn_host(host):
            return False

        # Resolve DNS
        addr_info = socket.getaddrinfo(host, None)
        for entry in addr_info:
            ip = entry[4][0]
            if not is_ip_allowed(ip):
                return False

        return True
    except Exception:
        return False

def sign_download_token(variant_url: str, filename: str, ttl_seconds: int = 300) -> str:
    """
    Signs variant download info into a tamper-proof HMAC token with expiration.
    TTL defaults to 5 minutes (300 seconds).
    """
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
    """
    Verifies token signature, expiration, and SSRF safety.
    Returns payload dictionary or None if invalid.
    """
    if not token or "." not in token:
        return None

    b64_payload, sig = token.split(".", 1)

    expected_sig = hmac.new(
        DOWNLOAD_SECRET.encode('utf-8'),
        b64_payload.encode('ascii'),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(sig, expected_sig):
        return None

    # Decode payload
    padding = '=' * (4 - (len(b64_payload) % 4)) if len(b64_payload) % 4 != 0 else ''
    try:
        raw_json = base64.urlsafe_b64decode(b64_payload + padding)
        data = json.loads(raw_json.decode('utf-8'))
    except Exception:
        return None

    # Check expiration
    if time.time() > data.get("exp", 0):
        return None

    variant_url = data.get("u")
    if not variant_url or not verify_safe_upstream_url(variant_url):
        return None

    return {
        "variant_url": variant_url,
        "filename": data.get("f", "download.mp4"),
        "exp": data.get("exp")
    }
