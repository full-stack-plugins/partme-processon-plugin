#!/usr/bin/env python3
"""UserPromptSubmit hook: point ProcessOn-shaped requests at the plugin commands.

Advisory only — always exits 0; silent unless the prompt looks ProcessOn-related.
"""
from __future__ import annotations

import json
import re
import sys

INTENT_RE = re.compile(
    r"processon|流程图|思维导图|脑图|泳道图|\buml\b|\ber\s*图\b|架构图|时序图|组织架构|信息图|时间轴图",
    re.IGNORECASE,
)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    prompt = ""
    if isinstance(payload, dict):
        prompt = str(payload.get("prompt") or "")

    if prompt.strip().startswith("/"):
        return 0

    if INTENT_RE.search(prompt):
        print(
            "提示：该请求疑似 ProcessOn 相关。可用 /processon 总入口或细分命令 "
            "(/processon-diagram /processon-mindmap /processon-infographic "
            "/processon-review /processon-setup)；MCP 工具经 processon 代理提供。"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
