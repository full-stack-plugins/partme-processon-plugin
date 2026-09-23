import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REAL_BEARER = re.compile(r"Bearer\s+(?!<|TOKEN_VALUE|test-secret-value)[A-Za-z0-9+/=_-]{20,}")


class SecurityContractTest(unittest.TestCase):
    def test_mcp_contains_only_a_secret_free_stdio_command(self):
        server = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["processon"]
        self.assertEqual(
            {"type", "command", "args", "cwd"},
            set(server),
        )
        serialized = json.dumps(server).lower()
        for forbidden in ("authorization", "token", "secret", "password"):
            self.assertNotIn(forbidden, serialized)

    def test_repository_contains_no_literal_bearer_credential(self):
        violations = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
                continue
            if path.suffix.lower() in {".png", ".pyc"}:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if REAL_BEARER.search(text):
                violations.append(str(path.relative_to(ROOT)))
        self.assertEqual([], violations)


if __name__ == "__main__":
    unittest.main()
