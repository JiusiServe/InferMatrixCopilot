# 精简计划 —— 在不丢任何一条保证的前提下把代码库变小

这是重构所遵循的跨切计划，目标是让代码库**精简**：去重复、删死代码、把重复的样板
收敛成共享 helper。每一条都点名确切的现场（有 grep 支撑）、预估可省行数、要引入的抽象，
以及**必须存活下来的不变量**。逐文件规范里带有对应的 **精简** 小节。

## 状态 —— K1–K7 已在 `main` 上应用（2026-07-10）

七条**全部完成**（全程 211 个测试绿；每条各自一个提交）。结果：**净 −2 个文件**
（删掉 3 个 shim + 4 个死 dataclass，新增 1 个共享的 `profiles/languages.py`），
且下面每一处重复都收敛到了单一真相来源。原始行数大致持平，因为 K2 是用**三份互相
分叉的副本**换来**一个共享模块**（DRY，不是更少的行）；真正的收益是**可维护性** ——
现在一个新 step 直接复用 `._common` 的守卫，语言规则也只住在一处。
**保留本文档作为那些 helper 为何存在的记录，免得它们被重新内联回去。**

## 两条轴 —— 不要混淆

- **精简**（本文档）：更少的行、更少的重复、更少的死代码。**本次重构优先它。**
- **内聚拆分**（各逐文件规范的"重构备注"）：把过大的文件拆成聚焦的文件 ——
  提升可读性，但会**增加文件数**，**并不减少总行数**。

两者冲突时，**优先精简**。例子：`agent_runtime.py`（685 行）曾带着一条内聚拆分备注，
但那里的精简收益更小（把修复轮和证据封顶的代码去重），**不是**拆分 ——
所以先做了去重。等它仍然难以导航时，内聚拆分才跟上。

## 已应用的内聚拆分（2026-07-10，在 K1–K7 之后）

在上面的精简轮之后仍然稠密的两个（后来是四个）过大文件被拆成了包
（全程 219 个测试绿；公开 import 面经由再导出的 `__init__` 保留，
**没有任何 importer 需要改**）：
- `engine/agent_runtime.py`（685 行）→ `engine/agent_runtime/` ——
  `dispatch`/`knowledge`/`utils`（底座）+ `runner`/`ensemble`（入口）。
- `engine/steps/review.py`（341 行）→ `engine/steps/review/` ——
  `prompts`（评测调优过的文本）+ `utils`（确定性 helper）+ `steps`（handler）。
- `engine/steps/pr.py`（484 行）→ `engine/steps/pr/` —— 按关注点拆：
  `fetch`（只读）+ `rebase` + `debug` + `publish`（两个 risk=push 的 step 都在这里）
  + `utils`（`extract_signature`）。
- `cli.py`（406 行）→ `cli/` —— `copilot`（编排器类，**完整保留**）+
  `entry`（argparse/REPL）+ `utils`（纯格式化器）；`__init__`/`__main__` 保住了
  `infermatrix_copilot.cli:main` 入口点和 `python -m` 的对等性。

每一次拆分里，无状态/纯 helper 都搬进了 `utils.py`，好让类/handler 文件承载**控制流
而不是管道**。评测引用注释**跟着它们的代码一起搬**，公开 import 面经再导出的
`__init__` 保留（只有一处测试的白盒 monkeypatch 目标改到了新子模块 —— `pr.debug._gh`
—— 这是四次拆分里**唯一**的测试改动）。

## 精简重构不得破坏的规则

- 逐文件规范里标记的**每一条不变量都逐字存活**；每一个护栏测试仍然通过
  （helper 可以改变一条保证**如何**被满足，**绝不能改变它是否**被满足）。
- 新 helper 必须住在依赖规则允许的地方（step helper 进 `engine/steps/_common.py`；
  共享数据进一个叶子数据模块）。**helper 不得制造被禁止的交叉 import**
  （`_ARCHITECTURE.md` §4）。
- **只会被用一次的 helper 不值得抽** —— 只在 ≥2 个真实调用点时才抽取
  （下面的数字都满足）。

## 按优先级排列的目录（价值最高在前）

### K1 —— 删除死掉的 target dataclass · 约 35 行 · 风险：无
`targets/base.py`（现在的 `push.py`）里的 `ModuleTask`、`ModuleSchedule`、
`ValidationPlan`、`RebaseRunSpec` 除了自己的再导出之外**无处使用**
（已验证：0 个其他 importer）。删掉这四个 dataclass 及其再导出。
**保留** `PushPolicy`/`PushDecision`/`guard_push`（活着的推送守卫）。
*要保住的不变量：* C4（推送守卫）不受影响。

### K2 —— 集中按语言的规则 · 约 30–40 行 + 防止漂移 · 风险：低
"在这门语言里，什么算源文件 / 符号 / 分支"这份数据一式三份：
`review._sweep_targets`（`line_rules`）、`establish`（`LANGUAGE_SUFFIXES` +
`scan_modules`）、`repo_map`（`_SYMBOL_RES` + `_SUFFIXES`）。
引入一个叶子数据模块 `profiles/languages.py`（纯数据 + 极小访问器：逐语言的后缀、
符号正则、分支/索引正则），三个消费者从它 import。
*要保住的不变量：* 未知语言在**每个**消费者里都诚实降级
（只做文件级 sweep / 空的模块扫描 / "use grep"）。

### K3 —— step handler 的守卫 helper · 约 40–60 行 · 风险：低
加进 `engine/steps/_common.py`，替换那些重复块：
- `require_repo(ctx) -> Path | StepResult` —— 各 step 文件里那 **8** 处
  `repo is None → BLOCKED` 守卫，各自缩成一行。
- `adapter_or_result(ctx) -> RepoAdapter | StepResult`（或一个 `@needs_adapter`
  装饰器）—— `profile.py` 里那 **7** 处 `_adapter_from_state` +
  `isinstance(..., StepResult)` 守卫。
- `no_llm_gap(ctx, step, effect) -> StepResult` —— 那 **4** 处一模一样的
  "无 LLM → 记 `capability_gap` → 返回 ok/skip" 块。
- `store_for(adapter) -> ProfileStore` —— `profile.py` 里那 **6** 处
  `ProfileStore(adapter.profile_dir)` 构造。
*要保住的不变量：* 类型化的 BLOCKED 返回（B1）、`capability_gap` trace 事件（E2），
以及每个 step 的公开名字/行为。

### K4 —— `state_updates` 的人体工学 · 可读性 + 约 10 行 · 风险：低
有 **21** 处调用点手写 `outputs={"state_updates": {...}, ...}`。加一个小的构造 helper
—— `published(summary, *, state=None, **outputs)` 或一个 `StepResult.publishing(...)`
类方法 —— 让一次交接变成**一次清晰的调用**。
*要保住的不变量：* **B2** —— 每个被后续 step 消费的 state 键仍然被发布；
**helper 让"遵守"更容易，而不是让它变成可选。**

### K5 —— 退役三个引擎 shim · 约 26 行 + 3 个文件 · 风险：低
`engine/{builtin_steps,pr_steps,rebase_native_steps}.py` 是再导出 shim。
先迁移它们的 importer（各 shim 的规范里列了名单），然后删掉文件和它们的规范。
*要保住的不变量：* 在其 fixture 迁移完成之前，
`rebase_native_steps._RUNTIME` 的"同一个对象"保证。

### K6 —— 去重 cli 的 过门+确认 · 约 15 行 · 风险：低
`Copilot.run_task` 和 `run_playbook` 重复了 plan-review + `[y/N]` 确认的序列。
抽出 `_gate_and_confirm(resolution, spec, assume_yes) -> bool`。
*要保住的不变量：* 确认之前先 plan-review；
`confirm_required or requires_review` 时触发确认。

### K7 —— 抓取类 step 的"从 state"早返回 · 约 10 行 · 风险：无
有 **5** 个抓取 step 以 `if "X" in ctx.state: return ...(state_updates)` 开头。
一个 `from_state(ctx, key) -> StepResult | None` helper 就能把它们收掉。
*要保住的不变量：* 注入式/离线测试路径保持完好。

## 总计预估
约 **160–200 行**被移除、约 **4 个文件**被删除，若干重复模式收敛到单一调用点 ——
而这一切都发生在任何内聚拆分**之前**。缩得最多的是各 step 文件（K3+K4+K7），
而那正是新 step 被添加的地方，所以**新增一个 step 的边际成本也随之下降**。

## 建议顺序（每一步都可独立发布，之间保持测试绿）
1. K1、K5（纯删除 —— diff 最小，立竿见影地变小）。
2. K3、K4、K7（`._common` helper —— step 文件样板的收敛）。
3. K2（`profiles/languages.py` —— 跨文件去重）。
4. K6（cli helper）。
5. **然后**才重新考虑内聚拆分（各逐文件规范的重构备注），
   此时面对的已经是一个更小、已去重的基线。
