import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DocumentationTest(unittest.TestCase):
    def test_index_lists_all_ai_and_mcp_primary_sections(self):
        text = (ROOT / "docs/ProcessOn-Documentation-Index.zh_CN.md").read_text()
        required = (
            "生成可编辑图形",
            "生成图片",
            "多渲染实例",
            "错误处理示例",
            "在 Vue 中使用",
            "在 React 中使用",
            "初始化",
            "创建图表",
            "创建图片",
            "更新图表",
            "停止请求",
            "事件监听",
            "渲染已有数据",
            "视觉信息图能力",
            "实例管理",
            "渲染实例方法",
            "申请 Token",
            "MCP 配置",
            "各平台接入教程",
            "错误码说明",
            "MCP Client 推荐",
            "LLM 推荐",
            "工具列表",
            "接口说明",
            "版本日志",
        )
        for heading in required:
            self.assertIn(heading, text)

    def test_index_records_every_ai_faq_and_best_practice(self):
        text = (ROOT / "docs/ProcessOn-Documentation-Index.zh_CN.md").read_text()
        required = (
            "visual 使用哪个编辑器",
            "visual 的 update() 是直接改原图吗",
            "editVisual('complete') 会自动覆盖当前编辑器吗",
            "如何停止正在进行的请求",
            "如何判断图表是否创建完成",
            "如何判断图表是否更新完成",
            "如何处理多个渲染实例",
            "如何处理错误",
            "如何处理 401 鉴权失败",
            "如何自定义 AI 服务器地址",
            "如何自定义渲染服务器地址",
            "如何自定义渲染 SDK host",
            "如何添加附件",
            "如何获取编辑器实例",
            "资源清理",
            "Token 管理",
            "多渲染实例管理",
            "超时处理",
        )
        for heading in required:
            self.assertIn(heading, text)

    def test_readmes_document_local_setup_and_advanced_override(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            self.assertNotIn("PROCESSON_MCP_AUTHORIZATION", text)
            self.assertIn("PROCESSON_MCP_TOKEN", text)
            self.assertIn("processon_setup.py ui", text)
            self.assertIn("processon_setup.py check", text)
            self.assertIn("~/.config/processon/credentials.json", text)
            self.assertIn("%APPDATA%", text)
            self.assertIn("0700", text)
            self.assertIn("0600", text)
            self.assertIn("Bearer ", text)
            self.assertGreaterEqual(text.count("ProcessOn"), 5)

    def test_bilingual_architecture_and_solution_pairs_exist(self):
        stems = (
            "Codex-ProcessOn-Plugin-Architecture",
            "Codex-ProcessOn-Plugin-Technical-Solution",
        )
        for stem in stems:
            self.assertTrue((ROOT / "docs" / f"{stem}.md").is_file())
            self.assertTrue((ROOT / "docs" / f"{stem}.zh_CN.md").is_file())

    def test_current_technical_docs_use_local_proxy_contract(self):
        names = (
            "ProcessOn-Documentation-Index.zh_CN.md",
            "Codex-ProcessOn-Plugin-Architecture.md",
            "Codex-ProcessOn-Plugin-Architecture.zh_CN.md",
            "Codex-ProcessOn-Plugin-Technical-Solution.md",
            "Codex-ProcessOn-Plugin-Technical-Solution.zh_CN.md",
        )
        combined = "\n".join((ROOT / "docs" / name).read_text() for name in names)
        self.assertNotIn("PROCESSON_MCP_AUTHORIZATION", combined)
        self.assertNotIn("env_http_headers", combined)
        self.assertIn("scripts/processon_mcp_proxy.py", combined)
        self.assertIn("UNKNOWN_WRITE_RESULT", combined)

    def test_index_distinguishes_live_tool_discovery_from_page_docs(self):
        text = (ROOT / "docs/ProcessOn-Documentation-Index.zh_CN.md").read_text()
        self.assertIn("实时发现差异", text)
        self.assertIn("generate_chart", text)
        self.assertIn("页面未列出", text)

    def test_readmes_share_marketing_hero_and_delivery_sections(self):
        hero = ROOT / "assets/processon-hero.png"
        self.assertTrue(hero.is_file())
        required_english = (
            "At a glance",
            "Architecture and core flow",
            "Capability matrix",
            "Quick start",
            "Verified results",
            "Security and privacy",
            "Troubleshooting",
        )
        required_chinese = (
            "一眼看懂",
            "架构与核心流程",
            "能力矩阵",
            "快速开始",
            "已验证成果",
            "安全与隐私",
            "故障排查",
        )
        english = (ROOT / "README.md").read_text()
        chinese = (ROOT / "README.zh-CN.md").read_text()
        self.assertIn("assets/processon-hero.png", "\n".join(english.splitlines()[:12]))
        self.assertIn("assets/processon-hero.png", "\n".join(chinese.splitlines()[:12]))
        for heading in required_english:
            self.assertIn(heading, english)
        for heading in required_chinese:
            self.assertIn(heading, chinese)

    def test_readmes_use_real_marketplace_install_commands(self):
        commands = (
            "codex plugin marketplace add partme-ai/codex-processon-plugin --ref main",
            "codex plugin marketplace add https://github.com/partme-ai/codex-processon-plugin.git --ref main --sparse .agents/plugins",
            "codex plugin marketplace add ./codex-processon-plugin",
            "codex plugin add codex-processon-plugin@partme-ai-processon",
        )
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            for command in commands:
                self.assertIn(command, text)

    def test_readmes_show_a_visual_result_gallery(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            self.assertIn("<img", text)
            self.assertGreaterEqual(text.count("<img"), 3)
            self.assertIn("Agent Harness", text)
            self.assertIn("AI delivery", text)

    def test_readmes_distinguish_official_mcp_example_from_installed_stdio_proxy(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            self.assertIn('"smart-mcp"', text)
            self.assertIn('"Authorization": "Bearer YOUR_MCP_TOKEN"', text)
            self.assertIn('"type": "stdio"', text)
            self.assertIn('"args": ["scripts/processon_mcp_proxy.py"]', text)
            self.assertIn("UNKNOWN_WRITE_RESULT", text)
            self.assertIn("HTTP 202", text)

    def test_readmes_keep_the_same_three_step_first_use_order(self):
        english = (ROOT / "README.md").read_text()
        chinese = (ROOT / "README.zh-CN.md").read_text()
        english_steps = [
            english.index("Open the ProcessOn user center"),
            english.index("Paste and save the Token"),
            english.index("Reopen Codex"),
        ]
        chinese_steps = [
            chinese.index("打开 ProcessOn 用户中心"),
            chinese.index("粘贴并保存 Token"),
            chinese.index("重新打开 Codex"),
        ]
        self.assertEqual(sorted(english_steps), english_steps)
        self.assertEqual(sorted(chinese_steps), chinese_steps)

    def test_privacy_discloses_local_storage_and_official_upstream(self):
        text = (ROOT / "PRIVACY.md").read_text()
        self.assertIn("credentials.json", text)
        self.assertIn("https://smart-hd.processon.com/mcp", text)
        self.assertIn("Authorization", text)


if __name__ == "__main__":
    unittest.main()
