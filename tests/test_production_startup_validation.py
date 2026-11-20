"""Production startup configuration validation regression tests."""
import os
import unittest
from unittest.mock import patch

from backend.main import _validate_production_configuration


class TestProductionStartupValidation(unittest.TestCase):
    def test_production_rejects_missing_secrets(self):
        keys = (
            "EXTENSION_SECRET_KEY", "JOB_OWNER_SECRET", "PUBLIC_BASE_URL", "JOBS_DIR",
            "WPB_ADMIN_KEY", "ADMIN_API_KEY", "SUPABASE_JWT_SECRET", "WPB_ADMIN_EMAILS",
            "TOKEN_HMAC_SECRET", "WPB_VAULT_SECRET",
        )
        env = {k: v for k, v in os.environ.items() if k not in keys}
        env["WPB_ENV"] = "production"
        env.pop("RENDER", None)
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                _validate_production_configuration()
        message = str(ctx.exception)
        self.assertIn("TOKEN_HMAC_SECRET", message)
        self.assertIn("WPB_VAULT_SECRET", message)
        self.assertIn("EXTENSION_SECRET_KEY", message)


if __name__ == "__main__":
    unittest.main()
