# engine/lifecycle.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~141 · 引擎底座（run 生命周期原语） · refactor-status: ok`

## 职责
executor 自己给不了的两条**进程级**保证：同一 run 的互斥锁，与 run 离开事件
循环时的 finalizer 挂钩点。

## 功能
`RunLock` 对 `<run_dir>/.lock` 取排他 advisory `flock`（第二个并发
`--resume` fail fast，而不是交错写进度、共享 checkout）；
`register_finalizer`/`finalize` 维护逐 run 的异步 finalizer 表；
`run_guarded` 包住 executor 协程，在完成/失败/抛异常的**每条**退出路径上、
同一事件循环内执行 finalize。

## 公开契约
`RunLock(run_dir).acquire()/release()`（context manager）；`RunLockHeld`；
`register_finalizer(run_dir, fn)`（`fn(outcome)`，outcome 是 RunOutcome，或
executor 在产出之前就抛时为 None）；`finalize(run_dir, outcome)`；
`run_guarded(run, run_dir) -> outcome`；`require_file_locking()` 与
`FileLockingUnavailable`（POSIX advisory 锁不可用时抛出的 fail-closed 门）。
调用方：`cli/copilot.py` 在 run/resume 全程持锁并用 `run_guarded` 包
`executor.run`；finalizer 注册者是 rebase 流水线（flock 释放、scratch 清理、
终局报告、CI abort 清理）与 `engine/worktrees.py` 的共享持有释放；
`require_file_locking` 由 `engine/worktrees.py::materialize` 和
`idempotency.py`（`key_lock`/`reap_stale`）消费。

## 不变量
- `flock` 争用按 open file description 计：同进程内对同一路径的第二次
  `acquire` 也失败 —— 抛 `RunLockHeld`，绝不静默共存。
- 锁文件释放后**留在原地**：它的存在不携带语义，只有 flock 本身算数。
- 非 POSIX（无 fcntl，与 `run_status.py` 同款守卫）：无 advisory 锁，
  `acquire` 直接成功 —— 注释声明的刻意降级（保住 run 可用；无 trace 事件）。
- **降级与 fail-closed 是两条刻意分开的路径**：`RunLock` 的静默降级只对
  "单进程 CLI run 可用性"成立；对**正确性就是锁本身**的路径（worktree
  materialize、idempotency 索引与 reaper），`require_file_locking()` 直接抛
  `FileLockingUnavailable` —— 宁可拒绝，也不在无保护下运行并谎报保证
  （不变量 7）。`contract.capabilities()` 会如实上报
  `supports_file_locking=False`。
- finalizer **恰好一次**：`finalize` 先 pop 再跑，第二次调用是 no-op；
  按注册顺序执行。
- 一个抛异常的 finalizer（**含 `CancelledError`** —— BaseException，不点名
  就会漏）绝不掩盖 run 自身的 outcome、绝不阻断兄弟 finalizer。
- `run_guarded` 的 teardown **不可被取消丢弃**：shield + 循环 re-await 直到
  finalize 真正完成，然后才让取消向外传播 —— 光 shield 会让外层先抛、
  loop 关闭时把孤儿 finalizer 拦腰取消。
- 什么都没注册时整个挂钩点是 no-op（现有非 rebase playbook 行为不变）。

## 边界 —— 不属于这里
不含 teardown 的内容本身（各注册方自带）；不做进度/checkpoint 持久化
（executor）；不是 run 状态查询（`run_status.py`）；不含 step 逻辑。

## 依赖（允许）
仅 stdlib（asyncio/os/pathlib/fcntl-守卫）。零 engine 内 import。

## 扩展点
新的 run 级资源清理 = 调用方去 `register_finalizer`，不改这里；只有新的
**进程级** run 保证才落在这里。

## 测试
`test_run_lifecycle.py`（同进程/跨进程锁争用、release 后可重取、无 fcntl
降级、finalizer 恰好一次 / 异常与取消隔离 / 失败路径也执行）。

## 重构备注
小而承重。`_finalizers` 是模块级进程状态 —— pop-before-run 就是它的自清
机制；若将来单进程要并行多 run，把表挂到 run 对象而不是模块全局。
`run_guarded` 的 shield 循环微妙（取消期间的 teardown 存活是评审加固过的）
—— 改动前先重跑取消路径的测试。
