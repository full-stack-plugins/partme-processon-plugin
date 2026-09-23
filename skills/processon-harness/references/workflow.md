# 调用链与状态机（workflow）

## 调用链

```
宿主 agent（Codex / ZCode / Kimi …）
  └─ stdio：每行一个 JSON-RPC 2.0 消息
      └─ scripts/processon_mcp_proxy.py（入口 shim）
          └─ processon_harness/mcp_proxy.py
              ├─ ProcessOnProxy.handle_line：入站校验 + 错误消毒
              └─ ProcessOnTransport.send：Bearer 注入 + 会话保持 + 上游 POST
                  └─ 官方 ProcessOn MCP（Streamable HTTP，SSE 或 JSON 响应）
```

- 代理按 `__file__` 解析插件根，任意 cwd 可启动。
- 会话头 `Mcp-Session-Id` 由上游下发并在后续请求中保持。
- 协议版本协商：`MCP-Protocol-Version`（实测 2025-06-18）。

## 请求分类与超时

| 类别 | 判定 | 超时 | 失败语义 |
|---|---|---|---|
| 读类 | `tools/list` 等 | 短超时 | `PROCESSON_UPSTREAM_ERROR`，可安全重试 |
| 写类 | `tools/call` 一律按写类 | 长超时（生成级） | `UNKNOWN_WRITE_RESULT`，先对账再重试 |

## 错误码表

| data code | 含义 | 处置 |
|---|---|---|
| `PROCESSON_SETUP_REQUIRED` | 无凭据 | 配置页已自动弹出，等用户保存后重试 |
| `PROCESSON_AUTH_REQUIRED` | 凭据失效（401 或业务层判定） | 同上；401 会先自动重载凭据重试一次 |
| `PROCESSON_UPSTREAM_ERROR` | 上游暂不可用 / 空响应 | 读类可有界退避重试 |
| `UNKNOWN_WRITE_RESULT` | 写类结果未知 | 先对账（查 `tools/list` 与既有图），禁止盲重试 |
| `INVALID_JSON_RPC` | 入站消息不合法 | 修正调用方输入，与凭据无关 |

所有对外错误经 `sanitize_rpc_error` 脱敏：绝不携带 Token、上游原始错误体或文件路径。

## 认证状态机

1. `get_token` 缺失 → 触发本地配置页 → `PROCESSON_SETUP_REQUIRED`。
2. 上游 401 第一次 → 清缓存重读凭据（覆盖“轮换落盘后自动恢复”）→ 自动重试。
3. 上游 401 第二次 → 触发配置页 → `PROCESSON_AUTH_REQUIRED`。
4. HTTP 200 但业务层报 token 无效 → 与第 3 步同等处理。
5. 配置页触发器带 600 秒冷却（原子 marker 文件），失败风暴最多弹一页。

## 凭据解析链

`EnvironmentSecretProvider`（`PROCESSON_MCP_TOKEN`）优先 →
`UserConfigSecretProvider`（用户级配置文件）兜底；复合提供器按序取第一个非空值。
保存永远只写用户级文件（0600 原子写 + 目录属主/符号链接校验），环境变量只读不写。
