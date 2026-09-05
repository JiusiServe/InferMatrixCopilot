# rebase_engine/ —— 规范

<!-- verified-against: 2026-09-06 -->

`LOC ~7500（26 个模块） · repo-rebase-v3 的原生 rebase 引擎 · refactor-status: ok`

## 职责
父级 rebase agent 机制的仓库中立移植（PR0..PR7 分片落地）：repo-rebase-v3
的全部**引擎原语**。仓库专属内容一律作为数据来自 `adapters/<repo>/`；
把原语接成 step 的装配在 `engine/steps/rebase_v3`（+`rebase_knowledge`），不在这里。

## 功能
四个阶段的原语 + 底座（phase-1 分析 → phase-2 模块 agent → phase-3 本地
测试环 → phase-4 push+CI；substate/runtime/锁/WAL）。逐模块图：

| 模块 | 独占的那件事 |
|---|---|
| `__init__.py` | 包 docstring（仓库中立宣言）；无逻辑 |
| `agent_loop.py` | rebase agent 循环（流式、`.decision.md` 计划闸、150 轮预算，cache-parity） |
| `assign.py` | commit→模块 确定性归类 + 路径漂移检查 + 报告渲染 |
| `ci_loop.py` | CI 构建生命周期：受守卫的创建/恢复、monitor、日志分类器、round 编排 |
| `debug_patch_policy.py` | 自动 CI debug 补丁策略：禁止 oracle 弱化，未本地验证时禁止 test 编辑 |
| `gitio.py` | git 机械层：暂存纪律、签名提交重试、token 头传输、执行已授权 decision |
| `hooks.py` | `RebaseHooks` —— adapter 可定制的窄行为面，fail-closed 加载 |
| `knowledge_attest.py` | 知识层的 WAL 安全逻辑摘要 + 快照/恢复（只读） |
| `knowledge_migrate.py` | PR4d 一次性知识迁移：全锁在手、逐 store 日志化事务 |
| `modes.py` | rebase 模式治理：唯一权威解析 + 写回、`mode_*` 旗标、闸冲突裁决 |
| `module_pytest.py` | `imx-omni-pytest` 受闸测试包装（GPU 互斥、看门狗、分层超时） |
| `module_rebase.py` | 单模块 rebase 单元：prompt → agent loop → substate 结果 |
| `parent_compat.py` | 父知识库的只读兼容读取层（`mode=ro`，fail-closed 打开） |
| `path_sync.py` | 模块路径图同步 + manifest modules 段重写 + L2 决定应用 |
| `phase1_steps.py` | phase-1 组合（归类 + 路径同步），父级报告文件名不变 |
| `plan_review.py` | L4 计划评审后端（注入的 LLM client，父级形状的结果） |
| `prompt_builder.py` | 模块/调试 prompt 渲染 —— 等输入下与父级字节一致（golden 钉住） |
| `push_gate.py` | 推送闸裁决：结构性 vs 断言失败的确定性分类（Rev 8 §2.3） |
| `push_to_ci.py` | commit+push-to-CI 编排：preflight、WAL 卫生、C4 双闸、单一传输 |
| `push_wal.py` | 推送 WAL：先落盘的 intent、精确 OID 三分对账、回滚数据 |
| `rebase_tools.py` | 父级 20 工具作为 `ToolDef`；未接线后端**可见地**失败 |
| `runctx.py` | `RebaseRuntime` + `CheckoutLock`（flock+卫生盾）+ 按事件循环的注册表 |
| `substate.py` | 可持久、单写者、merge-not-overwrite 的 `state.json`（run_id 戳） |
| `test_loop.py` | 本地测试环：逐测试恢复、baseline 复跑分流回归、类型化 skip |
| `test_manifest.py` | 动态测试清单：CI YAML + 活测试树 + diff 分类 → 模块计划 |
| `testing_env.py` | agent shell 子环境 scrub 接线（仅 agent shell，进程环境不动） |
| `worktree.py` | 工作树卫生：中止残留 in-flight 状态、丢弃未跟踪产物、L2 脏树决定 |

## 公开契约
按簇：`run_agent_loop` / `rebase_module(ModuleRunConfig)`；`run_test_loop`
/ `run_ci_rounds`（`CIClient` 协议 + 注入动作）；`commit_and_push`→
`PushOutcome`、`evaluate_push_gate`→`GateDecision`、`PushRecord` +
`record_intent`/`reconcile`/`resolve_pending`；`resolve_effective_mode`/
`mode_state_flags`；`Substate`、`REGISTRY`、`CheckoutLock`；
`build_manifest`、`build_module_prompt`、`build_rebase_tools`、
`ensure_wheel_installed`（`WheelSpec`/`PinSpec`）、`load_hooks`。
runner/LLM/CI client 全部可注入 —— 每个模块都能离线测试。

## 不变量
- **C4** —— `commit_and_push` **从不自我授权**：`allowed` 与 `allow_push`
  （ALLOW_PUSH）由调用方传入，`push.guard_push` 裁决；无 `allow_push` 在
  WAL 前就停为 dry-run；执行参数**只**从已授权的 `decision.command` 推导
  （`decision_push_args`），`execute_push` 对未允许的 decision 抛错。
- **C4** —— WAL 纪律：推送前先落**可持久** intent（tmp+fsync+replace+目录
  fsync，真实存储失败传播）；重入先 `resolve_pending`；对账三分
  intended⇒pushed / pre-push⇒retry / 其余⇒escalate，**绝不猜**，且先比
  canonical 远端身份；分支缺失时创建走 absence-pinned lease。token 只走
  `http.extraheader`，URL 进 argv 前去凭证，有 token 时 SSH 改写 HTTPS；
  probe/push/WAL 身份共用**同一次**解析的 URL。
- 模式与闸（Rev 8 §2.1/§2.3）：可变模式**只能显式选取**，`report_only=True`
  + 可变模式、strict+with-failures 都 BLOCKED（narrowing 胜，绝不猜）；
  结构性失败总是阻断（除显式 `push_with_failures`，被记录），断言失败
  FLAGGED 放行。**B3**：`when:` 只用 `mode_state_flags` 的旗标。
- **B1** —— 失败类型化且 fail-closed：`GitIOError`（坏索引绝不读作干净）、
  `PushWalError`（坏记录绝不静默跳过）、`PushPreflightError`（非 40-hex
  上游 commit / pin 不匹配拒推）、`SubstateError`（异 run substate 拒收）。
- **C3** —— agent 的每次工具调用都过 `tools.dispatch`（写工具经
  `write_path_arg` 路径 scoping）；计划闸通过前 edit/pytest/precommit
  工具**不可见**。
- **D2** —— hooks 人闸：manifest 显式声明 + adapter active 才加载，且
  manifest `rebase` 段高风险（agent 写被拒）—— agent 无法自装 hooks。
- **E2** —— 显式降级：未接线后端返回**可见错误**，绝不装作空搜索结果；
  `parent_compat` 声明了但坏 ⇒ 构造即抛，开后故障降级为显式 error dict。
- 检出锁：flock 拿到后必须锁内装好 `/locks/` 卫生盾（根锚定、原子写、
  外来行保留）—— **盾装不上等于锁没拿到**；注册表按（run_dir, 事件循环
  弱引用）发放，绝不复用死循环的原语；teardown 有界、绝不外抛。
- GPU 受闸：`IMX_GPU_MUTEX=1` 时每次调用都持 GPU 锁，否则仅 e2e/examples
  取锁（父级 parity）。
- wheel：每个 uv 调用 `--python` 显式指向**声明的目标 venv** —— 启动
  shell 的 venv 状态绝不影响装到哪；只有 import 验证失败才重试。
- CI 创建受守卫：durable op 记录先于 API 调用，恢复按 op id 精确匹配，
  **不确定时绝不重复创建**。
- 每个被 monitor 的 CI round 持久化实际 monitor 时长，供 run metrics 从 durable
  substate 计费；无法恢复的旧/中止 build 时长保持 unknown。
- CI baseline 使用最高可信来源（schedule > API > other）的最近窗口：最新
  构建失败立即生效，较旧失败只有在窗口内重复出现才保留；单次陈旧红构建不会
  越过更新的绿构建复活。
- baseline 分类以同名 job 的日志根因为身份，provider exit code 只作候选排序；
  支持 `FAILED`/`ERROR` pytest node 的原因相关子集，但缺坐标、日志、当前签名
  或共同异常证据时一律 fail-closed。每个 job 的分类理由与 baseline build/job
  坐标随 round 持久化，供恢复和审计使用。
- 自动 debug agent 不能修改 assertion/tolerance oracle；任何 test 文件编辑只有
  在对应本地验证明确 passed 时才可进入远端重试。拒绝的尝试由调用方恢复快照。
- **A5** —— 全包仓库中立：仓库值经 `WheelSpec`/`PinSpec`/`ManifestSpec`/
  `ModulePromptData`/`tool_schemas.json`/hooks 注入；`test_repo_neutral_core` 钉住。

## 边界 —— 不属于这里
推送授权规则（`push.py`）；工具 scope 强制（`tools`/`scopes`）；step 注册
与编排（装配 PR）；CI provider 的 HTTP 实现（adapter 接线）；测试进程底座
（`testing/`）；知识存储本体（`memory/`）。

## 依赖（允许）
`..push`、`..tools`、`..scopes`、`..run_trace`、`..memory.debug_memory`
（migrate 惰性用 `..memory.*`、`..adapters.base`、`..llm`）、
`..testing.{runner,watchdog,env_plan,process_tree}`；`yaml`；stdlib。
包内 import 单向。**绝不 import `engine/`**（A2 —— 叶子包）。

## 扩展点
adapter 数据（WheelSpec/PinSpec/ManifestSpec/prompt_data/tool_schemas/
watchdog 模式）；`RebaseHooks` 子类；注入可调用（`CIClient`、`RunFn`、
test loop 动作、`precommit_fix`、`RebaseBackends`、LLM client）。
新能力 = 新注入点或新 adapter 数据，不是仓库字面量。

## 测试
`test_push_cluster.py`（gitio/push_wal/push_to_ci/push_gate）、
`test_phase1_cluster.py`、`test_engine_core.py`（substate/runctx/modes/
worktree）、`test_assembly.py`（tools/loop/module/prompt/wheel）、
`test_ci_wiring.py`（ci_loop/test_loop/test_manifest）、
`test_ext1_checkout_guard.py`（锁+卫生盾）、`test_knowledge_migrate.py`、
`test_parent_compat.py`、`test_shell_golden.py`、`test_v3_complete_e2e.py`。

## 重构备注
`ci_loop.py`（1156 行）最大：monitor/分类器/round 编排同居，再长就按
`engine/steps/pr` 先例拆包。`knowledge_migrate.py` 与 `parent_compat.py`
是 PR4d 执行后的退役候补（"无永久双 store 世界"）。docstring 里的
choke-point 编号（agent_loop/rebase_tools 写"C5"）落后于 `_CONSTRAINTS.md`
目录（工具 choke point = C3）—— 值得统一，改注释不改行为。
