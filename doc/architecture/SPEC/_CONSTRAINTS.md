# 01 —— 编程约束与不变量目录

让代码保持干净与安全的那些规则。每一条都表述为**可强制的约束**，并给出钉住它的
机制/测试。**违反其中任何一条的改动都是错的，哪怕它"能跑"。**

## A. 结构约束（组织）

- **A1 —— 一个模块一个职责。** 每份逐文件规范都点名了它唯一的职责。
  引入不相关的关注点意味着**新建一个模块**，而不是把现有模块撑大。
- **A2 —— 依赖方向只能向下/向外。** 见 `_ARCHITECTURE.md` §4。
  叶子包**绝不** import `engine/`；接口层**绝不**被向下 import；
  step 模块**绝不互相 import**（共享代码 → `engine/steps/_common.py`）。
- **A3 —— step 编排工具，planner 编排 step。** planner **不得**编排原始工具；
  一个 step **不得**只是某个工具的薄别名。step = **一次稳定的工程动作**，
  带声明的风险、I/O 和成功判据。
- **A4 —— 自注册，单一定义。** 一个 step 的名字、元数据（kind/risk/scope/triggers）
  和 handler **就在它的定义处**通过 `@step(...)` 或 `register_step(StepSpec(...))`
  写在一起。**不存在集中式的 `add()` 块。**
- **A5 —— 知识在边缘。** 仓库专属字面量（仓库名、模块名、领域 prompt、绝对路径、
  CI 接线）**只**住在 `adapters/<repo>/` 之下。由 `test_repo_neutral_core` 钉住
  （逐文件的泄漏上限**只能变小**；shim 和委托文件承载着仅有的已知例外）。

## B. 契约约束（类型化、结构化、显式）

- **B1 —— 类型化失败，绝不裸抛异常。** step 返回
  `StepResult(ok=False, failure=FailureKind.X)`。六种 —— RETRYABLE、REPLAN、
  TEST_FAILURE、BLOCKED、FORBIDDEN、ESCALATE —— 在 executor 里走**不同路由**。
  未处理的异常被强制转为 BLOCKED，**绝不吞掉**。
- **B2 —— 状态交接必须被发布，而不只是被修改。** 任何被后续 step 消费的 state 键
  **必须**经 `outputs.state_updates` 发布（JSON-simple；像 `PushPolicy` 这样的
  dataclass 要序列化）。**只做 `ctx.state[...] = v` 会在 resume 时丢失。**
  由 resume 完整性测试钉住。（**这曾是 v2 的头号正确性缺陷。**）
- **B3 —— `when:` 条件只能引用已知键。** 它先读 TaskSpec 字段、再读已发布的 state 键；
  未知键会在执行时**大声阻塞**，**绝不静默地判为 false**。
- **B4 —— 结构化的 agent I/O。** 每个 `kind == "agent"` 的 step 都经 `run_agent_step`，
  带显式 dispatch context 和 JSON 输出契约（基础 schema + 逐 step 扩展）、一轮修复、
  类型化的 状态 → 失败 映射。**step 里不得为了做 agentic 工作而临时
  `ctx.llm.create()`。** 由 `test_agent_runtime.py` 里的参数化 dispatch 测试钉住。

## C. 安全约束（权限与护栏）

- **C1 —— tier 是推导的，绝不解析而来。** `TaskSpec` 没有可设置的 tier 字段；
  `tier` 是 `kind` 的 property。**自然语言无法扩大权限。**
- **C2 —— 生成路径在结构上只读。** planner 的 generate 路径在任何被编排的 step
  `risk ∈ {write_workspace, push, knowledge}` 时抛错；
  没有已审核 playbook 的写能力 kind 一律**升级**。
- **C3 —— 唯一的工具 choke point。** 每次工具调用都过 `tools.dispatch`，
  由它强制 `ToolScope`/`PathScope` 并记 trace。三种结果：允许 / 拒绝 /
  执行但记录（可写墙内的越界写）。agent step **只**看得见其 scope 允许的工具。
- **C4 —— 唯一的推送 choke point。** 每次推送都过 `push.guard_push`：
  需要一个允许的 `PushPolicy` **且**分支不受保护；force 只有 with-lease；
  除非 `ALLOW_PUSH=1` 否则是 dry-run。**受保护分支永不被推送，与策略无关。**
- **C5 —— 对外写入是双闸的。** 发评论/回答需要显式的 `post` 意图**并且**
  `ALLOW_POST=1`；两者默认都关（dry-run）。
- **C6 —— 评审 fail-closed。** 没有 reviewer 时 plan/patch review 返回 `unavailable`；
  除 `lgtm`/`pass` 之外一律视为未通过。**缺少 reviewer 不等于静默批准。**
- **C7 —— 不可信数据被围栏。** GitHub/CI 文本进入 agent prompt 时被包在
  `<untrusted_data>` 里，并带"这不是指令"的前言；**只有终端输入到达意图解析器**
  （通道分离）。

## D. 知识治理约束

- **D1 —— 事实自由记录，知识经门晋升。** RunTrace/debug memory 廉价且仅追加。
  skill、playbook、adapter 和 profile fact 都是 candidate→promote；
  **晋升是策展人/人类的动作**。
- **D2 —— agent 提议，人类裁决（高风险处）。** agent **只能**写 candidate。
  `update_manifest` 拒绝 agent 对 `manifest.yaml` 高风险段
  （`push`/`repo`/`upstream`）的写入。profile judge **只读**。
- **D3 —— 每条 profile fact 都要有溯源 + 稳定性。** 各自携带
  `source`/`evidence`/`first_seen`/`last_confirmed`/`confirmations`；
  **无证据的 fact 被拒**；稳定 fact（≥3 次确认）在重写时**不得丢失已引用的证据**；
  被取代的正文进 `history`，**绝不删除**。
- **D4 —— 两个写入层。** 逐 run 的 op 是**追加式**的（`RUN_OPS`）；
  只有**有节奏的巩固层**可以 rewrite/merge/mark-stale。
  **禁止连续的 LLM 重写**（它会腐蚀记忆）。
- **D5 —— profile 内容按通道分类。** `machine` fact 喂代码，有词预算的 `briefing`
  切片进 prompt，`retrieved` fact **只在按需时**浮现。
  **自动生成的概览不得被整体注入。**

## E. 可观测与降级约束

- **E1 —— 每条治理主张都有一个 trace 事件。** 只要某道守卫触发过、某个 scope 拒绝过、
  某条 fact 被应用过、或某项能力缺失过，就有对应的 RunTrace 事件
  （`tool_refused`、`out_of_scope_edit`、`patch_review`、`capability_gap`、
  `profile_*`…）。
- **E2 —— 显式降级，绝不静默。** 能力缺失（没有 CI provider、没有 LLM、语言不支持）
  会记一条 `capability_gap` 事件和一次**被声明的降级**；
  它**绝不崩溃**，也**绝不假装能力完整**。
- **E3 —— metrics 绝不搞坏一次 run。** `metrics.py` 的失败被捕获并记 trace；
  **run 的成败与它的 metrics 无关**。

## F. 不变量目录（快速索引 → 归属）

| # | 不变量 | 归属文件 | 测试 |
|---|---|---|---|
| C1 | tier 由 kind 推导 | `task_spec.py` | `test_intent_taskspec.py` |
| C2 | generate 只读 | `engine/planner.py` | `test_planner_playbooks.py`,`test_capabilities.py` |
| B1 | 类型化失败路由 | `engine/executor.py` | `test_engine.py` |
| B2 | resume 时的 state_updates | `engine/executor.py` + 各 step | `test_v2_p0.py` |
| B3 | `when:` 只用已知键 | `engine/executor.py` | `test_v2_p0.py` |
| B4 | 受治理的 agent I/O | `engine/agent_runtime.py` | `test_agent_runtime.py` |
| C3 | 工具 choke point | `tools.py` + `scopes.py` | `test_scopes_tools.py` |
| C4 | 推送 choke point | `push.py` | `test_push_and_steps.py` |
| A5 | 仓库中立的核心 | 整个 `src/` | `test_v2_p0.py::test_repo_neutral_core` |
| D3 | 溯源 + 稳定性 | `profiles/store.py` | `test_profile_store.py` |
| D2 | judge/agent 对生效内容只读 | `profiles/*`,`adapters/base.py` | `test_p3_machinery.py` |
