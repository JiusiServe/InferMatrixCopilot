# run_status.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~247 · 持久化的单写者 run 生命周期记录 · refactor-status: ok`

## 职责
`run_status.json` —— 一次 Strict run 的**持久、无歧义**的生命周期记录，可跨进程观测。

## 功能
server 把每次 run 作为子进程拉起，且**只能通过文件系统**观测它，所以状态必须能挺过
server 重启，并且必须能把**崩掉的 run 和正在跑的 run 区分开**（靠"文件在不在"这类
启发式做不到）。

## 公开契约
`reserve_run`、`mark_child_started`、`read_status`，以及状态常量
（`queued`/`planning`/`running`/终态/`interrupted`/`FAILED`）。

## 不变量（**C3**、**E1**）
- **单写者。** `reserve_run`（server，在子进程存在之前）写下 `queued`；一旦拉起，
  **子进程就是运行期唯一的写者**：它的第一件事是通过 `mark_child_started` 写下自己的
  pid，然后 `planning → running → 终态`。父进程**只在 `.wait()` 之后**对账 ——
  也就是在子进程已确认死亡之后。
- **跨进程对账只发生在写者被确认死亡之后**，持 `flock` 进行，并保留 owner 字段。
- **按属主对账**（`owner_server_id` / `owner_server_pid` / `child_pid`）：只有**属主**
  server 被确认死亡，才可以把一个非终态 run 标记为 `interrupted`。在多 server 模型下
  （Claude Code 和 Codex 各自拉起一个 server），正是这一条阻止了某个 server 去抢另一个
  server 仍然活着的 `queued` run。
- **没有 run 会永远停在非终态**：对账发生在每次 `get_*` 时（惰性）、父进程 `wait()`
  之后、以及启动扫描时 —— **三处**。

## 边界 —— 不属于这里
不拉起进程（那是 `mcp_server`）；不含策略；不渲染报告。

## 依赖（允许）
仅 stdlib（`json`、`os`、`fcntl`/`flock`、`pathlib`）。

## 测试
`test_mcp.py`（单写者对账、属主判定）。

## 重构备注
这里的每一处改动，都必须**带着"两个 server + 一个已死子进程"的场景**去推演；
"精简掉 owner 字段" 会把跨 server 抢 run 的问题原样请回来。
