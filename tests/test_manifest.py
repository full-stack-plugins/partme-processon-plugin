import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestContractTest(unittest.TestCase):
    def test_plugin_exposes_skills_and_processon_mcp(self):
        plugin = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        mcp = json.loads((ROOT / ".mcp.json").read_text())

        self.assertEqual("codex-processon-plugin", plugin["name"])
        self.assertEqual("./skills/", plugin["skills"])
        self.assertEqual("./.mcp.json", plugin["mcpServers"])

        server = mcp["mcpServers"]["processon"]
        self.assertEqual("http", server["type"])
        self.assertEqual("https://smart-hd.processon.com/mcp", server["url"])
        self.assertEqual(
            "PROCESSON_MCP_AUTHORIZATION",
            server["env_http_headers"]["Authorization"],
        )
        self.assertNotIn("headers", server)

    def test_marketplace_exposes_installable_creativity_plugin(self):
        marketplace = json.loads(
            (ROOT / ".agents/plugins/marketplace.json").read_text()
        )

        self.assertEqual("partme-ai-processon", marketplace["name"])
        self.assertEqual("PartMe.AI ProcessOn", marketplace["interface"]["displayName"])
        self.assertEqual(1, len(marketplace["plugins"]))
        entry = marketplace["plugins"][0]
        self.assertEqual("codex-processon-plugin", entry["name"])
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_USE", entry["policy"]["authentication"])
        self.assertEqual("Creativity", entry["category"])
        self.assertEqual("url", entry["source"]["source"])
        self.assertEqual(
            "https://github.com/partme-ai/codex-processon-plugin.git",
            entry["source"]["url"],
        )
        self.assertEqual("main", entry["source"]["ref"])


if __name__ == "__main__":
    unittest.main()
