"""Production startup configuration validation regression tests."""
import ast
import os
import pathlib
import unittest
import urllib.parse
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "backend" / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(node for node in TREE.body if isinstance(node, ast.FunctionDef) and node.name == "_validate_production_configuration")
MODULE = ast.Module(body=[FUNCTION], type_ignores=[])
NS = {
    "os": os, "urllib": urllib, "EXTENSION_SECRET_KEY": "",
    "token_vault": type("Vault", (), {"store": type("Store", (), {"name": "memory"})()})(),
}
exec(compile(ast.fix_missing_locations(MODULE), "<startup-validator-test>", "exec"), NS)
validate = NS["_validate_production_configuration"]


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
                validate()
        message = str(ctx.exception)
        self.assertIn("TOKEN_HMAC_SECRET", message)
        self.assertIn("WPB_VAULT_SECRET", message)
        self.assertIn("EXTENSION_SECRET_KEY", message)


if __name__ == "__main__":
    unittest.main()
