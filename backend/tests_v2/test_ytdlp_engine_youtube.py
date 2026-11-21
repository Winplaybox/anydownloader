"""/api/resolve for YouTube went through engines/ytdlp_engine.py and signed raw googlevideo/HLS URLs
(an m3u8 manifest was downloaded as '.mp4'). Variants must use the server-side merge endpoints."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault("WPB_VAULT_SECRET", "test-secret")

INFO = {
    "id": "E9pv8ILNxHM", "title": "Vishnu ke 10 Avatar", "duration": 483, "thumbnails": [],
    "formats": [
        {"format_id": "91", "protocol": "m3u8_native", "ext": "mp4", "height": 144, "vcodec": "avc1", "acodec": "mp4a",
         "url": "https://manifest.googlevideo.com/api/manifest/hls_playlist/a.m3u8"},
        {"format_id": "137", "ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "none",
         "url": "https://rr1.googlevideo.com/videoplayback?a=1"},
        {"format_id": "136", "ext": "mp4", "height": 720, "vcodec": "avc1", "acodec": "none",
         "url": "https://rr1.googlevideo.com/videoplayback?a=2"},
        {"format_id": "140", "ext": "m4a", "vcodec": "none", "acodec": "mp4a", "abr": 129,
         "url": "https://rr1.googlevideo.com/videoplayback?a=4"},
    ],
}


class _FakeYDL:
    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def extract_info(self, url, download=False): return INFO


def test_youtube_variants_are_internal_merge_endpoints(monkeypatch):
    from backend.engines import ytdlp_engine as eng
    from backend.engines.base import ExtractContext
    from backend.normalizer import normalize_raw_result
    from backend.utils.security import verify_download_token
    monkeypatch.setattr(eng.yt_dlp, "YoutubeDL", _FakeYDL)

    url = "https://youtu.be/E9pv8ILNxHM"
    raw = asyncio.run(eng.YtDlpEngine().extract(url, ExtractContext(url=url, platform_id="youtube")))
    assert [i.height for i in raw.items if i.kind == "video"] == [1080, 720, 144]
    for i in raw.items:
        if i.kind in ("video", "audio"):
            assert i.url.startswith(("/api/download_video?", "/api/download_audio?"))
            assert "googlevideo" not in i.url and "m3u8" not in i.url
    assert all(i.has_audio and not i.needs_merge for i in raw.items if i.kind == "video")

    n = normalize_raw_result(raw, {"id": "youtube"}, "video").to_dict()
    assert len(n["videos"]) == 3 and len(n["audios"]) == 3
    for v in n["videos"]:
        assert verify_download_token(v["token"])["variant_url"].startswith("/api/download_video?")


def test_non_youtube_still_uses_raw_urls(monkeypatch):
    from backend.engines import ytdlp_engine as eng
    from backend.engines.base import ExtractContext
    monkeypatch.setattr(eng.yt_dlp, "YoutubeDL", _FakeYDL)
    url = "https://vimeo.com/1"
    raw = asyncio.run(eng.YtDlpEngine().extract(url, ExtractContext(url=url, platform_id="vimeo")))
    assert any(i.url.startswith("https://rr1.googlevideo.com") for i in raw.items if i.kind == "video")
