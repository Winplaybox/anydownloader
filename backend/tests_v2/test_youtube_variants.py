"""YouTube resolve must never hand out raw googlevideo/HLS URLs (they saved an m3u8 playlist as .mp4)."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

INFO = {
    "title": "Vishnu ke 10 Avatar",
    "duration": 483,
    "formats": [
        {"format_id": "96", "protocol": "m3u8_native", "ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "mp4a",
         "url": "https://manifest.googlevideo.com/api/manifest/hls_playlist/x.m3u8"},
        {"format_id": "137", "protocol": "https", "ext": "mp4", "height": 1080, "vcodec": "avc1", "acodec": "none",
         "url": "https://rr1.googlevideo.com/videoplayback?a=1"},
        {"format_id": "136", "protocol": "https", "ext": "mp4", "height": 720, "vcodec": "avc1", "acodec": "none",
         "url": "https://rr1.googlevideo.com/videoplayback?a=2"},
        {"format_id": "18", "protocol": "https", "ext": "mp4", "height": 360, "vcodec": "avc1", "acodec": "mp4a",
         "url": "https://rr1.googlevideo.com/videoplayback?a=3"},
        {"format_id": "140", "protocol": "https", "ext": "m4a", "vcodec": "none", "acodec": "mp4a",
         "url": "https://rr1.googlevideo.com/videoplayback?a=4"},
    ],
}


def test_variants_use_server_side_merge_not_raw_urls(monkeypatch):
    from backend.extractors import youtube as yt
    monkeypatch.setattr(yt.yt_dlp, "YoutubeDL", lambda opts: _FakeYDL())
    res = asyncio.run(yt.YouTubeExtractor().resolve("https://youtu.be/E9pv8ILNxHM"))
    video = [i for i in res.items if i.kind == "video"][0]
    assert [v.height for v in video.variants] == [1080, 720, 360]   # deduped, one per height
    for v in video.variants:
        assert v.url.startswith("/api/download_video?url=")
        assert "googlevideo" not in v.url and "m3u8" not in v.url
        assert v.hasAudio is True
        assert v.downloadUrl.startswith("/api/download?token=")


class _FakeYDL:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download=False):
        return INFO
