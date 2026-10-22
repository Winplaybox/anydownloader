import re
import urllib.parse
from typing import Dict, Any, Optional
import httpx
from .errors import ErrorCode, AppError

SHORT_DOMAINS = {
    "t.co",
    "youtu.be",
    "fb.watch",
    "vm.tiktok.com",
    "vt.tiktok.com",
    "instagr.am",
}

STRIP_PARAMS = {
    "s", "t", "igsh", "igshid", "fbclid", "si", "feature",
    "ref", "source", "ref_src", "context", "vertical"
}

def extract_first_url(text: str) -> Optional[str]:
    """Finds and extracts the first URL from a string with possible surrounding text."""
    if not text:
        return None
    pattern = r"(https?://[^\s<>\"\']+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>\"\']*)?)"
    url_m = re.search(pattern, text)
    if url_m:
        return url_m.group(0).rstrip(".,;!?:)")
    return None

def normalize_url(raw_input: str, resolve_redirects: bool = True) -> Dict[str, Any]:
    """
    Normalizes a social media URL across Twitter/X, YouTube, Facebook, Instagram, TikTok.
    """
    if not raw_input or not raw_input.strip():
        raise AppError(ErrorCode.URL_MISSING, "Paste a link to get started.")

    cleaned_text = raw_input.strip()

    all_urls = re.findall(r"https?://[^\s<>\"\']+", cleaned_text)
    multiple_found = len(all_urls) > 1

    extracted = extract_first_url(cleaned_text)
    if not extracted:
        raise AppError(ErrorCode.URL_INVALID, "That doesn't look like a valid link.")

    target = extracted

    if not target.startswith("http://") and not target.startswith("https://"):
        target = "https://" + target

    try:
        parsed = urllib.parse.urlparse(target)
    except Exception:
        raise AppError(ErrorCode.URL_INVALID, "That doesn't look like a valid link.")

    host = (parsed.netloc or "").lower().split(":")[0]
    path = parsed.path or "/"

    if not host or "." not in host:
        raise AppError(ErrorCode.URL_INVALID, "That doesn't look like a valid link.")

    if resolve_redirects and (host in SHORT_DOMAINS or host.startswith("t.co")):
        try:
            with httpx.Client(follow_redirects=True, timeout=8.0, max_redirects=5) as client:
                resp = client.head(target)
                if resp.status_code in (405, 403, 400):
                    resp = client.get(target)
                final_url = str(resp.url)
                parsed = urllib.parse.urlparse(final_url)
                host = (parsed.netloc or "").lower().split(":")[0]
                path = parsed.path or "/"
                target = final_url
        except Exception:
            pass

    platform = None

    if host in ("twitter.com", "mobile.twitter.com", "www.twitter.com", "fxtwitter.com", "vxtwitter.com", "fixupx.com", "x.com"):
        platform = "twitter"
        host = "x.com"
        status_m = re.search(r"/(?:i/web/status|i/status|[\w-]+/status)/(\d+)", path)
        if status_m:
            tweet_id = status_m.group(1)
            path = f"/i/status/{tweet_id}"

    elif host in ("youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"):
        platform = "youtube"
        host = "www.youtube.com"
        if "youtu.be" in host or parsed.netloc == "youtu.be":
            vid_id = path.lstrip("/").split("/")[0]
            path = "/watch"
            parsed = parsed._replace(query=f"v={vid_id}")

    elif host in ("facebook.com", "www.facebook.com", "m.facebook.com", "fb.watch", "web.facebook.com"):
        platform = "facebook"
        host = "www.facebook.com"

    elif host in ("instagram.com", "www.instagram.com", "instagr.am"):
        platform = "instagram"
        host = "www.instagram.com"

    elif host in ("tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"):
        platform = "tiktok"
        host = "www.tiktok.com"

    else:
        raise AppError(
            ErrorCode.PLATFORM_UNSUPPORTED,
            "This site isn't supported yet. Supported: X, YouTube, Facebook, Instagram, TikTok."
        )

    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=False)
    filtered_qs = {}
    for k, v in qs.items():
        k_lower = k.lower()
        if k_lower in STRIP_PARAMS or k_lower.startswith("utm_"):
            continue
        filtered_qs[k] = v

    clean_query = urllib.parse.urlencode(filtered_qs, doseq=True)

    clean_url = urllib.parse.urlunparse((
        "https",
        host,
        path.rstrip("/") if path != "/" else "/",
        "",
        clean_query,
        ""
    ))

    return {
        "ok": True,
        "url": clean_url,
        "platform": platform,
        "raw": raw_input,
        "multiple_found": multiple_found
    }
