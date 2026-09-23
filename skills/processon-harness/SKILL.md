---
name: processon-harness
description: "ProcessOn calling spec: the local stdio MCP proxy (secret-free credential setup via processon-setup), the diagram/mindmap/infographic skill surface, and the quality review workflow. Use for any ProcessOn task; do not use for non-ProcessOn requests or account administration. Read this before any ProcessOn task."
---

# ProcessOn 调用规范（Harness）

执行通道：本地 stdio MCP 代理 `scripts/processon_mcp_proxy.py`（无密钥落盘设计，
凭据经 `processon-setup` 引导配置）。本技能是所有 ProcessOn 任务的总规范：
凭据契约、错误码语义、技能路由、交付纪律都以本文为准。

## 30 秒快速开始

直接命中本规范的请求形如：

- "用 ProcessOn 画一张系统架构图。"
- "把这个业务流程变成泳道图，用 ProcessOn。"
- "ProcessOn 生成的图帮我先审一遍再交付。"
- “生成失败提示 unknown write result，接下来怎么办？”

执行顺序见下方 Step 1–5；细节按“渐进披露”按需加载对应文件。

## 什么时候使用（When to use）

- 任何要调用 ProcessOn 生成图表、思维导图、信息图的任务，先读本规范再动手。
- 出现 `PROCESSON_SETUP_REQUIRED`、`PROCESSON_AUTH_REQUIRED`、`UNKNOWN_WRITE_RESULT`
  等代理错误码，需要按本规范解释与处置。
- 需要在多个制图技能（diagram / mindmap / infographic）与评审技能之间路由时。
- 需要核对“可编辑交付、评审闭环、不静默重试”这类交付纪律时。

不适用（do not use）：非 ProcessOn 的绘图请求（应使用其他工具）；ProcessOn 账号
管理、密码找回、权限与套餐变更；替用户创建 Token 或代填凭据；批量抓取或上传
用户未授权的本地文件。

## Capability boundary（能力边界）

### ✅ 处理得好

- 经本地 stdio 代理调用远程 ProcessOn MCP，生成可编辑的流程图 / 泳道图 / 时序图 /
  架构块图 / UML / ER / 思维导图 / 时间轴 / 组织架构 / 信息图。
- 凭据缺失或失效后的安全恢复路径（自动弹出本地配置页，10 分钟冷却最多一次）。
- 生成结果的质量评审（`processon-review` 一轮修订闭环）与可编辑源文件交付。

### ⚠️ 需要用户动作或输入

- Token 的创建与粘贴：用户在 ProcessOn 用户中心自行创建，并只粘贴进本地配置页。
- 重启宿主应用：新凭据要被当前 MCP 进程重新加载时由用户重启。
- 启动按钮：配置页的“启动”按钮当前仅内置 Codex 宿主命令，其他宿主请手动重启
  自己的编码助手（详见 Gotchas 第 8 条）。

### ❌ 不适用 / 越界（Out of scope）

- 账号密码找回、套餐与云文件权限变更——走 ProcessOn 官方产品界面或支持渠道。
- 替他人配置私有 Token；每个用户各自配置自己的凭据。
- 静默重放生成请求：结果不确定时必须先对账，见 [error-recovery](references/error-recovery.md)。

## 标准工作流

### Step 1：确认凭据与代理就绪

以 `processon-setup` 的检查结果为唯一事实来源；凭据缺失就先引导本地配置，
不要替用户填，也不要把 Token 带进对话或命令行。

### Step 2：结构先行，定图表类型

先用 `processon-prompt` 打磨结构与图形类型描述（架构图明确要“架构块图”并禁止
UML 类表），再进入生成；不要把叙述原文直接扔给生成工具。类型路由矩阵加载
[tool-routing](references/tool-routing.md) 文件。

### Step 3：按类型生成

走 `processon-diagram` / `processon-mindmap` / `processon-infographic` 三个技能之一，
以工具输出为事实来源；返回的图片 URL 不可访问时优先改用 `generate_chart`。

### Step 4：质量评审

交付前必须过 `processon-review`（至多一轮修订），评审按结构、可读性、类型正确性
三个维度给结论，验收清单加载 [validation-checklist](references/validation-checklist.md) 文件。

### Step 5：可编辑交付

交付 ProcessOn 可编辑源文件加预览；不接受仅图片交付。若此前发生过生成类错误，
先完成对账再重试（参考 [error-recovery](references/error-recovery.md) 文件）。

## Rules（硬规则）

1. 图表结构先行：先 `processon-prompt` 打磨结构，再生成；不直接把叙述文本扔给生成工具。
2. 交付前必须过 `processon-review` 质量评审。
3. 生成的图必须可编辑（ProcessOn 源格式），不接受仅图片交付。
4. 每步以工具输出为事实来源，不臆造工具能力；上游没有的方法不要宣称。
5. 凭据永远不出现在聊天、命令参数、仓库文件、日志里；缺失时只报状态和补办指引。
6. 写类请求（`tools/call`）失败不静默重试：先按 `UNKNOWN_WRITE_RESULT` 语义对账。

## Gotchas（常见坑）

1. **凭据缺失≠报错了事**：代理报 `PROCESSON_SETUP_REQUIRED` 时会自动弹出本地配置页
   （10 分钟冷却内最多弹一次），正确动作是等用户保存后重试，不是反复重调。
2. **401 只自动重试一次**：代理会清缓存重读凭据再试一次（覆盖“轮换 Token 落盘后自动
   恢复”）；第二次仍 401 才升级为 `PROCESSON_AUTH_REQUIRED` 并再次弹配置页。
3. **HTTP 200 也可能是认证失败**：业务层 token 无效与 HTTP 401 同等处理，不要被
   状态码 200 误导。
4. **写类失败不许静默重试**：`tools/call` 超时或网络错会返回 `UNKNOWN_WRITE_RESULT`
   （生成状态未知），必须先对账再决定重试，否则会重复生成。
5. **202 空响应是正常的**：notification 类请求无返回消息，不是错误。
6. **Token 只进本地配置页**：不要接受用户把 Token 粘贴进聊天；也不要写入 `.mcp.json`、
   `.zshrc` 或任何仓库文件。环境变量 `PROCESSON_MCP_TOKEN` 仅供开发者在受控子进程里
   高级覆盖。
7. **架构图默认块图**：不指定就会被画成 UML 类表；要在需求里明确“架构块图”并禁止类表。
8. **启动按钮只内置 Codex 命令**：配置页的“启动”能力当前仅探测 Codex 宿主（桌面应用
   或 `codex` CLI）；ZCode / Kimi 等其他宿主需用户手动重启自己的编码助手来加载凭据。
9. **代理按 `__file__` 定位插件根**：从任何 cwd 启动都可以，不要假设工作目录。
10. **上游图片 URL 有生命周期**：交付要落到可编辑源文件，不要只发一个会失效的图片链接。
11. **限流要串行**：不要并行启动重绘循环；退避要有界。
12. **不要宣称越界能力**：建 Token、账号管理、权限变更都不是本插件能做的事。

## 校验清单（Validation / 自检）

交付前逐项 verify：

- [ ] 凭据状态确认过（configured），过程里没有回显任何凭据值。
- [ ] 图形类型在需求里写死，架构图已声明“块图、禁 UML 类表”。
- [ ] 结构稿经 `processon-prompt` 打磨过，评审至多修订一轮。
- [ ] 交付物是可编辑源文件 + 预览，不是裸图片链接。
- [ ] 若发生过生成类错误：已按对账流程确认无重复生成。

完整清单与评审契约加载 [validation-checklist](references/validation-checklist.md) 文件。

## 渐进披露索引（按需加载对应文件）

- 需要执行命令、解释代理状态机时，加载 [workflow](references/workflow.md) 文件。
- 处理凭据失效、轮换或任何安全疑问时，加载 [security](references/security.md) 文件。
- 遇到错误码要处置或“结果不确定要不要重试”时，加载 [error-recovery](references/error-recovery.md) 文件。
- 核对类型路由与工具矩阵时，加载 [tool-routing](references/tool-routing.md) 文件。
- 需要评审与交付验收细节时，加载 [validation-checklist](references/validation-checklist.md) 文件。
- 避免常见误用、需要正确替代写法时，加载 [anti-patterns](references/anti-patterns.md) 文件。
- 深度疑问（多任务、CI、团队共享）加载 [faq-deep](references/faq-deep.md) 文件。

完整示例（含 happy path、失败恢复、边界拒绝）见 [examples/happy-path](examples/happy-path.md)、
[examples/failure-recovery](examples/failure-recovery.md)、
[examples/boundary-refusal](examples/boundary-refusal.md)。
