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

    def test_diagram_skill_covers_professional_families(self):
        text = self.read_skill("codex-processon-diagram")
        for value in (
            "flowchart",
            "swimlane",
            "sequence",
            "architecture",
            "ER",
            "UML",
            "SWOT",
            "PEST",
        ):
            self.assertIn(value.lower(), text.lower())

    def test_mindmap_skill_defines_seven_structures(self):
        text = self.read_skill("codex-processon-mindmap")
        for value in (
            "mind_free",
            "mind_right",
            "mind_org",
            "mind_ishikawa_left",
            "mind_timeline_h",
            "mind_tree_free",
            "mind_treeTable_left_title",
        ):
            self.assertIn(value, text)

    def test_infographic_skill_maps_relationships_to_layout(self):
        text = self.read_skill("codex-processon-infographic")
        for value in ("comparison", "cycle", "matrix", "ring", "staircase", "radial"):
            self.assertIn(value, text.lower())

    def test_architecture_defaults_to_blocks_not_class_tables(self):
        text = self.read_skill("codex-processon-diagram").lower()
        self.assertIn("architecture block diagram", text)
        self.assertIn("do not use uml class tables", text)


if __name__ == "__main__":
    unittest.main()
