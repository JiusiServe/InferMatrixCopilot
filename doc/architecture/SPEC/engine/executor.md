# engine/executor.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~267 · 引擎底座（那个循环） · refactor-status: ok`

## 职责
以与任务无关的保证运行一个 playbook 的各个 step：检查点/resume、`foreach` 扇出、
`when:` 条件、有界重试、类型化失败路由、升级。

## 功能
`run` 逐个迭代 step；跳过已完成的（并**恢复它们的 `state_updates`**）；对 `foreach`
扇出；求值 `when:`；对 RETRYABLE 重试；把 BLOCKED/ESCALATE/FORBIDDEN 路由给 notifier；
持久化进度并按 step id 索引输出。

## 公开契约
`Executor(registry, settings, run_dir, trace, llm?, notifier?)`；
`run(playbook, state) -> RunOutcome(status, step_results, blocked_reason)`。
helper：`_eval_when`、`_merge`。

## 不变量
- **B2**：resume 在跳过之前先恢复 `outputs.state_updates`；成功后
  `state.update(state_updates)` 并按 step id 索引输出。
- `_merge` 把每个 foreach 条目的 `state_updates` **提升**到顶层（同键最后写者胜）。
- **B3**：`when:` 先读 TaskSpec 再读 state；**未知键 → 阻塞，绝不静默**。
- **B1**：类型化路由；未处理的异常 → BLOCKED（**绝不吞掉**）。
- 只对 RETRYABLE 重试，受 `max_step_retries` 限制。
- **run 级 task params 会到达每个 step**：`state["task_spec"]["params"]` 被合并在每个
  step 自己的 params **之下**，所以 `--task-param limit=5` 不会被静默丢弃。
  **playbook 自己的 params 在合并中获胜** —— 其中好几个是安全攸关的
  （`force_push`、`pre_push`），因此被撰写下来的不变量**不得**被命令行覆盖。
- step 的 span 会记录 playbook 的 step id 和 foreach 条目键：同一个 spec 可能在一个
  playbook 里跑两次、还会再扇出，所以**光靠 `step` 无法标识这份工作**。

## 边界 —— 不属于这里
不含 step 逻辑、不含仓库知识、不做规划、不含 LLM prompt。**只提供执行保证。**

## 依赖（允许）
`engine/{step,registry}`；仅类型引用：config/llm/notifier/playbook/run_trace。

## 扩展点
新的**跨 step** 保证（例如逐 step 超时）放这里；新的 step **行为**不放这里。

## 测试
`test_engine.py`、`test_v2_p0.py`（resume/foreach/when 的完整性）。

## 重构备注
约 200 行，职责划得很好。`state_updates` 的发布/恢复/合并逻辑**微妙且承重**
（它曾是 v2 的头号缺陷）—— **不要在没有重跑 resume 完整性测试的情况下"简化"它**。
如果将来加入 DAG 边（目前只有有序列表），请把它们留在这里、藏在同一个 `RunOutcome`
契约之后。
