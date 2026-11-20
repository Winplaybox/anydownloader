import ast
import unittest
import urllib.parse

SOURCE = "backend/main.py"


def load_origin_matcher():
    with open(SOURCE, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_matches_allowed_origin")
    ns = {"urllib": urllib, "ALLOWED_ORIGINS": ["https://winplaybox.in", "http://localhost:3000"]}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), SOURCE, "exec"), ns)
    return ns["_matches_allowed_origin"]


class TestOriginAllowlist(unittest.TestCase):
    def test_exact_origin_is_allowed(self):
        match = load_origin_matcher()
        self.assertTrue(match("https://winplaybox.in"))
        self.assertTrue(match("https://winplaybox.in/path?x=1"))

    def test_prefix_domain_attack_is_rejected(self):
        match = load_origin_matcher()
        self.assertFalse(match("https://winplaybox.in.evil.example"))
        self.assertFalse(match("https://evil.example/winplaybox.in"))

    def test_scheme_and_port_must_match(self):
        match = load_origin_matcher()
        self.assertFalse(match("http://winplaybox.in"))
        self.assertFalse(match("http://localhost:5174"))
        self.assertTrue(match("http://localhost:3000"))


    def test_sensitive_diagnostics_handlers_require_admin(self):
        with open(SOURCE, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        functions = {node.name: node for node in tree.body if isinstance(node, ast.AsyncFunctionDef)}
        for name in ("queue_metrics_handler", "diag_handler"):
            self.assertIn(name, functions)
            calls = [node for node in ast.walk(functions[name]) if isinstance(node, ast.Call)]
            self.assertTrue(any(isinstance(call.func, ast.Name) and call.func.id == "authenticate_admin" for call in calls),
                          f"{name} must enforce admin authentication")

    def test_credentials_are_rejected(self):
        match = load_origin_matcher()
        self.assertFalse(match("https://user:pass@winplaybox.in"))


if __name__ == "__main__":
    unittest.main()
