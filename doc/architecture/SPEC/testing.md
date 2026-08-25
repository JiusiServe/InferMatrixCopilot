# testing/ —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~1760（6 个文件） · 测试执行底座（rebase agent shell 测试层的 Python 移植） · refactor-status: ok`

## 职责
仓库中立的测试执行底座：gpu_lock.sh / kill_test_tree.sh / test_watchdog.sh /
test_runner.sh 的 Python 移植。仓库专属数据（watchdog 模式、artifact glob、
测试 manifest）全部住在 adapter 侧，本包只**接收**它们作为输入。

## 功能（一行一模块）
- `env_plan.py` —— 子进程环境构造：inherit-plus-overlay（`build_subprocess_env`）
  + agent-shell 的**allowlist 式**凭据洗刷（`scrub_agent_shell_env`）。
- `gpu_lock.py` —— 跨进程 GPU 互斥（磁盘协议与 shell 字节兼容）+ nvidia-smi
  孤儿清理 + VRAM 空闲等待。
- `process_tree.py` —— 进程树终结：BFS 收集后代、自身祖先排除、
  TERM → 宽限 → KILL、(pid, starttime) 身份校验防 PID 复用。
- `runner.py` —— 单测试执行器：GPU 锁、watchdog、分层超时、silent-exit 尸检
  footer、cov-strip 回退、pass marker、artifact 清理、后代快照线程。
- `watchdog.py` —— 双档日志看门狗：Tier 1 灾难模式即杀；Tier 2 去噪后交
  廉价 reviewer 裁决（KILL/CONTINUE）。
- `watchdog_learn.py` —— Tier-2 裁决的记录/收割/晋升：一贯良性的模式
  自动晋升进噪声 overlay YAML（数据，而非 shell 时代的改代码）。

## 公开契约
- `env_plan`：`build_subprocess_env(...)`、`scrub_agent_shell_env(env, keep_hf_token, extra_safe_prefixes)`，
  以及 `AGENT_SHELL_SAFE_EXACT` / `AGENT_SHELL_SAFE_PREFIXES` / `AGENT_SHELL_CRED_SUFFIXES` 常量。
- `gpu_lock`：`GpuLock`（context manager）、`GpuLockTimeout`、`visible_devices`、
  `cleanup_orphan_gpu_procs`、`wait_gpu_memory_idle`。
- `process_tree`：`collect_descendants`、`kill_tree(pids, identity=...)`、`kill_by_pattern`。
- `runner`：`TestRunner.run(job, env, baseline, dry_run) -> TestOutcome`、
  `TestJob`、`RunPlan`、`TestOutcome`、`strip_cov_flags`、`cleanup_test_artifacts`、
  `log_file_for`/`pass_marker_for`、`TIMEOUT_RC=124`、`PY_TIMEOUT_MARGIN_SEC`。
- `watchdog`：`WatchdogPatterns(.from_yaml)`、`LogWatchdog(.start/.stop/.check_once/.result)`、`WatchdogResult`。
- `watchdog_learn`：`record`、`harvest`、`eligible_patterns`、`promote`、
  `read_decisions`、`normalize_pattern`、`repair_tail`。

## 不变量
- **E2** —— 硬件门槛产生**显式的 `skipped` 结果**，绝不是 shell 时代那种
  虚增通过数的静默 rc=0；skip 前先撕掉旧 pass marker。
- 超时分层：**primary** 定时器在 `timeout_sec` 杀整个进程组 + 逐 pid 后代；
  **safety** 在 `+PY_TIMEOUT_MARGIN_SEC` **严格更晚** SIGKILL。fired 的定时器
  被 join 后才返回 —— 下一个 job 不会在后代仍占 GPU 时启动。
- PID 复用安全：快照 map **只增不减**，身份绑定在**发现时**的 (pid, starttime)，
  且记录只接受**已验证祖先链**上的 pid；`kill_tree` 丢弃 starttime 不再匹配的
  pid —— 升级 SIGKILL 绝不打中无关进程。
- GPU 锁绝不 unlink 活主的锁：偷锁在 flock side file 的临界区内**重新判定**
  staleness；release 只删除仍属于自己的锁文件。
- **E2** —— Tier-2 无 reviewer / reviewer 异常 / 无法解析的回复一律 CONTINUE，
  **绝不 wedge 一次 run**；Tier 1 不经评审即杀。
- **E1（精神）** —— 每次 Tier-2 裁决落 decision log（`record_fn`/`result.decisions`），
  kill **先于**遥测执行 —— 满盘的日志绝不留下一个坏引擎继续跑。
- watchdog 的每次扫描以 `start_offset` 限定在**本次尝试自己的字节**内 ——
  setup 输出或上次尝试的报错杀不掉一次通过的主运行。
- **D4** —— 学习只做加法：overlay 只 append `noise`（可静音、**绝不锐化**）；
  `harvest` 以 state log 自身为去重权威，flock + 撕尾修复 + fsync，exactly-once。
- 凭据洗刷是 allowlist、fail-closed：未知名字直接丢弃，凭据后缀一票否决，
  HF token 仅显式 opt-in 重进；纯函数，**绝不改写自身进程环境**。
- artifact 清理只在 repo 根的**深度 1**，含路径分隔符/`..`/`**` 的 pattern 被拒。

## 边界 —— 不属于这里
watchdog 模式、artifact glob、manifest（adapter 数据）；测试循环/重试编排
（`rebase_engine/module_pytest.py`）；远程执行（随 shell 层退役）；不含 LLM
（reviewer 是注入的 callable）。

## 依赖（允许）
stdlib（`fcntl` 带 POSIX 守卫）；`pyyaml`（patterns/overlay）；包内互引
（runner → gpu_lock/watchdog/process_tree）；`watchdog_learn` →
`memory/skills._fsync_dir`（overlay 落盘持久化）。**绝不** import `engine/`。

## 扩展点
新的 watchdog 模式/噪声 → adapter 的 seed YAML 或 learned overlay；额外安全
env 前缀 → `scrub_agent_shell_env(extra_safe_prefixes=…)`（manifest 数据），
绝不放宽默认表；runner 的协作者（`review_fn`/`record_fn`/`available_gpus`…）
全部可注入。

## 测试
`test_testing_substrate.py`（77 个，覆盖全部六模块）、`test_shell_golden.py`
（TestRunner 对 shell 的 command-echo 金样）；`watchdog_learn` 另由
`test_curator.py`（harvest exactly-once）与 `test_knowledge_foundation.py`
（record 身份字段、撕尾修复）钉住。

## 重构备注
`runner.py`（643L）是包内最重的一块：`_spawn` 把快照线程、双定时器、watchdog
接线挤在一个方法里，密度高但每行都背着一条已记录的竞态教训 —— 拆分前先读
注释里的事故史。身份校验逻辑分居 `_record_walk`（记录侧）与 `kill_tree`
（消费侧），契约靠注释维系；若再演化，考虑一个共享的 identity 小模块。
