"""OVD resolve/extract regressions: shared yt-dlp opts, block detection, degraded YouTube, Instagram embed."""
import asyncio
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
os.environ.setdefault("WPB_VAULT_SECRET", "test_secret_key_" + "x" * 40)

import pytest  # noqa: E402

from backend.engines.base import ExtractContext  # noqa: E402
from backend.engines import instagram_embed_engine as ig  # noqa: E402
from backend.engines import ytdlp_engine as yte  # noqa: E402
from backend.utils import ytdlp_opts as yo  # noqa: E402
from backend.utils.errors import AppError, ErrorCode  # noqa: E402

EMBED_HTML = r'''<html><body>
<div class="Header"><span class="UsernameText">dhrusavlogs</span></div>
<script>window.__additionalDataLoaded('extra',{"shortcode_media":{"video_url":"https:\/\/scontent.cdninstagram.com\/v\/t50\/abc.mp4?x=1&y=2","display_url":"https:\/\/scontent.cdninstagram.com\/v\/t51\/thumb.jpg"}});</script>
<div class="Caption"><a class="CaptionUsername">dhrusavlogs</a> Mira Road <b>street food</b> tour</div>
</body></html>'''


def test_robust_opts_extract_mode_has_runtime_clients_and_fast_fail():
    o = yo.robust_opts("extract")
    assert o["skip_download"] is True and o["extractor_retries"] == 1 and o["socket_timeout"] <= 12
    assert "tv" in o["extractor_args"]["youtube"]["player_client"]
    d = yo.robust_opts("download")
    assert d["retries"] == 3 and "skip_download" not in d


def test_cookies_env_is_normalized(monkeypatch, tmp_path):
    monkeypatch.setattr(yo, "_cookie_loaded", False)
    monkeypatch.setattr(yo, "_cookie_cache", None)
    monkeypatch.setenv("YTDLP_COOKIES", ".youtube.com TRUE / TRUE 0 SID abc")
    path = yo.cookiefile()
    body = open(path).read()
    assert body.startswith("# Netscape HTTP Cookie File") and "\tSID\tabc" in body
    monkeypatch.setattr(yo, "_cookie_loaded", False)
    monkeypatch.setattr(yo, "_cookie_cache", None)


def test_instagram_session_env_is_normalized(monkeypatch, tmp_path):
    monkeypatch.setattr(yo, "_cookie_loaded", False)
    monkeypatch.setattr(yo, "_cookie_cache", None)
    monkeypatch.setenv("YTDLP_COOKIES", ".youtube.com TRUE / TRUE 0 SID abc")
    monkeypatch.setenv("INSTAGRAM_SESSION_ID", "mock_ig_session_999")
    monkeypatch.setenv("INSTAGRAM_USER_ID", "12345678")
    path = yo.cookiefile()
    body = open(path).read()
    assert body.startswith("# Netscape HTTP Cookie File")
    assert ".youtube.com\tTRUE\t/\tTRUE\t0\tSID\tabc" in body
    assert ".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tmock_ig_session_999" in body
    assert ".instagram.com\tTRUE\t/\tTRUE\t2147483647\tds_user_id\t12345678" in body
    monkeypatch.setattr(yo, "_cookie_loaded", False)
    monkeypatch.setattr(yo, "_cookie_cache", None)


@pytest.mark.parametrize("msg,blocked", [
    ("ERROR: [youtube] x: Failed to extract any player response; please report", True),
    ("Sign in to confirm you're not a bot", True),
    ("HTTP Error 429: Too Many Requests", True),
    ("Private video. Sign in if you've been granted access", False),
])
def test_block_detection(msg, blocked):
    assert yo.is_youtube_block(msg) is blocked


@pytest.mark.parametrize("msg,blocked", [
    ("ERROR: [Instagram] abc: Instagram sent an empty media response. Check if this post is accessible in your browser without being logged-in.", True),
    ("use --cookies for the authentication", True),
    ("Private video", False),
])
def test_instagram_block_detection(msg, blocked):
    assert yo.is_instagram_block(msg) is blocked


def test_ytdlp_engine_maps_instagram_empty_response_to_login_required(monkeypatch):
    class Boom:
        def __init__(self, *_a, **_k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def extract_info(self, *_a, **_k):
            raise Exception("ERROR: [Instagram] C_q8L: Instagram sent an empty media response. Check if this post is accessible in your browser without being logged-in.")
    monkeypatch.setattr(yte.yt_dlp, "YoutubeDL", Boom)
    with pytest.raises(AppError) as ei:
        asyncio.run(yte.YtDlpEngine().extract("https://www.instagram.com/reel/C_q8L/", ExtractContext(url="u")))
    assert ei.value.code == ErrorCode.LOGIN_REQUIRED


def test_ytdlp_engine_maps_bot_check_to_source_blocked_not_private(monkeypatch):
    class Boom:
        def __init__(self, *_a, **_k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def extract_info(self, *_a, **_k):
            raise Exception("ERROR: [youtube] G3WASPVq54Q: Sign in to confirm you're not a bot")
    monkeypatch.setattr(yte.yt_dlp, "YoutubeDL", Boom)
    with pytest.raises(AppError) as ei:
        asyncio.run(yte.YtDlpEngine().extract("https://youtu.be/G3WASPVq54Q", ExtractContext(url="u")))
    assert ei.value.code == ErrorCode.SOURCE_BLOCKED and ei.value.retryable


def test_instagram_embed_parser():
    d = ig.parse_embed_html(EMBED_HTML)
    assert d["videos"] == ["https://scontent.cdninstagram.com/v/t50/abc.mp4?x=1&y=2"]
    assert d["images"][0].endswith("thumb.jpg")
    assert d["author"] == "dhrusavlogs" and "street food" in d["caption"]


def test_instagram_embed_engine(monkeypatch):
    class Resp:
        status_code = 200
        text = EMBED_HTML

    class Client:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def get(self, url):
            assert url == "https://www.instagram.com/p/De18B6nDB7N/embed/captioned/"
            return Resp()

    monkeypatch.setattr(ig.httpx, "AsyncClient", Client)
    r = asyncio.run(ig.InstagramEmbedEngine().extract(
        "https://www.instagram.com/reel/De18B6nDB7N/?igsh=x", ExtractContext(url="u")))
    assert r.items[0].kind == "video" and r.author["username"] == "dhrusavlogs"


def test_unknown_error_codes_exist():
    assert ErrorCode.LOGIN_REQUIRED and ErrorCode.SOURCE_BLOCKED


def test_resolve_youtube_blocked_returns_degraded_fast(monkeypatch):
    from starlette.testclient import TestClient
    import main

    async def blocked(*_a, **_k):
        raise AppError(ErrorCode.SOURCE_BLOCKED, "YouTube is temporarily blocking our server.")

    calls = {"legacy": 0}

    def legacy(*_a, **_k):
        calls["legacy"] += 1
        return {}

    def fallback(url, vid):
        return {"title": "Mahadev vs Ravana", "platform": "youtube", "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "thumbnails": [{"quality": "HD", "resolution": "1280x720", "url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"}],
                "video_formats": [], "audio_formats": []}

    monkeypatch.setattr(main.engine_registry, "execute_chain", blocked)
    monkeypatch.setattr(main, "extract_media", legacy)
    monkeypatch.setattr(main, "extract_youtube_fallback", fallback)
    monkeypatch.setattr(main, "_yt_fb", lambda: None)
    main._RESOLVE_CACHE.clear()
    c = TestClient(main.app)
    r = c.post("/api/resolve", json={"url": "https://www.youtube.com/shorts/G3WASPVq54Q?feature=share"},
               headers={"Origin": "https://ovd.winplaybox.in"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["degraded"] is True and d["data"]["notice"]["code"] == "SOURCE_BLOCKED"
    assert d["data"]["notice"]["downloads_available"] is False
    assert calls["legacy"] == 0  # no second yt-dlp run


def test_download_video_blocked_returns_friendly_json(monkeypatch):
    from starlette.testclient import TestClient
    import main

    def boom(*_a, **_k):
        raise Exception("ERROR: [youtube] G3WASPVq54Q: Failed to extract any player response; please report this issue")
    monkeypatch.setattr(main, "run_download_video_task", boom)
    monkeypatch.setattr(main, "_is_public_http_url", lambda u: True)
    r = TestClient(main.app).get("/api/download_video", params={"url": "https://www.youtube.com/watch?v=G3WASPVq54Q", "height": "1080"},
                                 headers={"Origin": "https://ovd.winplaybox.in"})
    assert r.status_code == 503
    j = r.json()
    assert j["error"]["code"] == "SOURCE_BLOCKED" and "yt-dlp" not in j["error"]["message"] and "ERROR" not in j["error"]["message"]


def test_download_falls_back_to_pytubefix_when_ytdlp_blocked(monkeypatch, tmp_path):
    import main

    class Blocked:
        def __init__(self, *_a, **_k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def download(self, *_a, **_k):
            raise Exception("ERROR: [youtube] x: Sign in to confirm you're not a bot")

    called = {}

    class FB:
        @staticmethod
        def download_video(url, height, out_dir):
            called["args"] = (url, height, out_dir)
            open(f"{out_dir}/media.mp4", "wb").write(b"x")

    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", Blocked)
    monkeypatch.setattr(main, "_yt_fb", lambda: FB)
    main.run_download_video_task("https://youtu.be/G3WASPVq54Q", 720, str(tmp_path / "media.%(ext)s"))
    assert called["args"][1] == 720 and (tmp_path / "media.mp4").exists()


def test_non_youtube_errors_are_not_swallowed(monkeypatch, tmp_path):
    import main

    class Fail:
        def __init__(self, *_a, **_k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def download(self, *_a, **_k):
            raise Exception("HTTP Error 404")

    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", Fail)
    with pytest.raises(Exception):
        main.run_download_video_task("https://vimeo.com/1", 720, str(tmp_path / "media.%(ext)s"))


def test_node_from_wheel_added_to_path():
    assert yo.ensure_node_on_path() is not None


def test_ssrf_guard_blocks_private_targets():
    import main
    for bad in ("http://127.0.0.1/x", "http://169.254.169.254/latest/meta-data", "file:///etc/passwd",
                "http://localhost:8000/", "ftp://example.com/x", "not a url"):
        assert main._is_public_http_url(bad) is False, bad


def test_download_endpoint_rejects_private_url():
    from starlette.testclient import TestClient
    import main
    r = TestClient(main.app).get("/api/download_video", params={"url": "http://169.254.169.254/x", "height": "720"},
                                 headers={"Origin": "https://ovd.winplaybox.in"})
    assert r.status_code == 400 and r.json()["error"]["code"] == "URL_INVALID"


def test_resolve_uses_pytubefix_when_ytdlp_blocked(monkeypatch):
    from starlette.testclient import TestClient
    import main

    async def blocked(*_a, **_k):
        raise AppError(ErrorCode.SOURCE_BLOCKED, "blocked")

    class FB:
        @staticmethod
        def resolve_info(url):
            return {"title": "Real Title", "author": "Real Channel", "duration": 125, "views": 4200,
                    "thumbnail": "https://i.ytimg.com/vi/G3WASPVq54Q/hqdefault.jpg", "heights": [720, 480, 360]}

    monkeypatch.setattr(main.engine_registry, "execute_chain", blocked)
    monkeypatch.setattr(main, "_yt_fb", lambda: FB)
    monkeypatch.setattr(main, "extract_youtube_fallback", main.extract_youtube_fallback)
    main._RESOLVE_CACHE.clear()
    r = TestClient(main.app).post("/api/resolve", json={"url": "https://youtu.be/G3WASPVq54Q"},
                                  headers={"Origin": "https://ovd.winplaybox.in"})
    d = r.json()
    assert r.status_code == 200 and d["ok"] and not d.get("degraded")
    data = d["data"]
    assert data["title"] == "Real Title" and data["author"]["displayName"] == "Real Channel"
    assert data["duration"] == 125 and data["stats"]["views"] == 4200
    labels = [v["label"] for v in data["videos"]]
    assert len(labels) == 3 and not any("1080" in l for l in labels)  # only qualities that exist
    assert len(data["audios"]) == 2 and data["audios"][0]["bitrate"] == 320
