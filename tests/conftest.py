import os
import sys

# Ensure required secrets exist with length >= 32 chars before app modules initialize
TEST_ADMIN_KEY = "admin_key_for_tests_" + "y" * 30
os.environ.setdefault("WPB_ADMIN_KEY", TEST_ADMIN_KEY)
os.environ.setdefault("WPB_VAULT_SECRET", "test_vault_secret_for_tests_" + "z" * 30)
os.environ.setdefault("LLM_DISABLE_POLLINATIONS", "1")
