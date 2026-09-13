import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def read_skill(self, name: str) -> str:
        return (ROOT / "skills" / name / "SKILL.md").read_text()

    def test_router_names_every_route_and_tool(self):
        text = self.read_skill("codex-processon-use")
        for value in (
            "codex-processon-diagram",
            "codex-processon-mindmap",
            "codex-processon-infographic",
            "generate_diagram",
            "generate_diagram_dsl",
        ):
            self.assertIn(value, text)

    def test_review_is_bounded(self):
        text = self.read_skill("codex-processon-review")
        self.assertIn("REVISE_ONCE", text)
        self.assertIn("at most one", text.lower())

    def test_secrets_are_not_echoed(self):
        combined = "\n".join(
            self.read_skill(name)
            for name in (
                "codex-processon-use",
                "codex-processon-prompt",
                "codex-processon-review",
            )
        )
        self.assertIn("never display", combined.lower())
        self.assertIn("PROCESSON_MCP_AUTHORIZATION", combined)


if __name__ == "__main__":
    unittest.main()
