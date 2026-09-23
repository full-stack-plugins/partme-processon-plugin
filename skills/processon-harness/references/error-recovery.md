# 错误处置与对账（error-recovery）

## PROCESSON_SETUP_REQUIRED（缺凭据）

1. 不要反复重调工具——配置页已自动弹出（10 分钟冷却最多一次）。
2. 引导用户在本地密码框粘贴 Token 并保存；聊天里只说状态，不见值。
3. 保存后重试原请求；若 MCP 进程未重新加载凭据，由用户重启宿主应用。

## PROCESSON_AUTH_REQUIRED（凭据失效 / 轮换）

1. 代理已自动做了一次“清缓存重读凭据 + 重试”；走到这一步说明旧值确实失效。
2. 配置页会再次弹出，用户覆盖保存新 Token。
3. 确认保存状态后重试；同样不要在聊天里复读上游原始错误体。

## UNKNOWN_WRITE_RESULT（写类结果未知）——必须对账

触发条件：`tools/call` 超时或网络错。生成可能已发生，盲重试会重复生成。

1. 先静默查证：`tools/list` 确认会话活着；如能列出既有图，检查目标图是否已产生。
2. 已产生 → 视为成功，接评审与交付，不再重试。
3. 未产生 → 可重试一次；再失败就停下来向用户报告“结果未知 + 已做过的对账”。
4. 任何情况下禁止并行启动重绘循环。

## PROCESSON_UPSTREAM_ERROR（读类暂不可用）

- 读类请求可有界退避后重试（次数与间隔都要有上限）。
- 空响应特例：HTTP 202 + 空体是 notification 的正常终态，不是错误。

## INVALID_JSON_RPC

调用方输入不合法（非 JSON-RPC 2.0 / 坏行）。修输入即可，与凭据、网络无关；
无 id 的坏行会被静默丢弃（按 JSON-RPC 通知语义）。

## 用户报“token is Invalid”

- 先 `processon-setup` 状态检查定性（missing / configured）。
- configured 仍报错 → 走 AUTH_REQUIRED 流程换新 Token。
- 提醒用户确认 Token 来源（用户中心新建/复制）而非旧缓存。
