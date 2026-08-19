# providers/cursor.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~207 · harness transport（Cursor 订阅） · refactor-status: ok`

## 职责
在订阅认证下通过 `cursor-agent` 跑完**一整个** agent step —— 这是可用预防型控制最弱的
后端，因此也是**背着侦测型兜底**的那一个。

## 功能
headless `cursor-agent --print --force --output-format stream-json`，
**prompt 走 STDIN**，按行解析事件，每次会话写一份桥 MCP 配置，并强制做一次运行后审计。

## 公开契约
`CursorTransport`（`auth_gap`、`run_session`、`complete`）、`spec = PROVIDERS["cursor"]`。

## 不变量（**C1**、**C2**、**E2**）
- **prompt 走 STDIN，绝不走 argv。** Linux 对单个 argv 条目的上限是 128KiB，而证据包
  会超过它；作为参数传会**静默截断整场评审**。
- **这里的内置工具无法完全关闭**，所以治理是两层，且**两层都公开声明**：scoped 工具
  经桥**提供**（用到时即预防），**并且**每次会话都做运行后审计
  （`providers/audit.py`），裁决进 trace 并渲染进 RUN_REPORT。
  **控制类别被明说 —— 绝不留静默缺口。**
- 子进程环境是 `base.sanitized_env()` 的白名单：厂商 CLI 保住自己的订阅认证，
  但不得继承我们的模型端点或仓库凭据。

## 边界 —— 不属于这里
不含审计规则（那些住在 `providers/audit.py`）；不含评测专属策略 —— 评测臂那条额外的
"不得访问 PR 讨论"规则属于 ground-truth 泄漏问题，**刻意不放进产品路径**。

## 依赖（允许）
stdlib + `.base` + `.registry` + `..agent_loop.AgentOutcome` + `..llm` 的类型。

## 测试
`test_provider_cursor.py`。

## 重构备注
这套调用形状是由 Composer 评测臂（`eval/dataset/run_cursor_arm.py`）验证出来的；
**如果那个脚本和这个 transport 发生漂移，评测臂就不再是在测量产品了。**
