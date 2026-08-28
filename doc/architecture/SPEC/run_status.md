# run_status.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~309 · 持久化的单写者 run 生命周期记录 · refactor-status: ok`

## 职责
`run_status.json` —— 一次 Strict run 的**持久、无歧义**的生命周期记录，可跨进程观测。

## 功能
server 把每次 run 作为子进程拉起，且**只能通过文件系统**观测它，所以状态必须能挺过
server 重启，并且必须能把**崩掉的 run 和正在跑的 run 区分开**（靠"文件在不在"这类
启发式做不到）。

## 公开契约
`init_queued`（server 预约时写 `queued` + 属主字段 + `child_pid: null`）、
`claim_for_execution(run_dir, child_pid)`（**预约 run 子进程的第一步**：
原子 CAS `queued → planning`，同 pid 幂等，输者不得执行）、
`mark_child_started`（**非预约** run 记录自身 pid 的路径）、`mark`、
`read_status`、`reclaim_queued(run_dir, owner_server_id,
owner_server_pid)`（`interrupted → queued` 重新武装）、
`reconcile_after_wait`/`reconcile_if_dead`/`startup_reconcile`、
`register_server`/`unregister_server`/`server_alive`，以及状态常量
（`QUEUED`/`PLANNING`/`RUNNING`/`TERMINAL`/`INTERRUPTED`/`FAILED`）。

## 不变量（**C3**、**E1**）
- **单写者。** `init_queued`（server，在子进程存在之前）写下 `queued`；一旦拉起，
  **子进程就是运行期唯一的写者**：预约 run 的子进程第一件事是
  `claim_for_execution` 赢下 CAS 并写入自己的 pid（非预约 run 走
  `mark_child_started`），然后 `planning → running → 终态`。父进程
  **只在 `.wait()` 之后**对账 —— 也就是在子进程已确认死亡之后。
- **跨进程对账只发生在写者被确认死亡之后**，持 `flock` 进行，并保留 owner 字段。
- **按属主对账**（`owner_server_id` / `owner_server_pid` / `child_pid`）：只有**属主**
  server 被确认死亡，才可以把一个非终态 run 标记为 `interrupted`。在多 server 模型下
  （Claude Code 和 Codex 各自拉起一个 server），正是这一条阻止了某个 server 去抢另一个
  server 仍然活着的 `queued` run。
- **没有 run 会永远停在非终态**：对账发生在每次 `get_*` 时（惰性）、父进程 `wait()`
  之后、以及启动扫描时 —— **三处**。
- **at-most-once 执行是状态 CAS，不是锁**（与"单写者"相关但独立的保证）：
  server 拉起子进程 A 后死亡、重试合法地重占预约并入队子进程 B 时，谁持锁
  都拦不住 A 醒来后把 `done` 走回 `planning` 再评审一次 —— 只有"持有者到场
  时 run 处在什么状态"能拦住。`claim_for_execution` 因此是原子
  compare-and-set：输掉 claim 的子进程不规划、不执行、不写状态，直接退出。
- **`interrupted → queued` 是对"终态不再迁移"的一个刻意的、狭窄的例外**：
  仅当 `interrupted` 且 `child_pid` 为 null（属主 server 在任何子进程启动前
  就死了，预约从未执行过 —— 不是真正的终局结果）时，`reclaim_queued` 才
  允许同一属主身份重新武装；带 pid 的 `interrupted` 做过部分工作，是真结果，
  拒绝重占。

## 边界 —— 不属于这里
不拉起进程（那是 `mcp_server`）；不含策略；不渲染报告。

## 依赖（允许）
仅 stdlib（`json`、`os`、`fcntl`/`flock`、`pathlib`）。

## 测试
`test_mcp.py`（单写者对账、属主判定）；`test_idempotency.py`
（claim 是 CAS 而非写入、终态不可再 claim、reclaim 的双重拒绝、
输掉 claim 的子进程 no-op 退出）。

## 重构备注
这里的每一处改动，都必须**带着"两个 server + 一个已死子进程"的场景**去推演；
"精简掉 owner 字段" 会把跨 server 抢 run 的问题原样请回来。
