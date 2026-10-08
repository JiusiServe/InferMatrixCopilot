# providers/cursor.py —— 规范

<!-- verified-against: 2026-10-08 -->

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
`test_provider_cursor.py`；共享 checkout 串行见 `test_run_service_concurrency.py`。

## 重构备注
这套调用形状是由 Composer 评测臂（`eval/dataset/run_cursor_arm.py`）验证出来的；
**如果那个脚本和这个 transport 发生漂移，评测臂就不再是在测量产品了。**

## 作为 rebase module-agent 后端（2026-09-19）

`REBASE_BACKEND=cursor` 时，cursor-agent 承担 rebase module agent。
registry 给 cursor 的能力是 `{mcp_tools, usage_reporting}`——**没有**
`builtin_tools_off`，所以 cursor 自带工具会绕过 bridge：bridged 调用受
scope 约束，native 调用只被**记录**。

## 2026-09-28
`complete()` 接受并忽略 `effort`（与 base 契约一致）。

## 2026-09-30
`complete()` 接受并忽略 `max_budget_usd`；`stops_at_spend` 为 False（CLI 无花费阈值）。

### 共享 checkout 上的会话串行（2026-09-30）
桥配置写在会话 cwd 的**固定路径** `.cursor/mcp.json`，同一目录里两个不同 run 的会话
会互相覆盖配置，令一方的 agent 绑定到另一个 run 的工具 scope 与 trace。
带桥的会话若 cwd 是**共享 checkout**（`.git` 为目录的 clone，或未托管的 linked
worktree），就在该 checkout 的 git dir 里 `imx-cursor-session.lock` 上持
`flock LOCK_EX` 直到会话结束并清理配置，跨线程/进程/服务串行——issue 任务与
worktree 物化失败而降级到 live checkout 的 PR run 都在这里。托管的 PR-time
worktree（repo+PR+sha 分键，run queue 不会让同 PR 的两个 run 并发）与 run 自己的
目录不加锁。等待上限为会话超时 + 60 s；超时则返回空文本、`truncated`、refusal，
并记 `capability_gap`（`cursor.exclusive_cwd`），绝不在别人的配置下静默开跑。

## 2026-10-08 共享机制
缓冲执行、保留超时部分 stdout 与 JSONL 解码复用 `base.run_cli/json_events`，MCP stdio 入口复用 `base.bridge_server`。
`SessionUsage.outcome/reply` 统一结果封装；无工具调用通过 `TemporaryDirectory` 管理空 cwd，清理错误仍可忽略。
会话目录串行、桥配置所有权、环境白名单及事后审计继续由本 transport 控制。

`complete()` 使用显式无工具 profile：`--mode ask --trust --workspace <空临时目录>`，
不传 `--force` 或 `--approve-mcps`。解析后用 `audit.assert_tool_less` 拒绝工具活动、
未知内容块和错误结果；普通带桥 `run_session` 的权限与事后容纳审计保持原契约。
只读仓库 JSON 会话由 `json_session.run_readonly_json` 承载，不能用本空 cwd profile
替代其源码读取与会话恢复协议。
