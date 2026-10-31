"""
OAuth "Connect account" flows for the Autopilot publisher.

The app credentials (client id/secret) belong to WinPlayBox and are set once on the server; end users
only click Connect and sign in on the platform's own page. One sign-in can add several accounts
(every Facebook Page the user grants, for example), and connecting again adds more.

Each flow returns accounts as {"platform", "external_id", "name", "avatar", "token"}; the token dict
is stored encrypted in Supabase Vault and later read by the render worker to publish.

  youtube    YT_CLIENT_ID / YT_CLIENT_SECRET               Google OAuth (web), offline refresh token
  facebook   META_APP_ID / META_APP_SECRET                  Facebook Login: one account per Page (page token)
  instagram  INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET        Instagram API with Instagram Login (60-day token)
  threads    THREADS_APP_ID / THREADS_APP_SECRET            Threads API (60-day token)
  tiktok     TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET       Login Kit + Content Posting API
  x          X_CLIENT_ID / X_CLIENT_SECRET                  OAuth 2.0 with PKCE, offline.access
"""

from __future__ import annotations

import base64
import hashlib
import os
import re
import secrets
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

GRAPH = os.environ.get("META_GRAPH_VERSION", "v23.0")


def env(*names: str) -> str:
    for n in names:
        v = os.environ.get(n, "").strip()
        if v:
            return v
    return ""


class OAuthError(Exception):
    pass


PLATFORMS: Dict[str, Dict[str, Any]] = {
    "youtube": {
        "label": "YouTube", "env": ["YT_CLIENT_ID", "YT_CLIENT_SECRET"], "pkce": False,
        "about": "Post Shorts and long videos to your channel.",
        "steps": ["Google Cloud console: create a project and enable \"YouTube Data API v3\".",
                  "OAuth consent screen: External, with the youtube.upload and youtube.readonly scopes.",
                  "Credentials > OAuth client ID > Web application; add the redirect URI below.",
                  "Paste the keys below, press Save, then Test."],
        "note": "Default quota allows about 6 uploads a day. Until Google verifies the app, uploads are private "
                "and only test users can connect.",
    },
    "tiktok": {
        "label": "TikTok", "env": ["TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET"], "pkce": False,
        "about": "Post videos straight to your TikTok account.",
        "steps": ["developers.tiktok.com: create an app with Login Kit and the Content Posting API (Direct Post).",
                  "Add the redirect URI below and the scopes user.info.basic, user.info.stats, video.publish, video.upload.",
                  "Paste the keys below, press Save, then Test."],
        "note": "Until TikTok audits the app, posts are visible only to the account owner.",
    },
    "instagram": {
        "label": "Instagram", "env": ["INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET"], "pkce": False,
        "about": "Post Reels. Needs a Professional (Business or Creator) account.",
        "steps": ["developers.facebook.com: create an app and add \"Instagram API with Instagram Login\".",
                  "Add the redirect URI below under Business login settings.",
                  "Paste the keys below (from the Instagram product page), press Save, then Test."],
        "note": "In development mode only accounts added as testers can connect; App Review opens it to everyone.",
    },
    "facebook": {
        "label": "Facebook", "env": ["META_APP_ID", "META_APP_SECRET"], "pkce": False,
        "about": "Post videos to a Facebook Page you manage.",
        "steps": ["developers.facebook.com: create a Business app and add Facebook Login for Business.",
                  "Add the redirect URI below as a valid OAuth redirect URI.",
                  "Paste the keys below, press Save, then Test."],
        "note": "Every Page you tick during sign-in is added. Pages you own work before App Review.",
    },
    "threads": {
        "label": "Threads", "env": ["THREADS_APP_ID", "THREADS_APP_SECRET"], "pkce": False,
        "about": "Post videos to your Threads profile.",
        "steps": ["developers.facebook.com: create an app with the \"Access the Threads API\" use case.",
                  "Add the redirect URI below, with threads_basic and threads_content_publish.",
                  "Paste the keys below, press Save, then Test."],
        "note": "In development mode only Threads testers can connect.",
    },
    "x": {
        "label": "X", "env": ["X_CLIENT_ID", "X_CLIENT_SECRET"], "pkce": True,
        "about": "Post videos to your X profile.",
        "steps": ["developer.x.com: create an app, enable OAuth 2.0 (Web App, confidential client), read and write.",
                  "Add the redirect URI below as the callback URL.",
                  "Paste the keys below, press Save, then Test."],
        "note": "Posting video needs an X API plan that includes media upload.",
    },
}


def configured(platform: str) -> bool:
    return all(env(e) for e in PLATFORMS[platform]["env"])


def pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    return verifier, challenge


def authorize_url(platform: str, redirect_uri: str, state: str, challenge: Optional[str] = None) -> str:
    if platform == "youtube":
        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
            "client_id": env("YT_CLIENT_ID"), "redirect_uri": redirect_uri, "response_type": "code",
            "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
            "access_type": "offline", "prompt": "consent select_account", "include_granted_scopes": "true",
            "state": state})
    if platform == "facebook":
        return f"https://www.facebook.com/{GRAPH}/dialog/oauth?" + urlencode({
            "client_id": env("META_APP_ID"), "redirect_uri": redirect_uri, "state": state, "response_type": "code",
            "scope": "pages_show_list,pages_read_engagement,pages_manage_posts,business_management"})
    if platform == "instagram":
        return "https://www.instagram.com/oauth/authorize?" + urlencode({
            "client_id": env("INSTAGRAM_APP_ID"), "redirect_uri": redirect_uri, "response_type": "code",
            "scope": "instagram_business_basic,instagram_business_content_publish", "state": state,
            "force_reauth": "true"})
    if platform == "threads":
        return "https://threads.net/oauth/authorize?" + urlencode({
            "client_id": env("THREADS_APP_ID"), "redirect_uri": redirect_uri, "response_type": "code",
            "scope": "threads_basic,threads_content_publish", "state": state})
    if platform == "tiktok":
        return "https://www.tiktok.com/v2/auth/authorize/?" + urlencode({
            "client_key": env("TIKTOK_CLIENT_KEY"), "redirect_uri": redirect_uri, "response_type": "code",
            "scope": "user.info.basic,user.info.stats,video.publish,video.upload", "state": state, "disable_auto_auth": "1"})
    if platform == "x":
        return "https://x.com/i/oauth2/authorize?" + urlencode({
            "response_type": "code", "client_id": env("X_CLIENT_ID"), "redirect_uri": redirect_uri,
            "scope": "tweet.read tweet.write users.read media.write offline.access", "state": state,
            "code_challenge": challenge or "", "code_challenge_method": "S256"})
    raise OAuthError(f"unknown platform {platform}")


async def _json(r: httpx.Response, what: str) -> Dict[str, Any]:
    try:
        data = r.json()
    except ValueError:
        raise OAuthError(f"{what}: HTTP {r.status_code}")
    if r.status_code >= 400 or (isinstance(data, dict) and data.get("error") and not data.get("access_token")):
        err = data.get("error") if isinstance(data, dict) else None
        if isinstance(err, dict):
            if any(e.get("reason") in ("quotaExceeded", "dailyLimitExceeded", "rateLimitExceeded") for e in err.get("errors") or []):
                raise OAuthError("YouTube's daily API limit for WinPlayBox is used up. It resets at 1:30 PM India time "
                                 "(midnight Pacific); connect again after that.")
            err = re.sub(r"<[^>]+>", "", str(err.get("message") or err.get("code")))
        desc = data.get("error_description") if isinstance(data, dict) else None
        raise OAuthError(f"{what}: {desc or err or r.status_code}")
    return data


async def complete(platform: str, code: str, redirect_uri: str, verifier: Optional[str] = None) -> List[Dict[str, Any]]:
    """Exchange the code and describe every account the sign-in granted."""
    async with httpx.AsyncClient(timeout=30) as c:
        if platform == "youtube":
            tok = await _json(await c.post("https://oauth2.googleapis.com/token", data={
                "code": code, "client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"),
                "redirect_uri": redirect_uri, "grant_type": "authorization_code"}), "token exchange")
            me = await _json(await c.get("https://www.googleapis.com/youtube/v3/channels",
                                         params={"part": "snippet", "mine": "true"},
                                         headers={"Authorization": f"Bearer {tok['access_token']}"}), "channel lookup")
            items = me.get("items") or []
            if not items:
                raise OAuthError("This Google account has no YouTube channel.")
            ch = items[0]
            # The worker refreshes access tokens itself, so it keeps the client pair with the refresh token.
            token = {"client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"),
                     "token_uri": "https://oauth2.googleapis.com/token"}
            if tok.get("refresh_token"):
                token["refresh_token"] = tok["refresh_token"]
            sn = ch["snippet"]
            return [{"platform": "youtube", "external_id": ch["id"], "name": sn.get("title", ch["id"]),
                     "avatar": sn.get("thumbnails", {}).get("default", {}).get("url"), "token": token}]

        if platform == "facebook":
            base = f"https://graph.facebook.com/{GRAPH}"
            short = await _json(await c.get(f"{base}/oauth/access_token", params={
                "client_id": env("META_APP_ID"), "client_secret": env("META_APP_SECRET"),
                "redirect_uri": redirect_uri, "code": code}), "token exchange")
            # Long-lived user token -> Page tokens derived from it don't expire.
            long = await _json(await c.get(f"{base}/oauth/access_token", params={
                "grant_type": "fb_exchange_token", "client_id": env("META_APP_ID"),
                "client_secret": env("META_APP_SECRET"), "fb_exchange_token": short["access_token"]}), "long-lived token")
            pages = await _json(await c.get(f"{base}/me/accounts", params={
                "fields": "id,name,access_token,picture{url}", "limit": 100,
                "access_token": long["access_token"]}), "page list")
            out = [{"platform": "facebook", "external_id": p["id"], "name": p["name"],
                    "avatar": (p.get("picture") or {}).get("data", {}).get("url"),
                    "token": {"page_access_token": p["access_token"]}} for p in pages.get("data", [])]
            if not out:
                raise OAuthError("No Facebook Pages were shared. Connect again and tick at least one Page.")
            return out

        if platform == "instagram":
            short = await _json(await c.post("https://api.instagram.com/oauth/access_token", data={
                "client_id": env("INSTAGRAM_APP_ID"), "client_secret": env("INSTAGRAM_APP_SECRET"),
                "grant_type": "authorization_code", "redirect_uri": redirect_uri, "code": code}), "token exchange")
            long = await _json(await c.get("https://graph.instagram.com/access_token", params={
                "grant_type": "ig_exchange_token", "client_secret": env("INSTAGRAM_APP_SECRET"),
                "access_token": short["access_token"]}), "long-lived token")
            me = await _json(await c.get(f"https://graph.instagram.com/{GRAPH}/me", params={
                "fields": "user_id,username,profile_picture_url", "access_token": long["access_token"]}), "profile")
            return [{"platform": "instagram", "external_id": str(me.get("user_id") or short.get("user_id")),
                     "name": "@" + me.get("username", "instagram"), "avatar": me.get("profile_picture_url"),
                     "token": {"access_token": long["access_token"],
                               "expires_at": int(time.time()) + int(long.get("expires_in", 5184000))}}]

        if platform == "threads":
            short = await _json(await c.post("https://graph.threads.net/oauth/access_token", data={
                "client_id": env("THREADS_APP_ID"), "client_secret": env("THREADS_APP_SECRET"),
                "grant_type": "authorization_code", "redirect_uri": redirect_uri, "code": code}), "token exchange")
            long = await _json(await c.get("https://graph.threads.net/access_token", params={
                "grant_type": "th_exchange_token", "client_secret": env("THREADS_APP_SECRET"),
                "access_token": short["access_token"]}), "long-lived token")
            me = await _json(await c.get("https://graph.threads.net/v1.0/me", params={
                "fields": "id,username,threads_profile_picture_url", "access_token": long["access_token"]}), "profile")
            return [{"platform": "threads", "external_id": str(me["id"]), "name": "@" + me.get("username", "threads"),
                     "avatar": me.get("threads_profile_picture_url"),
                     "token": {"access_token": long["access_token"],
                               "expires_at": int(time.time()) + int(long.get("expires_in", 5184000))}}]

        if platform == "tiktok":
            tok = await _json(await c.post("https://open.tiktokapis.com/v2/oauth/token/", data={
                "client_key": env("TIKTOK_CLIENT_KEY"), "client_secret": env("TIKTOK_CLIENT_SECRET"),
                "code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri},
                headers={"Content-Type": "application/x-www-form-urlencoded"}), "token exchange")
            me = await _json(await c.get("https://open.tiktokapis.com/v2/user/info/",
                                         params={"fields": "open_id,display_name,avatar_url"},
                                         headers={"Authorization": f"Bearer {tok['access_token']}"}), "profile")
            u = (me.get("data") or {}).get("user") or {}
            return [{"platform": "tiktok", "external_id": u.get("open_id") or tok.get("open_id"),
                     "name": u.get("display_name") or "TikTok", "avatar": u.get("avatar_url"),
                     "token": {"access_token": tok["access_token"], "refresh_token": tok.get("refresh_token"),
                               "expires_at": int(time.time()) + int(tok.get("expires_in", 86400)),
                               # the worker refreshes the 24 h access token itself
                               "client_key": env("TIKTOK_CLIENT_KEY"), "client_secret": env("TIKTOK_CLIENT_SECRET")}}]

        if platform == "x":
            basic = base64.b64encode(f"{env('X_CLIENT_ID')}:{env('X_CLIENT_SECRET')}".encode()).decode()
            tok = await _json(await c.post("https://api.x.com/2/oauth2/token", data={
                "code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri,
                "code_verifier": verifier or "", "client_id": env("X_CLIENT_ID")},
                headers={"Authorization": f"Basic {basic}"}), "token exchange")
            me = await _json(await c.get("https://api.x.com/2/users/me", params={"user.fields": "profile_image_url"},
                                         headers={"Authorization": f"Bearer {tok['access_token']}"}), "profile")
            u = me.get("data") or {}
            return [{"platform": "x", "external_id": u.get("id"), "name": "@" + u.get("username", "x"),
                     "avatar": u.get("profile_image_url"),
                     "token": {"access_token": tok["access_token"], "refresh_token": tok.get("refresh_token"),
                               "expires_at": int(time.time()) + int(tok.get("expires_in", 7200)),
                               "client_id": env("X_CLIENT_ID"), "client_secret": env("X_CLIENT_SECRET")}}]

    raise OAuthError(f"unknown platform {platform}")


# --------------------------------------------------------------------------- live stats for the analytics page

class TokenRevoked(OAuthError):
    """The user removed our access or it expired for good: the account must be connected again."""


async def _refresh(c: httpx.AsyncClient, platform: str, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """New token fields when the access token needed refreshing ("_access" = short-lived, not stored)."""
    exp = token.get("expires_at", 0)
    if platform == "youtube":
        if not token.get("refresh_token"):
            raise TokenRevoked("connect the channel again")
        r = await c.post(token.get("token_uri", "https://oauth2.googleapis.com/token"), data={
            "client_id": token["client_id"], "client_secret": token["client_secret"],
            "refresh_token": token["refresh_token"], "grant_type": "refresh_token"})
        if r.status_code != 200:
            raise TokenRevoked("YouTube access was revoked or expired")
        return {"_access": r.json()["access_token"]}
    if platform in ("instagram", "threads") and exp and exp - time.time() < 7 * 86400:
        url = ("https://graph.instagram.com/refresh_access_token" if platform == "instagram"
               else "https://graph.threads.net/refresh_access_token")
        r = await c.get(url, params={"grant_type": "ig_refresh_token" if platform == "instagram" else "th_refresh_token",
                                     "access_token": token["access_token"]})
        if r.status_code != 200:
            raise TokenRevoked(f"{platform} access expired")
        d = r.json()
        return {"access_token": d["access_token"], "expires_at": int(time.time()) + int(d.get("expires_in", 5184000))}
    if platform == "tiktok" and exp - time.time() < 300:
        r = await c.post("https://open.tiktokapis.com/v2/oauth/token/", data={
            "client_key": token.get("client_key") or env("TIKTOK_CLIENT_KEY"),
            "client_secret": token.get("client_secret") or env("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token", "refresh_token": token.get("refresh_token", "")})
        d = r.json()
        if r.status_code != 200 or "access_token" not in d:
            raise TokenRevoked("TikTok access expired")
        return {"access_token": d["access_token"], "refresh_token": d.get("refresh_token", token.get("refresh_token")),
                "expires_at": int(time.time()) + int(d.get("expires_in", 86400))}
    if platform == "x" and exp - time.time() < 300:
        cid, sec = token.get("client_id") or env("X_CLIENT_ID"), token.get("client_secret") or env("X_CLIENT_SECRET")
        basic = base64.b64encode(f"{cid}:{sec}".encode()).decode()
        r = await c.post("https://api.x.com/2/oauth2/token", headers={"Authorization": f"Basic {basic}"}, data={
            "grant_type": "refresh_token", "refresh_token": token.get("refresh_token", ""), "client_id": cid})
        d = r.json()
        if r.status_code != 200 or "access_token" not in d:
            raise TokenRevoked("X access expired")
        return {"access_token": d["access_token"], "refresh_token": d.get("refresh_token", token.get("refresh_token")),
                "expires_at": int(time.time()) + int(d.get("expires_in", 7200))}
    return None


async def revoke(platform: str, token: Dict[str, Any]) -> bool:
    """Best effort: tell the platform to drop our access when a user disconnects. Instagram, Threads and Facebook
    pages have no token-revocation endpoint for these tokens (the user removes the app in their settings)."""
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            if platform == "youtube" and (token.get("refresh_token") or token.get("token")):
                r = await c.post("https://oauth2.googleapis.com/revoke", data={"token": token.get("refresh_token") or token["token"]})
            elif platform == "tiktok" and token.get("access_token"):
                r = await c.post("https://open.tiktokapis.com/v2/oauth/revoke/", data={
                    "client_key": token.get("client_key") or env("TIKTOK_CLIENT_KEY"),
                    "client_secret": token.get("client_secret") or env("TIKTOK_CLIENT_SECRET"), "token": token["access_token"]})
            elif platform == "x" and (token.get("refresh_token") or token.get("access_token")):
                cid, sec = token.get("client_id") or env("X_CLIENT_ID"), token.get("client_secret") or env("X_CLIENT_SECRET")
                basic = base64.b64encode(f"{cid}:{sec}".encode()).decode()
                hint = "refresh_token" if token.get("refresh_token") else "access_token"
                r = await c.post("https://api.x.com/2/oauth2/revoke", headers={"Authorization": f"Basic {basic}"},
                                 data={"token": token.get(hint), "token_type_hint": hint, "client_id": cid})
            else:
                return False
            return r.status_code < 400
    except httpx.HTTPError:
        return False


async def check_app(platform: str, redirect_uri: str) -> tuple:
    """Are this platform's app keys accepted by the platform? -> (True | False | None, message). None = cannot tell
    without a real sign-in. Bad-code probes rely on the error the platform gives a wrong client vs. a wrong code."""
    if not configured(platform):
        return False, "Add the keys first."
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            if platform == "youtube":
                r = await c.post("https://oauth2.googleapis.com/token", data={
                    "client_id": env("YT_CLIENT_ID"), "client_secret": env("YT_CLIENT_SECRET"), "code": "probe",
                    "grant_type": "authorization_code", "redirect_uri": redirect_uri})
                err = (r.json() or {}).get("error", "")
                if err in ("invalid_client", "unauthorized_client"):
                    return False, "Google rejected the client ID or secret."
                return True, "Google accepted the client ID and secret. Add yourself as a test user, then Connect."
            if platform == "facebook":
                r = await c.get(f"https://graph.facebook.com/{GRAPH}/oauth/access_token", params={
                    "client_id": env("META_APP_ID"), "client_secret": env("META_APP_SECRET"), "grant_type": "client_credentials"})
                return (True, "Meta accepted the app ID and secret.") if r.status_code == 200 else (False, "Meta rejected the app ID or secret.")
            if platform == "tiktok":
                r = await c.post("https://open.tiktokapis.com/v2/oauth/token/", data={
                    "client_key": env("TIKTOK_CLIENT_KEY"), "client_secret": env("TIKTOK_CLIENT_SECRET"), "grant_type": "client_credentials"})
                ok = r.status_code == 200 and "access_token" in (r.json() or {})
                return (True, "TikTok accepted the client key and secret.") if ok else (False, "TikTok rejected the client key or secret.")
            if platform == "x":
                basic = base64.b64encode(f"{env('X_CLIENT_ID')}:{env('X_CLIENT_SECRET')}".encode()).decode()
                r = await c.post("https://api.x.com/2/oauth2/token", headers={"Authorization": f"Basic {basic}"}, data={
                    "grant_type": "authorization_code", "code": "probe", "redirect_uri": redirect_uri,
                    "code_verifier": "probe" * 9, "client_id": env("X_CLIENT_ID")})
                if r.status_code == 401 or "unauthorized_client" in r.text:
                    return False, "X rejected the client ID or secret (use OAuth 2.0 keys, confidential client)."
                return True, "X accepted the client ID and secret."
    except httpx.HTTPError as e:
        return None, f"Could not reach the platform: {type(e).__name__}"
    return None, "Keys are saved. This platform can only be checked by connecting a test account."


def _auth_failed(r: httpx.Response) -> bool:
    return r.status_code in (401, 403) or "OAuthException" in r.text[:500]


async def stats(platform: str, external_id: str, token: Dict[str, Any]) -> tuple:
    """({"followers", "views", "posts", "likes", "recent": [...]}, token fields to save or None). Raises TokenRevoked."""
    async with httpx.AsyncClient(timeout=20) as c:
        fresh = await _refresh(c, platform, token)
        tok = {**token, **(fresh or {})}
        save = {k: v for k, v in (fresh or {}).items() if not k.startswith("_")} or None
        if platform == "youtube":
            h = {"Authorization": f"Bearer {tok['_access']}"}
            r = await c.get("https://www.googleapis.com/youtube/v3/channels",
                            params={"part": "statistics,contentDetails", "id": external_id}, headers=h)
            if _auth_failed(r):
                raise TokenRevoked("YouTube access was revoked")
            ch = (r.json().get("items") or [{}])[0]
            st = ch.get("statistics", {})
            uploads = ch.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            recent = []
            if uploads:
                pl = (await c.get("https://www.googleapis.com/youtube/v3/playlistItems", headers=h, params={
                    "part": "contentDetails", "playlistId": uploads, "maxResults": 8})).json()
                ids = [i["contentDetails"]["videoId"] for i in pl.get("items", [])]
                if ids:
                    vids = (await c.get("https://www.googleapis.com/youtube/v3/videos", headers=h, params={
                        "part": "snippet,statistics", "id": ",".join(ids)})).json()
                    recent = [{"title": v["snippet"]["title"], "url": f"https://youtu.be/{v['id']}",
                               "published": v["snippet"].get("publishedAt"),
                               "views": int(v["statistics"].get("viewCount", 0)), "likes": int(v["statistics"].get("likeCount", 0)),
                               "comments": int(v["statistics"].get("commentCount", 0))} for v in vids.get("items", [])]
            return {"followers": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)),
                    "posts": int(st.get("videoCount", 0)), "recent": recent}, save
        if platform == "instagram":
            r = await c.get(f"https://graph.instagram.com/{GRAPH}/me", params={
                "fields": "followers_count,media_count", "access_token": tok["access_token"]})
            if _auth_failed(r):
                raise TokenRevoked("Instagram access expired")
            d = r.json()
            media = (await c.get(f"https://graph.instagram.com/{GRAPH}/me/media", params={
                "fields": "caption,permalink,timestamp,like_count,comments_count", "limit": 8,
                "access_token": tok["access_token"]})).json().get("data", [])
            return {"followers": d.get("followers_count"), "posts": d.get("media_count"),
                    "recent": [{"title": (m.get("caption") or "")[:80], "url": m.get("permalink"), "published": m.get("timestamp"),
                                "likes": m.get("like_count"), "comments": m.get("comments_count")} for m in media]}, save
        if platform == "facebook":
            r = await c.get(f"https://graph.facebook.com/{GRAPH}/{external_id}", params={
                "fields": "followers_count,fan_count", "access_token": tok["page_access_token"]})
            if _auth_failed(r):
                raise TokenRevoked("Facebook Page access expired")
            d = r.json()
            return {"followers": d.get("followers_count") or d.get("fan_count"), "likes": d.get("fan_count")}, save
        if platform == "threads":
            r = await c.get(f"https://graph.threads.net/v1.0/{external_id}/threads_insights", params={
                "metric": "views,likes,followers_count", "access_token": tok["access_token"]})
            if _auth_failed(r):
                raise TokenRevoked("Threads access expired")
            vals = {}
            for m in r.json().get("data", []):
                v = m.get("total_value", {}).get("value")
                if v is None and m.get("values"):
                    v = sum(x.get("value", 0) for x in m["values"])
                vals[m.get("name")] = v
            return {"followers": vals.get("followers_count"), "views": vals.get("views"), "likes": vals.get("likes")}, save
        if platform == "tiktok":
            r = await c.get("https://open.tiktokapis.com/v2/user/info/", headers={"Authorization": f"Bearer {tok['access_token']}"},
                            params={"fields": "follower_count,likes_count,video_count"})
            if _auth_failed(r):
                raise TokenRevoked("TikTok access expired")
            u = (r.json().get("data") or {}).get("user") or {}
            return {"followers": u.get("follower_count"), "likes": u.get("likes_count"), "posts": u.get("video_count")}, save
        if platform == "x":
            r = await c.get("https://api.x.com/2/users/me", headers={"Authorization": f"Bearer {tok['access_token']}"},
                            params={"user.fields": "public_metrics"})
            if _auth_failed(r):
                raise TokenRevoked("X access expired")
            m = (r.json().get("data") or {}).get("public_metrics") or {}
            return {"followers": m.get("followers_count"), "posts": m.get("tweet_count"), "likes": m.get("like_count")}, save
    return {}, None
