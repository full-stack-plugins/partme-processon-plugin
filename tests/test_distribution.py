import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_distribution import validate_distribution


ROOT = Path(__file__).resolve().parents[1]


class DistributionValidatorTest(unittest.TestCase):
    def isolated_distribution(self, directory):
        target = Path(directory) / "plugin"
        shutil.copytree(
            ROOT,
            target,
            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.pyc"),
        )
        return target

    def test_missing_plugin_manifest_is_actionable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = validate_distribution(Path(temp_dir))
        self.assertIn("missing required file: .codex-plugin/plugin.json", errors)

    def test_repository_distribution_is_complete(self):
        self.assertEqual([], validate_distribution(ROOT))

    def test_missing_setup_asset_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.isolated_distribution(directory)
            (target / "assets/setup/app.js").unlink()
            errors = validate_distribution(target)
        self.assertIn("missing required file: assets/setup/app.js", errors)

    def test_missing_proxy_entry_point_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.isolated_distribution(directory)
            (target / "scripts/processon_mcp_proxy.py").unlink()
            errors = validate_distribution(target)
        self.assertIn("missing required file: scripts/processon_mcp_proxy.py", errors)

    def test_missing_setup_skill_is_actionable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.isolated_distribution(directory)
            shutil.rmtree(target / "skills/processon-setup")
            errors = validate_distribution(target)
        self.assertIn(
            "missing required file: skills/processon-setup/SKILL.md", errors
        )

    def test_altered_stdio_command_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.isolated_distribution(directory)
            path = target / ".mcp.json"
            payload = json.loads(path.read_text())
            payload["mcpServers"]["processon"]["command"] = "unsafe-runner"
            path.write_text(json.dumps(payload))
            errors = validate_distribution(target)
        self.assertIn("ProcessOn MCP must use the local secret-free stdio proxy", errors)

    def test_literal_mcp_credential_field_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = self.isolated_distribution(directory)
            path = target / ".mcp.json"
            payload = json.loads(path.read_text())
            payload["mcpServers"]["processon"]["token"] = "fixture-value"
            path.write_text(json.dumps(payload))
            errors = validate_distribution(target)
        self.assertIn("ProcessOn MCP must use the local secret-free stdio proxy", errors)


if __name__ == "__main__":
    unittest.main()
