# mcp_server.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~421 · Strict 后台机器（start/poll） · refactor-status: ok`

## 职责
为 MCP 宿主运行 Strict 工作流：预约、拉起、跟踪、供给结果 ——
**且绝不阻塞一次同步工具调用**。

## 功能
评审要跑 5–12 分钟，任何同步 MCP 调用都会超时，所以接口是**start/poll 工具对**：
`start_review` / `start_issue_answer` / `start_issue_triage` 预约后**立即**返回
`run_id`；`get_result`（经 `next_offset` 分页，受 `mcp_report_max_bytes` 封顶）
和 `get_status`（`run_status` + `progress`）负责轮询。

## 公开契约
`CopilotMCP`、`build_mcp()`，以及那组 start/poll 工具。

## 不变量（**C2**、**C3**、**E1**）
- **安全是结构性的，不是"信任宿主"。** `enforce_mcp_policy` 在这里跑一次，
  **并且**在子进程里（权威地）再跑一次，因此只有 `READ_ONLY_KINDS` 会被执行、
  `post` 恒为 `False`、只有 allowlist 内的仓库可达 —— **无论被篡改的
  `request.json` 声称什么**。
- **每次 run 都是一个隔离子进程**
  （`python -m infermatrix_copilot --execute-reserved <id>`）。两个理由都很关键：
  copilot 的 stdout 必须离开本进程的 JSON-RPC stdio 通道（子进程 stdout →
  `<run_dir>/console.log`），且进程级全局 tracer / `last_run_dir` **由此天然按 run 隔离**。
- **run 由单个 worker 线程串行执行。** worker 等待子进程后把退出码交给对账：
  退出码 3 且无终态即 lock-loser 签名（真正 BLOCKED 的子进程会先写终态再退出），
  以 `suspect_lock_loser` 传入 `reconcile_after_wait`。
- 跨重启、跨多个并发 server 的轮询正确性，来自 `run_status.py` 的持久记录 + 按属主
  对账，**而不是内存状态**。
- **`mcp` SDK 是可选 import**，藏在 `[mcp]` extra 之后，且**绝不能**被核心包 import
  —— 纯 CLI 安装保持零依赖。
- `build_mcp()` 暴露 V1 工具面（autonomous 工作流执行器）；它**默认不注册**。

## 边界 —— 不属于这里
不含 Direct 模式逻辑（`thin_mcp_server.py`）；不定义策略（`mcp_policy.py`）；
不定义状态文件格式（`run_status.py`）。

## 依赖（允许）
stdlib + `mcp`（可选 extra）+ `.mcp_policy` + `.run_status` + `.cli`。

## 测试
`test_mcp.py`（篡改防御、单写者对账、分页、只读工具集）。

## 重构备注
预约形状（先建 run 目录，再规划）是 **MCP 专属**的；CLI 主路径仍然在**建目录之前**
过门，所以被放弃的计划不会留下目录。**不要在没有保住这个差别的前提下把两者统一。**
