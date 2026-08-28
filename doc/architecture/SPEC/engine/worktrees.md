# engine/worktrees.py —— 规范

<!-- verified-against: 2026-08-28 -->

`LOC ~231 · PR-time worktree：身份、物化、持有 · refactor-status: ok`

## 职责
PR 快照 worktree 的三条性质，每条都对应一个修掉的真实事故：
**身份**（旧键 `<repo>-pr<N>` 在不同 head 的 run 之间、同名目录的不同
checkout 之间碰撞，force-remove 曾删掉一个活评审的树）、
**验证**（复用前确认这棵树属于请求方仓库且 HEAD == sha）、
**存活**（run 期间的共享 flock 持有，让 reaper 的 `LOCK_EX|LOCK_NB`
扫描跳过它 —— 这是对 MCP 预约 run 和 CLI run 都成立的唯一存活信号，
`run_status.json` 只有前者才有）。

## 公开契约
`worktree_root()`；`canonical(path)`；`owner_tag(repo)`（checkout canonical
路径 sha256 前 8 位）；`dest_for(repo, pr, sha)` —— 键形如
`<name>-<owner8>-pr<N>-<sha12>`；`is_managed_dest(dest)`；`lock_path(dest)`；
`owned_by(repo, dest, sha, git)`；`materialize(repo, sha, dest, git,
timeout=300)`；`hold(dest, run_dir)`；`held_paths()`；`GitRunner` 类型别名
（git 以可调用注入 —— 本模块不含 subprocess 策略，可测）。

## 不变量
- **reaper 只删匹配 `_MANAGED_DEST`（`-hex8-prN-hex12` 后缀）的树**：
  worktrees 根是共享 scratch，长期存着其他工具的树 —— 一次"见什么删什么"
  的扫描曾经毁掉过别人的工作，这个守卫因此存在。
- `materialize` 对 git 级失败**绝不抛**（调用方决定 block 还是降级），
  但平台无文件锁**必须抛**（`lifecycle.require_file_locking` —— 序列化
  就是保证本身）。
- 物化锁 `LOCK_EX` **阻塞而非失败**：同 sha 两个 run 在
  `git worktree add` 里赛跑是常态，失败路径会静默降级回 live checkout ——
  恰是 head 门要防的"评错树"。
- 复用验证：`--git-common-dir` 必须解析回请求方仓库自己的 git dir **且**
  HEAD == sha；force-remove 只对外来/撕裂的树成立，绝不对同身份的活树。
- `hold()` 幂等（进程内 memo），经 `lifecycle.register_finalizer` 在每条
  退出路径释放，进程死亡时内核兜底 —— 崩掉的 run 绝不永久钉住一棵树。
- **持有挂在"使用"而不是"创建"上**（`engine/steps/_common.py::repo_path`
  里的 `_hold_if_worktree`）：`--resume` 重放 `state_updates` 并跳过已完成
  step 的函数体，挂在 `pr.fetch_diff` 体内的持有只在首轮存在。

## 边界 —— 不属于这里
无 subprocess 策略（git runner 注入）；无 run 生命周期逻辑（持有原语之外
—— 那是 `engine/lifecycle.py`）；何时物化/何时 block 是
`engine/steps/pr/fetch.py` 的决定。

## 依赖（允许）
stdlib（hashlib/os/re/time/pathlib）+ `.lifecycle`
（fcntl 守卫、register_finalizer、require_file_locking）。

## 测试
`test_pr_steps.py`（materialize 创建与复用、同 basename 仓库分键、
拒绝外来树、fetch_diff 端到端钉住）；`test_idempotency.py`
（reaper 只碰自己键出的树、放过被持有的树）。

## 重构备注
新模块（PR2）。键格式与 `_MANAGED_DEST` 必须同步演进 —— 改其一忘其二，
reaper 就会开始放过（或误删）新格式的树。
