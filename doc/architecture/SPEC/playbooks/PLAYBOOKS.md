# playbooks/*.yaml —— 规范

<!-- verified-against: 2026-08-31 -->

`9 个文件 · 声明式编排数据 · refactor-status: ok`

> 当前集合：`pr-review`@6、`pr-quality`@1、`pr-debug`@2、`pr-rebase`@2、`issue-answer`@2、
> `issue-triage`@2、`repo-profile`@1（active）；`repo-rebase-v3`@1（**locked**）；
> `profile-consolidate`@1（candidate）。带 step 链的完整清单
> 在 [`../../../GUIDE.md`](../../../GUIDE.md) §5 —— **不在这里**。

## 职责
用声明式的有序 step 列表（含 `foreach`、`when:`、逐 step `params`）实现一种任务 kind。

## 每个文件的契约
`name, version, status, task_kinds, repos, requires?, params, provenance,
success, steps[]`。

## 已注册的 playbook
- `repo-rebase-v3` —— **locked**，L0，仓库中立（`repos: []`、
  `requires: [modules, upstream.fork_tracking, ci.provider]`）。全仓库
  rebase 引擎（2026-08-25 切换；委托版 v2 与 native-v1 已删除）——
  **不要改它的 step 列表**。
- `pr-rebase`/`pr-debug`/`pr-review`/`pr-quality`/`issue-answer`/`issue-triage` —— active，
  仓库中立（`repos: []`、`requires: [repo.path]`）。
- `repo-profile` —— active，仓库中立（用于接入第二个仓库）。
- `profile-consolidate` —— **candidate**
  （planner 不可见；只能经 `--playbook` 运行）。

## 不变量
- 每个 step id 唯一；每个 `step` 名字都必须已注册（由 `store.validate` 强制）。
- 写/推送 step **只**出现在已审核（非生成）的 playbook 里。
- locking 面向会改代码/会推送的 playbook；晋升 candidate→active→locked
  是**带 provenance 的人类动作**。
- **`candidate` 对 `find()` 不可见** —— 只能经 `--playbook <name>` 到达。
  正是这一条让 `profile-consolidate` 保持"刻意的节奏"（连续的 LLM 重写**实测**会腐蚀
  记忆）。
- 仓库中立的 playbook 声明 `repos: []` + 一份 `requires:` 能力清单；
  存在精确 repo 的 playbook 时仍然由它获胜。

## 边界 —— 不属于这里
不含代码；除 `repos`/`requires` 匹配外不含仓库知识。

## 扩展点
新任务 = 一个 YAML 文件；新仓库在其 profile 满足 `requires` 之后，
**直接复用仓库中立的 playbook**（核心零改动）。

## 重构备注
它们是 reuse>adapt>generate 模型里的"配置"那一半 —— **保持声明式**。
要顶住在 `when:`/`foreach` 之外加条件逻辑的冲动；更复杂的东西属于某个 step。
**当第二个仓库接入时，它应该不需要任何新 playbook —— 那就是不变性测试。**
