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
                "codex-processon-setup",
                "codex-processon-prompt",
                "codex-processon-review",
            )
        )
        self.assertIn("never display", combined.lower())
        self.assertNotIn("PROCESSON_MCP_AUTHORIZATION", combined)
        self.assertNotIn("paste your token into chat", combined.lower())

    def test_setup_skill_routes_all_credential_states(self):
        setup = self.read_skill("codex-processon-setup")
        router = self.read_skill("codex-processon-use")
        for value in ("首次使用", "缺少凭证", "凭证失效", "轮换 Token"):
            self.assertIn(value, setup)
        for value in (
            "PROCESSON_SETUP_REQUIRED",
            "PROCESSON_AUTH_REQUIRED",
            "codex-processon-setup",
        ):
            self.assertIn(value, router)

    def test_setup_skill_has_progressive_disclosure_resources(self):
        skill_dir = ROOT / "skills" / "codex-processon-setup"
        text = (skill_dir / "SKILL.md").read_text()
        for name in (
            "workflow.md",
            "security.md",
            "anti-patterns.md",
            "faq-deep.md",
            "examples.md",
        ):
            self.assertTrue((skill_dir / "references" / name).is_file())
            self.assertIn(name, text)

    def test_setup_skill_never_routes_secrets_into_project_or_shell_files(self):
        setup_dir = ROOT / "skills" / "codex-processon-setup"
        combined = "\n".join(path.read_text() for path in setup_dir.rglob("*.md"))
        prohibited = ("写入 .mcp.json", "写入 .zshrc", "打印 Token 值")
        for phrase in prohibited:
            self.assertNotIn(phrase, combined)

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

    def test_router_prefers_editable_live_tool_with_documented_fallback(self):
        text = self.read_skill("codex-processon-use")
        self.assertIn("generate_chart", text)
        self.assertIn("prefer", text.lower())
        self.assertIn("fall back", text.lower())


if __name__ == "__main__":
    unittest.main()
