"""
OVD usage analytics: who used which tool, when, what they downloaded, and what failed.

- record()   fire-and-forget; never raises, never slows a request
- storage    Supabase table `ovd_events` (supabase/ovd_events.sql) when SUPABASE_URL +
             SUPABASE_SERVICE_ROLE_KEY are set; otherwise an in-memory ring buffer (lost on restart)
- privacy    IP is never stored: only a salted hash (visitor) plus country/region from a free geo lookup
- summary()  everything the admin dashboard shows
"""
from __future__ import annotations

import asyncio
import collections
import hashlib
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

TABLE = "ovd_events"
IST = timezone(timedelta(hours=5, minutes=30))
_COLS = ("ts", "kind", "platform", "status", "code", "http", "ms", "quality", "title", "url", "host",
         "visitor", "device", "browser", "ref", "country", "region")

_MEM: collections.deque = collections.deque(maxlen=5000)   # newest last; also powers the no-database fallback
_PENDING: List[Dict[str, Any]] = []
_GEO: Dict[str, Dict[str, Optional[str]]] = {}
_task: Optional[asyncio.Task] = None
_stats = {"uploaded": 0, "upload_errors": 0, "last_error": None, "last_purge": 0.0}


# --------------------------------------------------------------------------- config
def _sb_url() -> str:
    return os.environ.get("SUPABASE_URL", "").rstrip("/")


def _sb_key() -> str:
    return os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def configured() -> bool:
    return bool(_sb_url() and _sb_key())


def admin_key() -> str:
    return os.environ.get("WPB_ADMIN_KEY") or ""


def _salt() -> str:
    return os.environ.get("ANALYTICS_SALT") or admin_key() or "ovd"


def _headers() -> Dict[str, str]:
    k = _sb_key()
    return {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}


# --------------------------------------------------------------------------- request parsing
def client_ip(request) -> str:
    xff = request.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else ""


def parse_ua(ua: str) -> Dict[str, str]:
    u = (ua or "").lower()
    if not u or re.search(r"bot|spider|crawl|curl|wget|python|httpx|headless|monitor|uptime", u):
        device = "bot"
    elif "ipad" in u or "tablet" in u:
        device = "tablet"
    elif "mobi" in u or "android" in u or "iphone" in u:
        device = "mobile"
    else:
        device = "desktop"
    if "edg/" in u: browser = "Edge"
    elif "opr/" in u or "opera" in u: browser = "Opera"
    elif "samsungbrowser" in u: browser = "Samsung"
    elif "firefox" in u: browser = "Firefox"
    elif "chrome" in u or "crios" in u: browser = "Chrome"
    elif "safari" in u: browser = "Safari"
    else: browser = "Other"
    return {"device": device, "browser": browser}


_HOSTS = (("youtube", ("youtube.com", "youtu.be", "googlevideo.com", "ytimg.com")),
          ("instagram", ("instagram.com", "cdninstagram.com")),
          ("tiktok", ("tiktok.com", "tiktokcdn", "ibytedtos", "byteoversea")),
          ("facebook", ("facebook.com", "fb.watch", "fbcdn.net", "fb.com")),
          ("twitter", ("twitter.com", "x.com", "twimg.com")),
          ("pinterest", ("pinterest.", "pinimg.com", "pin.it")),
          ("reddit", ("reddit.com", "redd.it", "redditmedia.com", "redditstatic.com")),
          ("threads", ("threads.net", "threads.com")))


def platform_from_url(url: str) -> str:
    host = (urlparse(url or "").hostname or "").lower()
    for name, needles in _HOSTS:
        if any(n in host for n in needles):
            return name
    return "other"


def _clip(v: Any, n: int) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s[:n] if s else None


def _response_json(resp) -> Dict[str, Any]:
    try:
        body = getattr(resp, "body", None)
        if body:
            j = json.loads(body)
            return j if isinstance(j, dict) else {}
    except Exception:
        pass
    return {}


async def track_request(kind: str, request, resp, ms: float, exc: Optional[BaseException] = None) -> None:
    """Build one event from a finished request. Never raises."""
    try:
        status_code = getattr(resp, "status_code", 500 if exc else 200)
        if status_code in (301, 302, 307, 308):      # redirect to another tracked endpoint: do not double count
            return
        q = request.query_params
        body_in: Dict[str, Any] = {}
        if request.method == "POST":
            try:
                body_in = await request.json()
            except Exception:
                body_in = {}
        out = _response_json(resp)
        data = out.get("data") if isinstance(out.get("data"), dict) else {}
        err = out.get("error") if isinstance(out.get("error"), dict) else {}

        url = q.get("url") or body_in.get("url") or body_in.get("link") or body_in.get("input") or ""
        title = data.get("title") or q.get("title") or q.get("filename")
        quality = None
        if kind == "download":
            path = request.url.path
            if path.endswith("download_video"):
                quality = f"{q.get('height', '720')}p"
            elif path.endswith("download_audio"):
                quality = f"mp3 {q.get('quality', '192')}k"
            else:
                quality = "file"
        ok = status_code < 400 and out.get("ok") is not False
        status = "ok" if ok else "fail"
        code = None
        if not ok:
            code = err.get("code") or ("EXCEPTION" if exc else f"HTTP_{status_code}")
        elif data.get("status") == "degraded":
            status = "degraded"
            code = (data.get("notice") or {}).get("code")
        platform = data.get("platform") or platform_from_url(url)
        ua = parse_ua(request.headers.get("user-agent", ""))
        ref_host = urlparse(request.headers.get("origin") or request.headers.get("referer") or "").hostname
        ip = client_ip(request)
        record({
            "kind": kind, "platform": platform, "status": status, "code": code, "http": status_code,
            "ms": int(ms), "quality": quality, "title": _clip(title, 120), "url": _clip(url, 300),
            "host": urlparse(url).hostname if url else None,
            "visitor": hashlib.sha256(f"{_salt()}|{ip}".encode()).hexdigest()[:16] if ip else None,
            "device": ua["device"], "browser": ua["browser"], "ref": _clip(ref_host, 80),
            "_ip": ip,
        })
    except Exception as e:  # analytics must never break a download
        print(f"[analytics] track failed: {e}", flush=True)


# --------------------------------------------------------------------------- recording + upload
def record(ev: Dict[str, Any]) -> None:
    ev.setdefault("ts", datetime.now(timezone.utc).isoformat())
    _MEM.append(ev)
    if configured():
        _PENDING.append(ev)
        if len(_PENDING) > 2000:
            del _PENDING[:500]
        _ensure_task()


def _ensure_task() -> None:
    global _task
    try:
        if _task is None or _task.done():
            _task = asyncio.get_running_loop().create_task(_flusher())
    except RuntimeError:
        pass


async def _geo(ip: str, client: httpx.AsyncClient) -> Dict[str, Optional[str]]:
    if not ip or ip.startswith(("10.", "127.", "192.168.", "172.16.")) or ip == "::1":
        return {"country": None, "region": None}
    if ip in _GEO:
        return _GEO[ip]
    try:
        r = await client.get(f"https://ipwho.is/{ip}?fields=success,country_code,region", timeout=3)
        j = r.json() if r.status_code == 200 else {}
        g = {"country": j.get("country_code") if j.get("success") else None,
             "region": j.get("region") if j.get("success") else None}
    except Exception:
        g = {"country": None, "region": None}
    if len(_GEO) > 5000:
        _GEO.clear()
    _GEO[ip] = g
    return g


async def flush() -> int:
    """Upload pending events. Returns how many were uploaded."""
    if not configured() or not _PENDING:
        return 0
    batch = _PENDING[:200]
    del _PENDING[:len(batch)]
    rows = []
    try:
        async with httpx.AsyncClient() as geo_client:
            looked_up = 0
            for ev in batch:
                ip = ev.get("_ip")
                if ip and ip not in _GEO and looked_up >= 15:
                    g = {"country": None, "region": None}
                else:
                    if ip and ip not in _GEO:
                        looked_up += 1
                    g = await _geo(ip, geo_client) if ip else {"country": None, "region": None}
                ev["country"], ev["region"] = g["country"], g["region"]   # also fixes the in-memory copy
                rows.append({k: ev.get(k) for k in _COLS})
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{_sb_url()}/rest/v1/{TABLE}", headers={**_headers(), "Prefer": "return=minimal"},
                             content=json.dumps(rows))
        if r.status_code >= 300:
            raise RuntimeError(f"{r.status_code} {r.text[:160]}")
        _stats["uploaded"] += len(rows)
        return len(rows)
    except Exception as e:
        _stats["upload_errors"] += 1
        _stats["last_error"] = str(e)[:200]
        print(f"[analytics] upload failed: {e}", flush=True)
        _PENDING[:0] = batch[:1000]      # keep for retry (bounded)
        return 0


async def _purge_old(days: int = 90) -> None:
    if time.time() - _stats["last_purge"] < 86400:
        return
    _stats["last_purge"] = time.time()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            await c.delete(f"{_sb_url()}/rest/v1/{TABLE}?ts=lt.{cutoff}", headers=_headers())
    except Exception as e:
        print(f"[analytics] purge failed: {e}", flush=True)


async def _flusher() -> None:
    while True:
        await asyncio.sleep(5)
        try:
            while _PENDING:
                if not await flush():
                    break
            await _purge_old()
        except Exception as e:
            print(f"[analytics] flusher error: {e}", flush=True)
        if not _PENDING:
            await asyncio.sleep(10)


# --------------------------------------------------------------------------- reading
async def fetch_rows(days: int) -> List[Dict[str, Any]]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    if not configured():
        return [e for e in _MEM if datetime.fromisoformat(e["ts"]) >= since]
    await flush()
    rows: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=20) as c:
        for page in range(25):                       # up to 25k rows
            lo = page * 1000
            r = await c.get(f"{_sb_url()}/rest/v1/{TABLE}?select={','.join(_COLS)}&ts=gte.{since.isoformat()}&order=ts.desc",
                            headers={**_headers(), "Range": f"{lo}-{lo + 999}"})
            if r.status_code >= 300:
                raise RuntimeError(f"database read failed: {r.status_code} {r.text[:120]}")
            chunk = r.json()
            rows.extend(chunk)
            if len(chunk) < 1000:
                break
    return rows


def _ts(row: Dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(row["ts"]).replace("Z", "+00:00"))


def _top(counter: collections.Counter, n: int = 8) -> List[Dict[str, Any]]:
    return [{"name": k, "count": v} for k, v in counter.most_common(n) if k]


def summarize(rows: List[Dict[str, Any]], days: int, yt_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rows = sorted(rows, key=_ts, reverse=True)
    resolves = [r for r in rows if r["kind"] == "resolve"]
    downloads = [r for r in rows if r["kind"] == "download"]
    dl_ok = [r for r in downloads if r["status"] == "ok"]
    now = datetime.now(IST)

    daily: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        daily[d] = {"resolves": 0, "downloads_ok": 0, "downloads_fail": 0}
    hourly = [0] * 24
    for r in rows:
        t = _ts(r).astimezone(IST)
        d = daily.get(t.strftime("%Y-%m-%d"))
        if d is None:
            continue
        hourly[t.hour] += 1
        if r["kind"] == "resolve":
            d["resolves"] += 1
        elif r["status"] == "ok":
            d["downloads_ok"] += 1
        else:
            d["downloads_fail"] += 1

    plat: Dict[str, Dict[str, int]] = {}
    for r in rows:
        p = plat.setdefault(r.get("platform") or "other", {"resolves": 0, "resolve_fail": 0, "downloads": 0, "download_fail": 0})
        if r["kind"] == "resolve":
            p["resolves"] += 1
            p["resolve_fail"] += r["status"] == "fail"
        else:
            p["downloads"] += 1
            p["download_fail"] += r["status"] == "fail"

    errs: Dict[tuple, Dict[str, Any]] = {}
    for r in rows:
        if r["status"] == "ok":
            continue
        k = (r.get("code") or "UNKNOWN", r.get("platform") or "other", r["kind"])
        e = errs.setdefault(k, {"code": k[0], "platform": k[1], "kind": k[2], "count": 0, "last": r["ts"]})
        e["count"] += 1

    content: Dict[str, Dict[str, Any]] = {}
    for r in dl_ok or resolves:
        key = r.get("url") or r.get("title") or ""
        if not key:
            continue
        c = content.setdefault(key, {"title": r.get("title"), "url": r.get("url"), "platform": r.get("platform"), "count": 0})
        c["count"] += 1

    day_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    yt = [r for r in downloads if r.get("platform") == "youtube" and _ts(r) >= day_ago]
    yt_ok = [r for r in yt if r["status"] == "ok"]
    resolve_ok = [r for r in resolves if r["status"] != "fail"]

    return {
        "range_days": days,
        "source": "supabase" if configured() else "memory",
        "storage_warning": None if configured() else "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set: data is kept in memory only and resets when the server restarts.",
        "upload": {"pending": len(_PENDING), **{k: v for k, v in _stats.items() if k != "last_purge"}},
        "totals": {
            "events": len(rows),
            "visitors": len({r["visitor"] for r in rows if r.get("visitor")}),
            "resolves": len(resolves),
            "resolve_ok_pct": round(100 * len(resolve_ok) / len(resolves), 1) if resolves else None,
            "downloads": len(downloads),
            "downloads_ok": len(dl_ok),
            "download_ok_pct": round(100 * len(dl_ok) / len(downloads), 1) if downloads else None,
        },
        "daily": [{"day": d, **v} for d, v in daily.items()],
        "hourly_ist": hourly,
        "platforms": sorted(({"platform": k, **v} for k, v in plat.items()), key=lambda x: -(x["resolves"] + x["downloads"])),
        "errors": sorted(errs.values(), key=lambda x: -x["count"])[:15],
        "devices": _top(collections.Counter(r.get("device") for r in rows)),
        "browsers": _top(collections.Counter(r.get("browser") for r in rows)),
        "countries": _top(collections.Counter(r.get("country") for r in rows)),
        "referrers": _top(collections.Counter(r.get("ref") for r in rows)),
        "top_content": sorted(content.values(), key=lambda x: -x["count"])[:10],
        "youtube": {
            "downloads_24h": len(yt), "ok_24h": len(yt_ok),
            "ok_pct_24h": round(100 * len(yt_ok) / len(yt), 1) if yt else None,
            "breaker": yt_state or {},
        },
        "recent": [{**{k: r.get(k) for k in ("ts", "kind", "platform", "status", "code", "quality", "title", "device", "country", "ms")},
                    "visitor": (r.get("visitor") or "")[:6]} for r in rows[:60]],
    }
