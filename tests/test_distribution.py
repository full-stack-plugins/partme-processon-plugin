import tempfile
import unittest
from pathlib import Path

from scripts.validate_distribution import validate_distribution


ROOT = Path(__file__).resolve().parents[1]


class DistributionValidatorTest(unittest.TestCase):
    def test_missing_plugin_manifest_is_actionable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            errors = validate_distribution(Path(temp_dir))
        self.assertIn("missing required file: .codex-plugin/plugin.json", errors)

    def test_repository_distribution_is_complete(self):
        self.assertEqual([], validate_distribution(ROOT))


if __name__ == "__main__":
    unittest.main()
