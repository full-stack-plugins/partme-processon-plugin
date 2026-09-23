# 工具与技能路由（tool-routing）

## 上游 MCP 工具（实时 `tools/list` 为准）

| 工具 | 用途 | 何时选 |
|---|---|---|
| `generate_chart` | 生成成品图（可编辑源 + 预览） | 默认首选；图片 URL 失效时的兜底 |
| `generate_diagram` | 生成图（可编辑） | 与 chart 同类、按上游描述微调时 |
| `generate_diagram_dsl` | 产出可复用 DSL 文本 | 要把结构沉淀为 DSL、批量套用时 |

以工具实际输出为事实来源：上游没有暴露的方法（例如某些浏览器 SDK 手段）一律不宣称、
不臆造。

## 技能路由

| 需求 | 技能 | 备注 |
|---|---|---|
| 总规范 / 错误码 / 纪律 | `processon-harness`（本技能） | 先读再动手 |
| 路由与能力矩阵 | `processon-use` | 不确定走哪条路时 |
| 凭据配置 / 轮换 | `processon-setup` | SETUP/AUTH 错误也走它 |
| 结构与描述打磨 | `processon-prompt` | 生成前必经 |
| 流程图 / 泳道 / 时序 / 架构 / UML / ER | `processon-diagram` | 架构图默认块图 |
| 思维导图（7 种结构） | `processon-mindmap` | 自由/右向/组织/鱼骨/时间轴/树形/树表 |
| 信息图（关系→版式） | `processon-infographic` | 对比/循环/矩阵/环形/阶梯/放射 |
| 质量评审 | `processon-review` | 至多一轮修订 |

## 图形类型速查

- 流程图、泳道图（跨职能）、时序图、架构块图、UML、ER 模型。
- 思维导图、时间轴、组织架构图、SWOT / PEST、信息图。
- 架构需求务必写“架构块图”，并明确禁止 UML 类表。
