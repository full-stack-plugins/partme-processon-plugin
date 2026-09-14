import tempfile
import unittest
from pathlib import Path

from processon_harness.setup_trigger import launch_setup_ui_once


class SetupTriggerTests(unittest.TestCase):
    def test_repeated_authentication_failures_open_only_one_window_during_cooldown(self):
        calls = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugin_root = root / "plugin"
            script = plugin_root / "scripts" / "processon_setup.py"
            script.parent.mkdir(parents=True)
            script.write_text("# setup\n", encoding="utf-8")
            marker = root / "setup-trigger.json"

            first = launch_setup_ui_once(
                plugin_root=plugin_root,
                marker_path=marker,
                now=lambda: 1000.0,
                launcher=lambda command: calls.append(command),
            )
            second = launch_setup_ui_once(
                plugin_root=plugin_root,
                marker_path=marker,
                now=lambda: 1001.0,
                launcher=lambda command: calls.append(command),
            )

            self.assertTrue(first)
            self.assertFalse(second)
            self.assertEqual([[str(script.resolve()), "ui"]], [call[-2:] for call in calls])
            self.assertEqual('{"launched_at":1000.0}\n', marker.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
