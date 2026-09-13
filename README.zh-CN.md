# Codex ProcessOn 插件

通过 ProcessOn 官方远程 MCP，让 Codex 生成专业、精美且可编辑的 ProcessOn 图表。插件内置专业图、思维导图、结构化信息图、提示词构造与质量审查工作流。

## 能力

- ProcessOn 流程图、泳道图、时序图、UML、系统架构图、ER 图、组织/股权图、时间轴、SWOT、PEST。
- ProcessOn 思维导图、向右逻辑图、鱼骨图、WBS 树和树形表格。
- ProcessOn 对比、循环、环形、矩阵、阶梯、金字塔和射线信息图。
- 检查语义、关系、视觉层级、可读性、一致性与可编辑性的有界质量审查。
- 直接调用官方 MCP 的 `generate_diagram` 与 `generate_diagram_dsl`。

## 认证

在启动 Codex 的环境中设置完整 Authorization 请求头值：

```bash
export PROCESSON_MCP_AUTHORIZATION="Bearer <你的-processon-token>"
```

可在 <https://smart.processon.com/user> 创建 Token。禁止把 Token 提交到仓库或写入图表 Prompt。

## 本地安装

先用当前 `codex plugin --help` 确认本机支持的 marketplace 命令，把本仓库 marketplace 加入 Codex，再安装 `codex-processon-plugin@partme-ai-processon`。安装或更新后请新建 Codex 任务，以加载新的 Skills 和 MCP 工具。

## 可复制示例

- 用 ProcessOn 画生产级 Agent Harness 架构图，包含编排、记忆、工具网关、Guardrails、评测、可观测性、信任边界和故障恢复。
- 把 AI 功能从需求到上线画成产品、算法、后端、测试、运维五泳道图，包含评测失败、审批、监控和回滚。
- 为租户、智能体、会话、工具调用、Trace 和评测结果建立 ER 图。
- 画 Agent 请求调用 RAG、工具、Guardrails 与重试逻辑的时序图。
- 把故障报告整理成鱼骨图，并区分已证实原因与待验证假设。
- 制作质量、安全、可靠性、运维四象限 ProcessOn 信息图。

## 工作方式

路由 Skill 先选择图形类型，再建模关系、增强 ProcessOn Prompt、调用官方 MCP，并审查真实返回结果。发现明确可修正缺陷时最多重新生成一次。只有工具调用成功、但结果不可访问时，不会宣称视觉验收通过。

## 上游约束

- 地址：`https://smart-hd.processon.com/mcp`
- 协议：Streamable HTTP
- 文档声明的协议上限：MCP `2025-06-18`
- 文档声明的限流：每 Token 每分钟 600 次
- 当前工具：`generate_diagram`、`generate_diagram_dsl`

AI SDK 还提供浏览器侧的创建、更新、导出和实例管理能力，但本插件不会把未被 MCP 实际暴露的能力描述成可用工具。

## 开发验证

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
.venv/bin/python scripts/validate_distribution.py
.venv/bin/python /Users/wandl/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

参阅[文档索引](docs/ProcessOn-Documentation-Index.zh_CN.md)、[架构文档](docs/Codex-ProcessOn-Plugin-Architecture.zh_CN.md)和[技术方案](docs/Codex-ProcessOn-Plugin-Technical-Solution.zh_CN.md)。
