# ProcessOn AI/MCP 文档索引

核对日期：2026-09-12（Asia/Shanghai）

本索引记录以下页面当时在导航与正文中可见的全部文档条目，并提炼与插件实现直接相关的契约：

- AI 访问文档：<https://smart.processon.com/docs/ai>
- DSL 语法规则：<https://smart.processon.com/docs/syntax>
- MCP 协议文档：<https://smart.processon.com/docs/mcp>

## AI 访问文档全部条目

### 概述

- 工具覆盖两大核心场景能力
  - 专业图形生成
  - 信息图生成
- 输出模式
  - 可编辑嵌入模式
  - 纯图片输出模式
- 核心价值

页面说明专业图形覆盖流程图、泳道图、UML、组织架构图、股权架构图、主体关系图、时间轴、SWOT、PEST 等；信息图提供单行、单列、多行多列、环形、S 型、阶梯、锥形、矩阵、射线、对比、循环等结构。

### 快速开始

- 生成可编辑图形
  - 步骤 1：下载并导入 SDK
  - 步骤 2：初始化 SDK 实例
  - 步骤 3：准备渲染图形所需的容器
  - 步骤 4：创建图形
  - 步骤 5：让 AI 修改图表
- 生成图片
  - 方式一：通过 SDK 获取生成的图片
  - 步骤 1：下载并导入 SDK
  - 步骤 2：初始化 SDK 实例
  - 步骤 3：创建图形

### 完整示例

- 多渲染实例
- 错误处理示例
- 在 Vue 中使用
- 在 React 中使用

### API 参考

- 初始化
  - `new AiImageServerSdk(config)`
- 创建图表
  - `sdk.create(prompt, options)`
  - 创建图表附件列表（AttachmentInput）
- 创建图片
  - `sdk.createImage(prompt, options?)`
  - `sdk.updateImage(prompt, options?)`
  - `sdk.createImageFromData(encryptedData, options?)`
- 更新图表
  - `sdk.update(prompt, options)`
- 停止请求
  - `sdk.stopAi(options?)`
- 事件监听
  - `sdk.on(event, listener)`
  - `sdk.off(event, listener?)`
  - `sdk.once(event, listener)`
- 渲染已有数据
  - `sdk.restoreDiagramEditorByData(encryptedData, mountConfig, options?)`
- 视觉信息图能力
  - `sdk.editVisual('start', options?)`
  - `sdk.editVisual('complete', options?)`
  - `sdk.editVisual('cancel', options?)`
  - `sdk.recognizeVisual(options)`
- 实例管理
  - `sdk.diagramEditorIds`
  - `sdk.diagramEditors`
  - `sdk.getDiagramEditor(id)`
  - `sdk.getDiagramEditorIdByContainer(container)`
  - `sdk.destroyDiagramEditor(id)`
  - `sdk.destroy()`
- 渲染实例方法
  - `sdk.exportDiagram(options)`
  - `sdk.zoomDiagram(actionOrOptions)`
  - `sdk.getDiagramRawData(instanceOptions?)`
  - `sdk.getDiagramType(instanceOptions?)`
  - `sdk.setEditorMode(modeOrOptions)`
  - `sdk.setEditorActive(activeOrOptions)` / `sdk.isEditorActive(instanceOptions?)`
  - `sdk.getThemeListView(options)`
  - `sdk.setMindStructure(structureOrOptions)`
  - `sdk.applyMindTheme(themeOrOptions)`

### 常见问题全部条目

1. Q: visual 使用哪个编辑器？
2. Q: visual 的 update() 是直接改原图吗？
3. Q: editVisual('complete') 会自动覆盖当前编辑器吗？
4. Q: 如何停止正在进行的请求？
5. Q: 如何判断图表是否创建完成？
6. Q: 如何判断图表是否更新完成？
7. Q: 如何处理多个渲染实例？
8. Q: 如何处理错误？
9. Q: 如何处理 401 鉴权失败？
10. Q: 如何自定义 AI 服务器地址？
11. Q: 如何自定义渲染服务器地址？
12. Q: 如何自定义渲染 SDK host？
13. Q: 如何添加附件？
14. Q: 如何获取编辑器实例？

### 最佳实践全部条目

1. 事件监听
2. 错误处理
3. 资源清理
4. Token 管理
5. 多渲染实例管理
6. 超时处理

### AI SDK 关键契约

- `create()` 返回 `diagramEditorId`、DSL 与编辑器数据；完成后 Promise 才 resolve。
- `createImage()` 返回 PNG Base64、实例 ID、DSL 与编辑器数据。
- `update()` 依赖已有编辑器实例；visual 更新是“带上下文的重新生成”，不是原图局部修改。
- `exportDiagram()`：ProcessOn Editor 支持 PNG/SVG，Smart Editor 仅支持 PNG。
- `getDiagramRawData()` 返回可用于恢复或重新生成图片的数据。
- 常用事件包括 `ai:complete`、`render:renderComplete`、`error:ai`、`error:render`、`instance:create` 和 `instance:destroy`。
- 主要错误包括 `GET_TOKEN_ERROR`、`CREATE_LINK_ERROR`、`SERVER_ERROR`、`CONNECTION_ERROR`、`UNAUTHORIZED`、`IDLE_TIMEOUT`、`TOTAL_TIMEOUT`、`RENDER_ERROR`、`ATTACHMENT_VALIDATION_ERROR`、`REQUEST_FORMAT_ERROR`、`RESPONSE_FORMAT_ERROR`。
- 图片附件支持 JPG/JPEG/PNG 且不超过 2 MB；文档支持 PDF/DOC/DOCX/CSV/MD/TXT 且不超过 5 MB；音频支持 MP3 且不超过 5 MB。除 TXT 外，接入方应先上传并传 URL 元信息。

## DSL 语法规则可见条目

### 通用语法

- 设计目标
- DSL 标准结构
- 字段级规范
- 内容与特殊字符规则
- 示例

### 样式语法

- 语法定义
- 核心规则（强约束）
- 适用范围
- 合法示例
- 非法示例
- 规则总结

### 信息图语法

- 支持图形与 DSL 头格式
- 支持图形表
- data 整体结构
- 节点规则
- 完整示例

### 组织架构语法

- 整体结构
- 字段规则
- 合法性约束
- 完整示例

### 金字塔语法

- 整体结构
- 节点规则
- 完整示例

### 时间轴语法

- 整体结构
- 节点规则
- 完整示例

页面明确 Smart Graphics DSL 的通用骨架不替代具体图形 `type` 的 `data` 语义。插件因此不手写臆测 DSL；默认由官方 `generate_diagram_dsl` 生成。

## MCP 协议文档全部条目

### 1. 申请 Token

- 打开 <https://smart.processon.com/user> 创建访问令牌。

### 2. 快速开始

- 2.1 接口
  - 请求 URL
  - 传输协议与安全
- 2.2 MCP 配置
- 2.3 各平台接入教程
  - 2.3.1 Cherry Studio
  - 2.3.2 Cursor
- 2.4 注意事项
- 2.5 错误码说明

### 3. 调试指南

- 3.1 MCP Client 推荐
  - Cherry Studio
  - Cursor
  - Kiro
- 3.2 LLM 推荐
  - 页面在 2026-03-25 列出 Qwen、Doubao、Kimi、Zhipu、Gemini、DeepSeek 的若干型号；该清单会随时间变化，插件不将其固化为运行要求。

### 4. 支持的工具能力

- 4.1 工具列表
  - `generate_diagram`：根据自然语言生成图。
  - `generate_diagram_dsl`：根据自然语言生成图语言 DSL。
- 4.2 接口说明
  - 4.2.1 `generate_diagram`
    - 入参：`prompt`
  - 4.2.2 `generate_diagram_dsl`
    - 入参：`prompt`

### 5. 版本日志

- 2026-03-21，版本 1.0.0：MCP Server 初版。

### MCP 官方连接契约与插件适配

ProcessOn 页面提供的通用 MCP Client 配置使用远程 HTTP 与内联 Authorization 请求头。`processon-design` 不把真实 Token 写入版本化配置；已安装插件使用以下本地 stdio 入口：

```json
{
  "mcpServers": {
    "processon": {
      "type": "stdio",
      "command": "python3",
      "args": ["scripts/processon_mcp_proxy.py"],
      "cwd": "."
    }
  }
}
```

- 插件内部链路为本地 stdio → 官方 Streamable HTTP。
- 普通用户通过本地三步页面把原始 Token 保存到当前用户受限配置；代理添加 `Bearer` 前缀。
- `PROCESSON_MCP_TOKEN` 仅作为受控自动化进程的高级覆盖项。
- 最高支持 MCP Version `2025-06-18` 及之前版本。
- 每个 Token 每分钟最多 600 次请求。
- 401 表示 Token 无效、过期或未提供；不得盲目重试。
- 407 表示触发限流；应降低频率并进行有上限的退避。

### 实时发现差异

2026-09-13 使用 MCP `initialize` 与 `tools/list` 实测发现三个工具：`generate_chart`、`generate_diagram`、`generate_diagram_dsl`。其中 `generate_chart` 在上述 MCP 页面“工具列表”和“接口说明”中页面未列出；其在线 schema 与 `generate_diagram` 都是必填 `prompt`。实测 `generate_chart` 返回图片 URL 和可编辑 ProcessOn 源文件 URL，而 `generate_diagram` 返回静态对象存储图片 URL。插件在运行时存在 `generate_chart` 时优先使用它；若服务器未发布该工具，则回退到页面已文档化的 `generate_diagram`。

同次实测中，初始化和工具发现成功，但生成调用对测试凭证返回业务文本 `token is Invalid`。这证明传输和工具发现可用，但不构成生成能力验收；必须用有效的新 Token 完成三图测试后才能宣称端到端通过。

## 插件采用范围

插件保留对 MCP 页面公开工具的兼容回退，同时按实时工具发现选择更适合可编辑交付的能力。AI SDK 文档用于理解 ProcessOn 的完整产品能力和结果语义，不代表当前 MCP 已暴露 SDK 的更新、导出、实例管理或视觉编辑方法。任何未来扩展都必须以当时实际发现的 MCP 工具为准。
