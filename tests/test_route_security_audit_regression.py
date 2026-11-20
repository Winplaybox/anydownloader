"""Regression guards for high-risk route authorization boundaries.

These tests intentionally assert source-level route wiring so that an accidental
removal of ownership/admin decorators is caught before integration tests run.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITOR = (ROOT / "backend" / "routes_editor.py").read_text(encoding="utf-8")
STUDIO = (ROOT / "backend" / "routes_studio.py").read_text(encoding="utf-8")
AUTOPILOT = (ROOT / "backend" / "routes_autopilot.py").read_text(encoding="utf-8")
TEMP_MEDIA = (ROOT / "backend" / "routes_temp_media.py").read_text(encoding="utf-8")
ZERO_TRUST = (ROOT / "backend" / "security" / "zero_trust.py").read_text(encoding="utf-8")


def test_editor_job_status_and_file_routes_keep_owner_check():
    assert "def _job_access_allowed(request: Request, job: Dict[str, Any])" in EDITOR
    assert "job_owner_matches(job, identity, fallback_key=_client_key(request))" in EDITOR
    assert "if not job or not _job_access_allowed(request, job)" in EDITOR
    assert "if not job or not _job_access_allowed(request, job) or job.get(\"status\") != \"done\"" in EDITOR


def test_studio_admin_routes_are_decorated_and_admin_prefix_is_guarded():
    assert "@route(admin_only=True)" in STUDIO
    assert 'ADMIN_ONLY_PATH_PREFIXES = ("/admin/", "/api/v1/system/", "/api/v1/studio/admin/")' in ZERO_TRUST
    assert 'if path.startswith(ADMIN_ONLY_PATH_PREFIXES):' in ZERO_TRUST
    assert "if not authenticate_admin(request):" in ZERO_TRUST


def test_autopilot_mutations_use_admin_route_decorator():
    for name in ("autopilots_save", "autopilots_delete", "jobs_create", "job_regen",
                 "job_publish", "job_cancel", "accounts_connect", "accounts_delete"):
        marker = f"async def {name}("
        assert marker in AUTOPILOT, f"missing handler {name}"
        before = AUTOPILOT[:AUTOPILOT.index(marker)]
        assert "@admin_route" in before.splitlines()[-3:], f"{name} missing admin_route decorator"


def test_temp_media_mutations_require_shared_api_or_worker_key():
    assert "async def upload_handler(request):" in TEMP_MEDIA
    assert "if not _authorized(request):" in TEMP_MEDIA
    assert "async def delete_handler(request):" in TEMP_MEDIA
    assert "auto_key" in TEMP_MEDIA and "worker_key" in TEMP_MEDIA and "worker_secret" in TEMP_MEDIA
    assert "_ID_RE.fullmatch(media_id)" in TEMP_MEDIA
    assert "async def serve_handler(request):" in TEMP_MEDIA
