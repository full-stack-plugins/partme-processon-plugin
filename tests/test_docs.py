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

    def test_readmes_document_runtime_secret_and_examples(self):
        for name in ("README.md", "README.zh-CN.md"):
            text = (ROOT / name).read_text()
            self.assertIn("PROCESSON_MCP_AUTHORIZATION", text)
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


if __name__ == "__main__":
    unittest.main()
