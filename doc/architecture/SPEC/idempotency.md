# idempotency.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~293 · 持久 idempotency 索引：每键一个 run、一次执行 · refactor-status: ok`

## 职责
三个分开解决的问题：(1) **每键一个 run** —— 持久的
`<run_root>/.idem/<key>.json` 条目 + 阻塞式逐键锁；(2) **每键一次执行**
—— `reserve` 报告自己是否*创建*了 run，只有创建才入队；(3) **崩溃安全**
—— 命中只有在其 run 存活或握有真实结局时才可复用，否则同锁之下重新武装
并重拉。

## 功能与范围
**刻意只服务 `start_strict_review`**：对通用 `start()` 按 spec 哈希取键
是主动有害的 —— `issue_answer`/`issue_filter` 携带 `pr=None` 且无 head，
一个仓库的所有 issue 任务会塌缩到同一个键上。

## 公开契约
`IdempotencyError`；`INDEX_DIR=".idem"`；`DEFAULT_RETENTION_DAYS=30`；
`KEY_RE` / `validate_key`；`spec_fingerprint(spec_dump)`（**整字典**
sha256 —— 之后新增的字段自动纳入，绝不把两个不同请求静默塌到一个键）；
`index_dir`；`key_lock(run_root, key, timeout=30)`（**阻塞**式上下文管理器
—— fail-fast 会把一次去重变成一个错误）；`read_entry`/`write_entry`
（tmp + `os.replace` 原子写）；`relaunchable(run_dir)`；
`resolvable(run_dir)`；`reap_stale(run_root, retention_days=30, ...) ->
{"entries","worktrees","refs"}`。

## 不变量
- `relaunchable`：`init_queued` 写 `child_pid: null`，子进程的 claim 才写
  pid —— `interrupted` 且 pid 为 null 意味着**没有子进程跑过**，可重拉；
  带 pid 的 `interrupted` 做过部分工作，是真实结局。
- **run 目录刻意不回收**：它们是用户可见的审计线索；删已完成的 run 是
  另一个、后果大得多的变更。`reap_stale` 只清索引条目、worktree、
  `refs/imx/<run_id>/*`。
- reaper 绝不触碰活 run 的条目（`state not in TERMINAL` → 跳过）。
- worktree 回收：存活以树**自己的**共享锁判定（绝不是注册表），移除走
  `git worktree remove`（绝不裸 `rmtree`），逐树限时（一棵慢树不拖垮
  整个扫描）。
- ref 回收只限 `refs/imx/<run_id>/*` 前缀 —— 扫描永远不可能解钉一个
  活 run 的 base/head。
- 无文件锁的平台 fail-closed（`lifecycle.require_file_locking`）。

## 边界 —— 不属于这里
不决定什么被取键（`mcp_server`/`cli/copilot` 的调用方决定）；不执行评审；
CAS 状态迁移住在 `run_status.py`（`claim_for_execution`/`reclaim_queued`）。

## 依赖（允许）
`run_status`、`engine.lifecycle`；`_reap_worktrees`/`_reap_refs` 内部
**惰性** import `engine.worktrees` 与 `engine.steps._common.git`
（保持模块可独立 import，不拖入整个 step 库）。

## 扩展点
新的可取键入口 → 先回答"这个 kind 的 spec 指纹在什么输入下会塌缩"，
答案不是"不会"就别接。

## 测试
`test_idempotency.py`（26 例：键字符集、终态前后同键去重、指纹覆盖全字段、
issue 任务不塌缩、并发预约恰好一次、写索引前崩溃、入队前崩溃后重拉、
claim 即 CAS、reclaim 守卫、reaper 三类各自的边界）；
`test_e2e_strict_mock.py`（idempotency-key 重试语义端到端）。

## 重构备注
新模块（PR2）。窄范围是它的安全性来源 —— 泛化到其他 kind 之前先把
"指纹塌缩"问题写成测试。
