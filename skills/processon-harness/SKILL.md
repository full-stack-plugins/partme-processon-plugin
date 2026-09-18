---
name: processon-harness
description: "ProcessOn calling spec: the local stdio MCP proxy (secret-free credential setup via processon-setup), the diagram/mindmap/infographic skill surface, and the quality review workflow. Read this before any ProcessOn task."
---

# ProcessOn 调用规范

执行通道：本地 stdio MCP 代理 `scripts/processon_mcp_proxy.py`（无密钥落盘设计，
凭据经 `processon-setup` 引导配置）。

## 1. 凭据与环境

- 凭据缺失时代理会在会话内报出并给补办指引；不要替用户填。
- 代理按 `__file__` 定位插件根——从任何 cwd 启动均可。

## 2. 硬规则（来自上游验证记录）

- 图表结构先行：先 `processon-prompt` 打磨结构，再生成；不直接把叙述文本扔给生成工具。
- 交付前必须过 `processon-review` 质量评审。

## 3. 标准工作流

1. `processon-setup` 确认凭据与代理就绪。
2. 按类型走 `processon-diagram` / `processon-mindmap` / `processon-infographic`。
3. `processon-review` 评审后交付（可编辑源文件 + 预览）。

## 4. 纪律

- 生成的图必须可编辑（ProcessOn 源格式），不接受仅图片交付。
- 每步以工具输出为事实来源。
