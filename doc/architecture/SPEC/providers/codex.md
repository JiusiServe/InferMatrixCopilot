# providers/codex.py —— 规范

<!-- verified-against: 2026-08-18 -->

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
  **什么都写不出去**。
- 经桥的工具调用仍然过 `tools.dispatch`；沙箱是**纵深防御，不是替代**。
- `_tool_activity` 是尽力而为的活动日志，**明确不是审计** —— 强制点是沙箱。
  不要让调用方把它当审计用。
- `complete()` 在一个空的临时 cwd 里无工具运行，所以一次性调用**根本够不到仓库**。
- `auth_gap()` 会报出 ChatGPT 登录缺口：这个后端**仅经离线测试**（开发机没有登录），
  readiness 必须如实说出来，而不是暗示它已被验证。

## 边界 —— 不属于这里
不发明沙箱策略（CLI 的 flag 就是契约）；不编造用量。

## 依赖（允许）
stdlib + `.base` + `..agent_loop.AgentOutcome` + `..llm` 的类型。

## 测试
`test_provider_codex.py`（离线；实网路径**按设计未经验证** —— 见
`doc/features/provider-registry.md` 里的状态说明）。

## 重构备注
**不要**把 `_tool_activity` "改进"成审计：`providers/audit.py` 的存在正是为了那些没有
OS 级控制可用的后端；把两者混同，会模糊掉"当前实际生效的是哪一类控制"——
而这正是 RUN_REPORT 要披露的事实。
