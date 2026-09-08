# providers/codex.py —— 规范

<!-- verified-against: 2026-09-08 -->

`LOC ~197 · harness transport（ChatGPT 订阅） · refactor-status: ok`

## 职责
在 ChatGPT 订阅认证下，通过 `codex` CLI 跑完**一整个** agent step。

## 功能
`codex exec`，用 MCP override 指向工具桥，按事件流解析最终文本与用量，并以 OS 级只读
沙箱作为容纳控制。

## 公开契约
`CodexTransport`（`auth_gap`、`run_session`、`complete`）、`spec = PROVIDERS["codex"]`。

## 不变量（**C1**、**C2**）
- **控制手段是沙箱，不是工具列表。** Codex 无法关闭自己的原生 shell，所以容纳靠 OS 级的
  `--sandbox read-only`。因此沙箱内**较宽的读取是可能且被接受的**；沙箱保证的是
  **原生命令不能写出**。普通显式 writable scope 可用 workspace-write；
  rebase 的 bridge_managed_writes 保持 native read-only，受控 MCP 工具执行写入。
- 经桥的工具调用仍然过 `tools.dispatch`；沙箱是**纵深防御，不是替代**。
- `_tool_activity` 是尽力而为的活动日志，**明确不是审计** —— 强制点是沙箱。
  不要让调用方把它当审计用。
- `complete()` 在一个空的临时 cwd 里无工具运行，所以一次性调用**根本够不到仓库**。
- `auth_gap()` 区分未登录与 CLI 启动失败；登录状态不代表模型版本兼容。
- 仅对本次注入的 infermatrix-tools 服务设置工具审批 override；不改全局或其他服务。
- 保留有界 stderr、非零退出码和结构化错误；失败不能消费残留的成功文本。
- 真实小型 rebase fixture 已验证 actor → reviewer → MCP edit → pytest；
  这不代表任意目标仓库的完整 runtime/GPU 验收。

## 边界 —— 不属于这里
不发明沙箱策略（CLI 的 flag 就是契约）；不编造用量。

## 依赖（允许）
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` 的类型。

## 测试
`test_provider_codex.py`、`test_afd_codex_rebase.py`（离线回归）；
小型实网验证证据独立保存，不能外推为完整版本适配通过。

## 重构备注
**不要**把 `_tool_activity` "改进"成审计：`providers/audit.py` 的存在正是为了那些没有
OS 级控制可用的后端；把两者混同，会模糊掉"当前实际生效的是哪一类控制"——
而这正是 RUN_REPORT 要披露的事实。
