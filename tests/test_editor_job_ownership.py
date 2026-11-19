import unittest

from backend.utils.job_access import job_owner_matches


class TestEditorJobOwnership(unittest.TestCase):
    def test_user_can_access_own_job(self):
        self.assertTrue(job_owner_matches({"client": "user-1"}, {"user_id": "user-1"}))

    def test_guest_can_access_own_job(self):
        self.assertTrue(job_owner_matches({"client": "guest-1"}, {"guest_id": "guest-1"}))

    def test_other_user_cannot_access_job_even_from_same_ip(self):
        self.assertFalse(job_owner_matches(
            {"client": "user-1"}, {"user_id": "user-2"}, fallback_key="same-ip"
        ))

    def test_ip_fallback_only_used_without_stable_identity(self):
        self.assertTrue(job_owner_matches({"client": "ip-hash"}, {}, fallback_key="ip-hash"))
        self.assertFalse(job_owner_matches({"client": "ip-hash"}, {"guest_id": "guest-2"}, fallback_key="ip-hash"))

    def test_missing_job_owner_denies(self):
        self.assertFalse(job_owner_matches({}, {"user_id": "user-1"}))


if __name__ == "__main__":
    unittest.main()
