"""表驱动契约测试：两个随插件分发的 hooks（意图识别 + 环境检查）。"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_hook(name: str):
    path = ROOT / "hooks" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"hooks_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_main(module, input_text: str) -> tuple[int, str]:
    output = io.StringIO()
    with mock.patch.object(sys, "stdin", io.StringIO(input_text)):
        with contextlib.redirect_stdout(output):
            code = module.main()
    return code, output.getvalue()


class IntentHookTest(unittest.TestCase):
    """check_processon_intent：UserPromptSubmit 意图提示，永远 exit 0、默认静默。"""

    @classmethod
    def setUpClass(cls):
        cls.module = load_hook("check_processon_intent")

    def run_prompt(self, prompt: str) -> tuple[int, str]:
        return run_main(self.module, json.dumps({"prompt": prompt}))

    def test_processon_intents_emit_the_router_hint(self):
        intents = (
            "画个流程图",
            "做个思维导图",
            "帮我画脑图",
            "转成泳道图",
            "UML 类图",
            "er 图",
            "画一张架构图",
            "生成时序图",
            "组织架构图",
            "做个信息图",
            "画个时间轴图",
            "用 ProcessOn 画图",
            "PROCESSON 生成",
            "processon diagram please",
        )
        for prompt in intents:
            with self.subTest(prompt=prompt):
                code, output = self.run_prompt(prompt)
                self.assertEqual(0, code)
                self.assertIn("/processon-diagram", output)
                self.assertIn("/processon-mindmap", output)
                self.assertIn("/processon-infographic", output)
                self.assertIn("/processon-review", output)
                self.assertIn("/processon-setup", output)

    def test_unrelated_prompts_stay_silent(self):
        unrelated = (
            "写一个 Python 脚本读取 CSV",
            "修复这个单元测试",
            "时间轴不带图字不应命中",
            "uml类图无空格按正则不命中",
            "",
        )
        for prompt in unrelated:
            with self.subTest(prompt=prompt):
                code, output = self.run_prompt(prompt)
                self.assertEqual(0, code)
                self.assertEqual("", output)

    def test_slash_commands_are_skipped_even_with_intent_words(self):
        code, output = self.run_prompt("/processon-diagram 画个流程图")
        self.assertEqual(0, code)
        self.assertEqual("", output)

    def test_malformed_or_empty_input_is_tolerated(self):
        for raw in ("", "not json", "{}", '{"prompt": null}', "[]"):
            with self.subTest(raw=raw):
                code, output = run_main(self.module, raw)
                self.assertEqual(0, code)
                self.assertEqual("", output)


class EnvCheckHookTest(unittest.TestCase):
    """env_check：SessionStart 环境自述，永远 exit 0。"""

    @classmethod
    def setUpClass(cls):
        cls.module = load_hook("env_check")

    def test_reports_readiness_on_the_real_tree(self):
        code, output = run_main(self.module, json.dumps({"source": "startup"}))
        self.assertEqual(0, code)
        self.assertIn("ProcessOn 插件环境：", output)
        self.assertIn("python3: ", output)
        self.assertIn("ProcessOn MCP proxy: 就绪", output)
        self.assertIn("ProcessOn 凭据: 首次使用时按 Skill 指引完成登录/令牌配置", output)

    def test_malformed_input_is_tolerated(self):
        for raw in ("", "not json", "[]"):
            with self.subTest(raw=raw):
                code, output = run_main(self.module, raw)
                self.assertEqual(0, code)
                self.assertIn("ProcessOn 插件环境：", output)

    def test_reports_missing_proxy_without_failing(self):
        with mock.patch.object(self.module.Path, "is_file", return_value=False):
            code, output = run_main(self.module, "")
        self.assertEqual(0, code)
        self.assertIn("脚本缺失", output)


if __name__ == "__main__":
    unittest.main()
