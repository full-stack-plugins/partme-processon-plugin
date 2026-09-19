import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestContractTest(unittest.TestCase):
    def test_plugin_exposes_skills_and_processon_mcp(self):
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        mcp = json.loads((ROOT / ".mcp.json").read_text())

        self.assertEqual("processon-design", plugin["name"])
        self.assertEqual("./skills/", plugin["skills"])
        self.assertEqual("./.mcp.json", plugin["mcpServers"])

        server = mcp["mcpServers"]["processon"]
        self.assertEqual(
            {
                "type": "stdio",
                "command": "python3",
                "args": ["scripts/processon_mcp_proxy.py"],
                "cwd": ".",
            },
            server,
        )

    def test_marketplace_exposes_installable_creativity_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text()
        )

        self.assertEqual("partme-ai-processon", marketplace["name"])
        self.assertEqual("ProcessOn Design", marketplace["interface"]["displayName"])
        self.assertEqual(1, len(marketplace["plugins"]))
        entry = marketplace["plugins"][0]
        self.assertEqual("processon-design", entry["name"])
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_USE", entry["policy"]["authentication"])
        self.assertEqual("Creativity", entry["category"])
        self.assertEqual("url", entry["source"]["source"])
        self.assertEqual(
            "https://github.com/full-stack-plugins/processon-design-plugin.git",
            entry["source"]["url"],
        )
        self.assertEqual("v0.2.4", entry["source"]["ref"])

    def test_plugin_uses_official_processon_name_and_icons(self):
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        interface = plugin["interface"]
        self.assertEqual("ProcessOn Design", interface["displayName"])
        self.assertEqual("./assets/official-logo.png", interface["logo"])
        self.assertEqual("./assets/official-logo.png", interface["logoDark"])
        self.assertEqual("./assets/composer-icon.png", interface["composerIcon"])
        self.assertEqual(
            ["./assets/processon-hero.png"],
            interface["screenshots"],
        )


if __name__ == "__main__":
    unittest.main()
