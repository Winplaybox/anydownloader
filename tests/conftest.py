import os
import sys

# Ensure required secrets exist with length >= 32 chars before app modules initialize
TEST_ADMIN_KEY = "admin_key_for_tests_" + "y" * 30
os.environ.setdefault("WPB_ADMIN_KEY", TEST_ADMIN_KEY)
os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_tests_" + "z" * 30)
os.environ.setdefault("LLM_DISABLE_POLLINATIONS", "1")
import tempfile as _tempfile

# Isolated, throw-away databases per test session (never the shared /var/tmp default).
_TEST_DATA_DIR = _tempfile.mkdtemp(prefix="ovd_test_data_")
os.environ.setdefault("WPB_DATA_DIR", _TEST_DATA_DIR)
os.environ.setdefault("EDITOR_WORK_DIR", os.path.join(_TEST_DATA_DIR, "editor"))
os.environ.setdefault("GUESTS_PER_IP_PER_DAY", "1000")
os.environ.setdefault("WPB_JWT_SECRET", "test_jwt_secret_for_unit_tests_" + "j" * 32)
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client.apps.googleusercontent.com")
