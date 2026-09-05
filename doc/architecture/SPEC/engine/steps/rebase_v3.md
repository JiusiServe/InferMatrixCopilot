# engine/steps/rebase_v3.py —— 规范

<!-- verified-against: 2026-09-06 -->

`LOC ~2204 · step 库（v3 rebase 装配层） · refactor-status: oversized`

## 职责
把 `rebase_engine` 包接进 executor：locked playbook `repo-rebase-v3` 的全部
step —— 薄的受治理 wrapper，substate-first、类型化失败、发布被消费的键。

## Steps（12 个）
| step | kind/risk | 发布（`state_updates`）/ 裁决 |
|---|---|---|
| `rebase.v3_prelude` | deterministic/read | `mode_*` 标志、`run_id`、`upstream_origin_path`、`last_rebase_upstream_commit`、(remote_ci) `upstream_commit`、(full) `upstream_path`；注册终局报告 finalizer；知识开账 attest |
| `rebase.v3_guard` | deterministic/write_workspace | 无发布 —— 幂等重取 checkout flock（首取在 prelude），再注入 adapter `rebase.guard` 策略委托 `workspace._guard_clean_rebase` |
| `rebase.v3_scan` | deterministic/read | `manifest_jobs`；`test_manifest.json` 产物 |
| `rebase.v3_wheel` | deterministic/write_workspace | `upstream_commit`（选 commit → 装进目标 venv → **最后**才 pin Dockerfile：装失败绝不留脏树） |
| `rebase.v3_assign` | deterministic/read | `active_modules`、`wave1_modules`、`wave2_modules`（path-sync 后按 wave 分派） |
| `rebase.v3_wave_gate` | deterministic/read | wave-1 失败 ⇒ `wave2_modules=[]`；`halt_on_module_failure` ⇒ ESCALATE |
| `rebase.v3_module_rebase` | script/write_workspace | `module_<name>_status`（foreach；同 run 串行锁 —— 同一 checkout；substate done/skipped 短路防重入二次执行） |
| `rebase.v3_test_loop` | script/write_workspace | `phase3_failed`；substate `tests.pipeline`/`infra_failures`；空 manifest ⇒ `manifest_empty` |
| `rebase.v3_precommit` | script/write_workspace | 无发布 —— substate `tests.precommit`（passed/failed/failed_preexisting/not_declared） |
| `rebase.v3_push_gate` | deterministic/read | `push_gate_flagged`、`push_gate_overrides`；不许 ⇒ FORBIDDEN；override 记 trace |
| `rebase.v3_ci` | script/push | `ci_result`、`ci_build_urls`；substate `ci`（rounds/adopted/unfixed，以及逐 job 分类证据） |
| `rebase.v3_finalize` | deterministic/read | 无发布 —— substate `phase=done|needs_human`；有失败 ⇒ BLOCKED（复用 exit 3） |

## 公开契约（注册的 step 之外）
`_adapter_manifest/_substate/_task_params`（被 `rebase_knowledge` import）、
`manifest_job_to_test_job`（golden 测试）、`_build_backends`（read-compat
测试）、`_make_ci_client`（模块级工厂，测试注入 fake 客户端）。

## 不变量
- **A4**：12 个 step 全部 `@step(...)` 就地自注册；`when:` 门**只**读
  prelude 发布的 `mode_*` 标志（**B3** 已知键，复合标志预算于
  `rebase_engine/modes`）。**B2**：被消费的键都经 `state_updates` 发布
  （上表），substate 同时落盘 —— 两份都写。
- **substate 裁决**：模块/测试/CI 失败是 substate **数据**，携带它们的 step
  返回 ok —— 终局裁决属于 `v3_finalize`（全 ok + substate 有失败 ⇒ BLOCKED
  needs-human），且它在 report 之后运行，RUN_REPORT 必已存在（**B1**）。
- **B1**：结构性拒绝全程类型化 —— mode 缺失/未知、adapter 非 active、声明的
  venv 展不开、无 CI token/provider/签名身份 → BLOCKED；绝不猜权限。
- **C4**（`v3_ci`）：只许推 adapter 声明的 `push.rebase_branch`（且
  `rebase_branch_allowed`，绝非受保护分支）；`ALLOW_PUSH` 未设 ⇒
  push_dry_run ⇒ **FORBIDDEN**；推送走 `push_to_ci` WAL，op id 对 CI 台账与
  push WAL **双清点**后起编（resume 绝不复用已指名的 op id）。
- 预推送采纳豁免必须**被证明**：remote ref 已等于本地 HEAD 才把 head 传给
  `ci_loop.run_ci_rounds`（同头 schedule 构建可采纳）；ls-remote 失败或
  不一致即禁用豁免（安全默认）。
- **checkout flock 先于任何 mutator**：prelude 取锁，每个 mutating step 经
  `_ensure_checkout_locks` 幂等重取（resume 重放 prelude 不执行它）；释放是
  lifecycle finalizer，每条退出路径都放。可变操作只碰 run_dir 内的
  `git clone --shared` **scratch** upstream；canonical 路径绝不被采纳为可变
  树；resume 采纳幸存 scratch 时重新注册 teardown。
- **C3**（`_module_scope`）：repo 树 + run dir 是硬可写墙；模块
  `local_paths` + `plans/` 是 primary；未知模块得到永不匹配的 primary ——
  它的每次仓库写都被记录 out-of-scope，而非静默在圈内。
- **E1/E2**：能力缺失记 `capability_gap` 并声明式降级（无 tier key/CI
  token/客户端、debug backend 缺失 ⇒ 回归记为结构性失败），绝不静默跳过。
- debug 尝试**快照护栏**：snapshot → agent → 内容 digest 变更检查（staged+
  unstaged+untracked 字节+mode+symlink）→ 复跑/本地验证；被拒或验证失败的
  尝试**回滚** —— 只有绿色复跑算修好。
- 空/损坏 manifest ⇒ `manifest_empty`（push gate 阻塞，绝不空洞通过）；
  不可运行的命令归 STRUCTURAL —— 绝不借 bash rc=0 假通过。
- **A5**：一切仓库知识来自 adapter manifest；parity 词汇泄漏上限 14，
  只能变小（`test_repo_vocabulary.py`）。

## 边界 —— 不属于这里
不含 rebase 机制本体（`rebase_engine/{module_rebase,test_loop,ci_loop,
push_to_ci,wheel,push_gate,assign,…}`）；不含 provider HTTP（`ci/buildkite`）；
知识尾段在 `rebase_knowledge`；finalizer 机制在 `engine/lifecycle`。

## 依赖（允许）
`rebase_engine/*`、`engine/{step,lifecycle}`、`._common`、`scopes`、
`ci/buildkite`（经 `_make_ci_client`）、`adapters/base`、`memory/*`、
`testing/*`、`config`、anthropic SDK；另有对 `.workspace` 的 guard 委托
import（见重构备注）。

## 测试
`test_assembly.py`（mode 治理、push-gate、report_only e2e、终局行、同头采纳）、
`test_v3_complete_e2e.py`（local_ci/full/remote_ci 全程）、`test_ci_wiring.py`
（`v3_ci` 接线）、`test_shell_golden.py`、`test_knowledge_readcompat.py`、
`test_repo_vocabulary.py`（泄漏上限）。

## 重构备注
2204 行 —— 全库最大的 step 文件；知识尾段已拆出（`rebase_knowledge`），下一
刀的自然缝：① env/backends 构建（~83–465 行）；② 锁与 scratch 生命周期
（~496–635 行）；③ `v3_ci` 及其 helper（~1753–2204 行）。被
`rebase_knowledge` import 的三个 helper 应下沉 `._common`，一并消掉那条 A2
违例；对 `.workspace._guard_clean_rebase` 的直接 import 是另一条。拆分时
substate + `state_updates` 双写、模块短路/串行锁的 crash-window 契约**必须**
原样保留（resume 完整性测试护住）。
