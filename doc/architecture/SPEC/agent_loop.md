# agent_loop.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~126 · 引擎（工具循环） · refactor-status: ok`

## 职责
最小的工具使用循环，受 ToolScope 约束、被 RunTrace 审计。

## 功能
`run_agent` 反复执行：调 LLM → 收集 tool_uses → 逐个过 `tools.dispatch` →
把结果喂回去；预算耗尽时，**强制一次不带工具的最终答复**。

## 公开契约
`run_agent(llm, *, system, prompt, scope, trace?, model?, max_iters,
extra_tools?) -> AgentOutcome`；`AgentOutcome`。

## 不变量
- 循环**只**看得见它的 scope 允许的工具（经 `tool_definitions_for`）。
- 每次调用都过 `tools.dispatch`（**C3**）。
- 预算耗尽会**强制一次最终答复**，而不是丢弃这场调查。
- **"FINAL ROUND" 收尾提示必须追加在 tool_result 块之后。**
  把它放在 `tool_use` 与其 `tool_result` 之间，会违反邻接契约并让整个请求以 400 失败。
  由 `test_agent_loop.py::test_final_round_nudge_follows_tool_results` 钉住。
- 这个循环**只**为 `api` 后端运行；harness 后端拥有自己的循环，
  被委托的是一整个 step（`providers/base.md`）。

## 边界 —— 不属于这里
不含规划/step 语义；不做输出契约收敛（那是 `agent_runtime`）；
除透传外不构造 prompt。

## 依赖（允许）
`llm`、`run_trace`、`scopes`、`tools`。

## 扩展点
预期没有 —— 它是 `agent_runtime` 赖以构建的原始底座。

## 测试
`test_agent_loop.py`。

## 重构备注
**恰到好处地小。** 保持它与 prompt 无关、与契约无关 —— 所有治理/结构都属于上一层的
`agent_runtime`。如果 `agent_runtime` 发生拆分，本文件保持原样（它已经就是"循环"层）。
