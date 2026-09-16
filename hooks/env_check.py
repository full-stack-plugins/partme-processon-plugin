#!/usr/bin/env python3
"""SessionStart hook: report ProcessOn proxy readiness for this plugin.

Advisory only — always exits 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    lines: list[str] = []
    lines.append(f"python3: {sys.version.split()[0]}")

    proxy = Path(__file__).resolve().parents[1] / "scripts" / "processon_mcp_proxy.py"
    lines.append("ProcessOn MCP proxy: 就绪" if proxy.is_file() else "ProcessOn MCP proxy: 脚本缺失")

    lines.append("ProcessOn 凭据: 首次使用时按 Skill 指引完成登录/令牌配置")

    try:
        sys.stdin.read()
    except Exception:
        pass

    print("ProcessOn 插件环境：" + "；".join(lines))
    return 0


if __name__ == "__main__":
    try:
        json.load(sys.stdin)
    except Exception:
        pass
    sys.exit(main())
