import importlib.util
import io
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from email import message_from_bytes
from pathlib import Path
from threading import Event
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest


KEY = "test-worker-key"
VIDEO_URL = "https://www.youtube.com/watch?v=media-id"
INSTAGRAM_URL = "https://www.instagram.com/reel/media-id/"
MEDIA = b"mock media contents"


@pytest.fixture
def worker(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "pc-worker" / "worker.py"
    spec = importlib.util.spec_from_file_location("pc_worker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    store = tmp_path / "media"
    store.mkdir()
    cookies = tmp_path / "cookies.txt"
    cookies.write_text("# Netscape HTTP Cookie File\n")
    monkeypatch.setattr(module, "MEDIA_DIR", str(store))
    monkeypatch.setattr(module, "COOKIES_FILE", str(cookies))
    monkeypatch.setattr(module, "WORKER_KEY", KEY)
    monkeypatch.setattr(module, "PUBLIC_BASE", "https://worker.example.test")
    monkeypatch.setattr(module, "_ffmpeg_dir", lambda: "")
    return module


def request(worker, method, target, body=b"", headers=None):
    handler = object.__new__(worker.Handler)
    header_lines = [f"Content-Length: {len(body)}", *[f"{k}: {v}" for k, v in (headers or {}).items()]]
    raw_request = "\r\n".join([f"{method} {target} HTTP/1.0", *header_lines, "", ""]).encode()
    handler.rfile = io.BytesIO(raw_request + body)
    handler.wfile = io.BytesIO()
    handler.handle_one_request()
    raw_headers, response = handler.wfile.getvalue().split(b"\r\n\r\n", 1)
    status, headers = raw_headers.split(b"\r\n", 1)
    return int(status.split()[1]), message_from_bytes(headers), response


def post(worker, headers=None, **payload):
    return request(worker, "POST", "/download", json.dumps(payload).encode(), headers)


def mock_download(cmd, **kwargs):
    ext = "mp3" if "-x" in cmd else "mp4"
    path = Path(cmd[cmd.index("-o") + 1]).parent / f"media.{ext}"
    path.write_bytes(MEDIA)
    return subprocess.CompletedProcess(cmd, 0)


@pytest.mark.parametrize("headers", [{}, {"X-Worker-Key": "wrong"}, {"Authorization": "Bearer wrong"}])
def test_download_rejects_missing_or_bad_key(worker, headers):
    status, _, body = post(worker, headers, url=VIDEO_URL, kind="video", height=1080)
    assert status == 401
    assert json.loads(body)["ok"] is False


@pytest.mark.parametrize(
    ("auth", "url", "kind", "mime"),
    [
        ({"X-Worker-Key": KEY}, VIDEO_URL, "video", "video/mp4"),
        ({"Authorization": f"Bearer {KEY}"}, INSTAGRAM_URL, "video", "video/mp4"),
        ({"Authorization": f"Bearer {KEY}"}, VIDEO_URL, "audio", "audio/mpeg"),
    ],
)
def test_download_success_uses_server_cookies_and_returns_signed_url(worker, monkeypatch, auth, url, kind, mime):
    def run(cmd, **kwargs):
        assert cmd[-1] == url
        assert cmd[cmd.index("--cookies") + 1] == worker.COOKIES_FILE
        if kind == "video":
            assert "[height<=1080]" in cmd[cmd.index("-f") + 1]
        return mock_download(cmd, **kwargs)

    monkeypatch.setattr(worker.subprocess, "run", run)
    status, headers, body = post(worker, auth, url=url, kind=kind, height=1080)
    assert status == 200
    assert headers["Cache-Control"] == "no-store"
    payload = json.loads(body)
    assert set(payload) == {"ok", "url"} and payload["ok"] is True
    signed = urlsplit(payload["url"])
    assert signed.scheme == "https"
    assert signed.netloc == "worker.example.test"
    params = parse_qs(signed.query)
    assert set(params) == {"expires", "sig"}
    stored, = Path(worker.MEDIA_DIR).iterdir()
    assert int(params["expires"][0]) - stored.stat().st_mtime == 900
    assert signed.path.endswith("/" + stored.name)
    target = f"{signed.path}?{signed.query}"
    status, headers, body = request(worker, "GET", target)
    assert (status, headers["Content-Type"], headers["Cache-Control"], body) == (200, mime, "no-store", MEDIA)
    status, headers, body = request(worker, "HEAD", target)
    assert (status, headers["Content-Length"], body) == (200, str(len(MEDIA)), b"")


def test_concurrent_download_gets_429_and_health_reports_busy(worker, monkeypatch):
    started, release = Event(), Event()

    def run(cmd, **kwargs):
        started.set()
        if not release.wait(timeout=5):
            raise RuntimeError("test did not release mock downloader")
        return mock_download(cmd, **kwargs)

    monkeypatch.setattr(worker.subprocess, "run", run)
    auth = {"X-Worker-Key": KEY}
    with ThreadPoolExecutor(max_workers=1) as pool:
        active = pool.submit(post, worker, auth, url=VIDEO_URL, kind="video", height=1080)
        try:
            assert started.wait(timeout=5)
            status, _, health = request(worker, "GET", "/health")
            assert status == 200 and json.loads(health)["busy"] is True
            status, _, body = post(worker, auth, url=VIDEO_URL, kind="video", height=1080)
            assert status == 429 and json.loads(body)["ok"] is False
        finally:
            release.set()
        assert active.result(timeout=5)[0] == 200
    assert json.loads(request(worker, "GET", "/health")[2])["busy"] is False


def test_file_link_rejects_missing_tampered_or_expired_signature(worker, monkeypatch):
    monkeypatch.setattr(worker.subprocess, "run", mock_download)
    status, _, body = post(worker, {"X-Worker-Key": KEY}, url=VIDEO_URL)
    assert status == 200
    signed = urlsplit(json.loads(body)["url"])
    params = dict((key, values[0]) for key, values in parse_qs(signed.query).items())
    expires = int(params["expires"])
    signature = params["sig"]
    tampered = ("1" if signature[0] == "0" else "0") + signature[1:]
    for query in ("", urlencode({**params, "sig": tampered}), urlencode({**params, "expires": expires + 1})):
        assert request(worker, "GET", f"{signed.path}?{query}")[0] == 403

    monkeypatch.setattr(worker.time, "time", lambda: expires)
    assert request(worker, "GET", f"{signed.path}?{signed.query}")[0] == 403
    assert any(Path(worker.MEDIA_DIR).iterdir())


def test_cleanup_deletes_only_expired_worker_media(worker, capsys):
    store = Path(worker.MEDIA_DIR)
    now = worker.time.time()
    expired = store / ("a" * 32 + ".mp4")
    fresh = store / ("b" * 32 + ".mp3")
    unrelated = store / "unrelated.txt"
    for path, mtime in [(expired, now - worker.FILE_TTL_S - 1), (fresh, now), (unrelated, now - worker.FILE_TTL_S - 1)]:
        path.write_bytes(MEDIA)
        os.utime(path, (mtime, mtime))
    worker._purge_expired_files()
    assert set(store.iterdir()) == {fresh, unrelated}
    assert json.loads(capsys.readouterr().out)["count"] == 1


@pytest.mark.parametrize("body", [b"", b"not json", b"[]", b'{"url":"https://"}', b'{"url":"https://youtu.be/media","height":"bad"}'])
def test_invalid_download_request_returns_400(worker, body):
    status, _, response = request(worker, "POST", "/download", body, {"X-Worker-Key": KEY})
    assert status == 400 and json.loads(response)["ok"] is False
    assert not list(Path(worker.MEDIA_DIR).iterdir())


@pytest.mark.parametrize(("failure", "code", "event"), [("exit", 502, "download_failed"), ("empty", 502, "download_failed"), ("timeout", 504, "download_timeout")])
def test_failed_download_cleans_scratch_and_never_exposes_source_or_cookies(worker, monkeypatch, capsys, failure, code, event):
    url = VIDEO_URL + "&private=not-for-logs"

    def run(cmd, **kwargs):
        path = Path(cmd[cmd.index("-o") + 1]).parent / "incomplete.mp4.part"
        path.write_bytes(b"partial")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(cmd, kwargs["timeout"])
        return subprocess.CompletedProcess(cmd, int(failure == "exit"), stderr=f"{url} {worker.COOKIES_FILE}")

    monkeypatch.setattr(worker.subprocess, "run", run)
    status, _, body = post(worker, {"X-Worker-Key": KEY}, url=url)
    assert status == code and json.loads(body)["ok"] is False
    assert not list(Path(worker.MEDIA_DIR).iterdir())
    assert not worker._LOCK.locked()
    out = capsys.readouterr().out
    assert json.loads(out)["event"] == event
    assert url not in out and url.encode() not in body
    assert worker.COOKIES_FILE not in out and worker.COOKIES_FILE.encode() not in body
