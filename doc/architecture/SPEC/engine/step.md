# engine/step.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~67 · 引擎基础词汇 · refactor-status: ok`

## 职责
整个引擎共用的基础执行词汇。

## 功能
定义失败分类法、step 的 result/context/spec 数据类，以及 `Kind`/`Risk` 字面量集合。

## 公开契约
`FailureKind`（RETRYABLE、REPLAN、TEST_FAILURE、BLOCKED、FORBIDDEN、ESCALATE）；
`StepResult(ok, failure?, summary, outputs, changed_files)`；
`StepContext(settings, state, params, run_dir, trace, llm?, item?)`；
`StepSpec(name, kind, risk, handler, description)`。`Kind ∈ {deterministic,
script, agent, validation, report}`；`Risk ∈ {read, write_workspace, push,
knowledge, report}`。

## 不变量
- 与仓库、任务无关；`StepSpec` 是 frozen 的。
- 六种 `FailureKind` 就是完整的路由词汇（**B1**）。
- `risk` 是被强制的（planner C2）；`kind` 是描述性的（按约定 `agent` ⇒ 受治理运行时）。
  **不要装饰性字段**：`StepSpec` 的每个字段都必须被什么东西读取
  （`tool_scope`/`patch_review_triggers` 两个字段已被移除，因为没有任何东西强制它们
  —— scope 和触发器都是 handler 本地的）。

## 边界 —— 不属于这里
只有类型 —— 无行为、无 registry、不执行。

## 依赖（允许）
只有 `run_trace`（**§ARCH.4.3**）。不含任何任务/仓库专属内容。

## 扩展点
新增一个 `Kind`/`Risk` 取值或 `FailureKind` 是**刻意的词汇变更** —— 必须与
executor 的路由和 `_CONSTRAINTS` 一起更新。

## 测试
到处都在用；形状被隐式钉住。

## 重构备注
地基性文件 —— 把依赖集合**精确**保持在 {run_trace}。在这里多加一个 import，就会把
整个引擎耦合到它上面。如果 `StepContext` 长出更多可选字段，那是**某个 step 越权**的
信号，而不是这个文件需要重构的信号。
