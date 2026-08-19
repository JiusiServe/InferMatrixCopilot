# engine/planner.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~116 · 规划 · refactor-status: ok`

## 职责
把一个 `TaskSpec`（+ 仓库能力）解析成可运行的 `Playbook`，走
**reuse > adapt > generate**，并处理能力缺口。

## 功能
查找 playbook（`store.find`）；返回 reuse（原样）/ adapt（在非 locked 上追加参数 →
需评审）/ generate（仅只读 kind，固定模板）；遇到 locked 改编、具备写能力的 generate、
或能力缺口时抛 `PlanningError`。

## 公开契约
`Planner(store, registry)`；`resolve(spec, capabilities?) -> Resolution`；
`PlanningError`；`_GENERATE_TEMPLATES`。

## 不变量
- reuse：当参数 ⊆ 已声明面时 `requires_review=False`。
- **locked playbook 拒绝改编**（抛错）。
- **C2**：generate **只对只读 kind 存在**，并会重新检查每个 step 的
  `risk ∈ {read, report}`（否则抛错）。
- 能力缺口（**§ARCH.8**）：具备写能力 + 未满足 → 抛出 "run repo_profile"；
  只读 → 走 generate；`capabilities=None` 即 v1 行为。
- tier 来自 `spec.tier` —— **绝不自己发明**。

## 边界 —— 不属于这里
只做选择/参数化。不执行、不含仓库知识、不含 LLM、不做原始工具编排（**A3**）。

## 依赖（允许）
`playbooks/store`、`task_spec`、`engine/registry`。

## 扩展点
需要生成的新只读 kind → 在 `_GENERATE_TEMPLATES` 加一条由 read/report step 组成的
条目。**具备写能力的 kind 必须自带一份已审核的 playbook。**

## 测试
`test_planner_playbooks.py`、`test_capabilities.py`。

## 重构备注
小而干净；**三条分支就是它的全部意义 —— 不要把它们合并**。能力缺口的提示文本是面向
用户的操作指引（"run repo_profile"）—— 保持它可执行。如果将来 generate 需要 LLM 编排，
它**仍然必须**通过逐 step 的 risk 复检；绝不为了灵活性绕过 C2。
