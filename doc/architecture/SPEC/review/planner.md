# review/planner.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~307 · 评审深度选择 · refactor-status: ok`

## 职责
为一个 PR 选定评审深度（`light` / `standard` / `full`）。

## 功能
4-lens ensemble 是重大改动的**召回下限**，但要花约 4 倍的 token 和时延（实测：
一个 2 文件 /+60 行的 PR 消耗了约 110 万输入 token、耗时 4 分 48 秒，其中 97% 在评审
阶段）。确定性规则先裁明确案例；只有灰区才花一次小的 LLM 调用。

## 公开契约
`plan_review_depth(...) -> depth`，以及那些确定性分类器。

## 不变量（**C2**、**B2**）
- **`light` 永远不可能来自模型输出。** 灰区那次调用**只能**返回 `standard` 或 `full`。
  这正是这里真正要紧的抗提示注入性质：**PR 里的内容说服不了 planner 少审自己。**
- 深度不变量就地强制：`light` ⇒ 无 lens；`standard` ⇒ 2–3 个 lens；`full` ⇒ 全部。
- 确定性规则**先跑**，不花模型调用就裁掉明确案例（小 + 低风险 → light；
  大或高风险路径 → full）。
- playbook 的 `review_depth` 参数可以显式 pin 住深度，覆盖 planner。
- **灰区调用需要推理留白。** 它曾在两个战役里对**每一个**灰区条目静默失败，因为思考
  在任何 JSON 出现之前就吃完了 400-token 的上限 —— 这里的 cap 是**正确性设置，
  不是成本旋钮**。

## 边界 —— 不属于这里
不执行 lens（`agent_runtime/ensemble.py`）；不做渲染；不含仓库专属风险清单
（那些来自 profile / adapter 的模块映射）。

## 依赖（允许）
`..config`、`..llm`、stdlib。**不 import 任何 step。**

## 测试
`test_review_planner.py`。

## 重构备注
注意包的划分：这个文件管评审**深度**，而 `engine/steps/review/` 装的是评审 step 本身。
**同一个词，两个包 —— 不要合并它们。**
