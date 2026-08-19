# tool_bridge.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~308 · 面向 harness 会话的 scoped 工具 MCP server · refactor-status: ok`

## 职责
以 stdio MCP server 的形式，把本次 run 的 scoped 工具暴露给 harness 会话 ——
好让"把一个 step 委托给厂商 agent"**不等于把权限闸也一并委托出去**。

## 功能
`python -m infermatrix_copilot.tool_bridge --spec <bridge_spec.json>` ——
一个由 harness 从它的 MCP 配置里拉起的 server。它提供本次 run 的内置工具、
`doc_search`/`doc_read`、按需的 `repo_map`，以及只读的变更考古工具组
（`diff_stat`、`file_at_base`、`show_commit`、`search_history`、`calc`）。

## 公开契约
`write_bridge_spec(...)`、`load_bridge_spec(path)`、`make_dispatcher(...)`、
`build_server(spec_path)`、`main(argv)`。

## 不变量（**C1**、**C2**、**E2**）
- **每一次内置工具调用都经过 `tools.dispatch`**，带着该 step 反序列化出来的
  `ToolScope`，因此拒绝行为、相对路径对 PR-time worktree 的解析、以及结果上限，
  都与进程内循环**表现一致**。
- **读取受容纳约束 —— 比进程内还严。** `ToolScope` 只对**写**做路径守卫；而 harness
  是持有不可信 PR diff 的**低信任调用方**，所以桥会拒绝容纳根（scope 根 + run 目录）
  之外的 read/list/grep 目标。**这就是防 `.env` 外泄的那道守卫。**
- **独立的 trace 文件。** 工具事件追加到 spec 旁边的 `bridge_trace.jsonl`；
  第二个进程**绝不能**与父进程的 `run_trace.jsonl` 交错。
- **`repo_map` 失败只降级，绝不崩溃** —— 记一条 `capability_gap`（`bridge.repo_map`）。
- **skill/memory 检索刻意不桥接。** 那两个工具会提出知识 candidate；
  开一条跨进程写入路径的方案**已被否决**。harness 会话可以**读**本仓库的知识，
  **永远不能往里加**。

## 边界 —— 不属于这里
不调用 transport（那归各 `providers/<id>.py`）；不构造 scope（那归 step）；
**永不写知识**。

## 依赖（允许）
stdlib + `mcp`（`[mcp]` extra）+ `..tools` + `..scopes` + `..run_trace` +
knowledge/repo-map 工厂。

## 测试
`test_tool_bridge.py`。

## 重构备注
**并非每个后端都够得到这个 server**：`providers/deepseek.py` 跑在 harness 原生 bash 上，
因为它捆绑的运行时不带 MCP client，拿到无法履约的 spec 时会记一条 `capability_gap`。
任何"这次 run 走了工具桥"的说法，都必须**对照那个标志核实**，
而不是从"后端是 harness"推定。
