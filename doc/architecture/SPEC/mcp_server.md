# mcp_server.py —— 规范

<!-- verified-against: 2026-08-31 -->

`LOC ~506 · Strict 后台机器（reserve/start/poll） · refactor-status: ok`

## 职责
为 MCP 宿主运行 Strict 工作流：预约、拉起、跟踪、供给结果 ——
**且绝不阻塞一次同步工具调用**。

## 功能
评审要跑 5–12 分钟，任何同步 MCP 调用都会超时，所以接口是**start/poll 工具对**：
`start_review` / `start_issue_answer` / `start_issue_triage` 预约后**立即**返回
`run_id`；`get_result`（经 `next_offset` 分页，受 `mcp_report_max_bytes` 封顶）
和 `get_status`（`run_status` + `progress`）负责轮询。

## 公开契约
`CopilotMCP`、`build_mcp()`、那组 start/poll 工具，外加
`get_capabilities()`（包 `contract.capabilities`，含
`MAX_STRICT_WORKERS=1` 与文件锁能力上报）。`start_review` 接受
`expected_head_sha`；`start_strict_review` 接受 `idempotency_key` 并把
`(run_id, created)` 语义（见下）落到入队决定上。新增内部
`reserve_strict_review` 原样返回该 tuple，供 typed SDK 准确报告幂等复用；
`start_strict_review` 继续只返 `run_id`，保持 MCP/既有调用兼容。

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
- **子进程环境闸恒关**：`_launch` 对**每个**子进程（含 Strict）无条件写
  `ALLOW_POST="0"` —— 给策略的"拒绝而非恢复"（`mcp_policy.md`）系上第二道
  背带；同时转发 `MCP_ALLOWED_REPO_ROOTS`，让子进程的
  `authorize_repo_path` 复检对着父进程判过的同一组根。
- **入队只发生在 `created` 为真时**：`reserve_run` 现在返回
  `(run_id, created)` —— 重试命中既有键只返回既有 run，绝不第二次入队
  （配合 `run_status.claim_for_execution` 的 CAS，双保险关掉重复执行）。
- **`configure_strict_repo` 已删除**（进程全局 `settings.repo_paths` 突变）：
  替代是 `strict_readiness(repo, repo_path="")` 按调用校验 —— 两个并发
  Strict 请求各带各的 checkout，再无共享状态可互踩。
- **回收是尽力而为、绝不拦路**：启动时与每次 run 终局后跑
  `idempotency.reap_stale`；一次清不完的扫描绝不阻止 server 服务或 run
  完成。
- **轮询对未知 id 给结构化答案**：`get_result` 对形状合法但不存在的
  run_id 返回 `contract.unknown_run_result`（`state: unknown`）而不是抛错
  —— 丢响应和还在跑可区分；终局响应同时附带
  `contract.build_review_result` 的结构化 `result`（分页 `report` 保留）。

## 边界 —— 不属于这里
不含 Direct 模式逻辑（`thin_mcp_server.py`）；不定义策略（`mcp_policy.py`）；
不定义状态文件格式（`run_status.py`）。

## 依赖（允许）
stdlib + `mcp`（可选 extra）+ `.mcp_policy` + `.run_status` + `.cli`
+ `.contract` + `.idempotency`。

## 测试
`test_mcp.py`（篡改防御、单写者对账、分页、只读工具集、快照绑定转发、
子进程 post 闸恒关、未知 run_id 不抛、结构化 result 附带）；
`test_contract.py`（capabilities 上报、configure_strict_repo 已亡）；
`test_e2e_strict_mock.py`（离线端到端：钉 head 评审、idempotency 重试、
第二个子进程 no-op、post 拒绝）。

## 重构备注
预约形状（先建 run 目录，再规划）是 **MCP 专属**的；CLI 主路径仍然在**建目录之前**
过门，所以被放弃的计划不会留下目录。**不要在没有保住这个差别的前提下把两者统一。**
