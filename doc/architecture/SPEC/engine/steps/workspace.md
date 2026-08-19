# engine/steps/workspace.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~43 · step 库 · refactor-status: ok`

## 职责
工作区前置条件 + 廉价 diff 摘要两个 step。

## Steps
`workspace.guard_clean`（deterministic/read）、`analysis.diff_summary`
（deterministic/read）。

## 不变量
- `guard_clean` 在**脏树**上拒绝启动（BLOCKED）—— 这是任何具备写能力的 run 的前置条件。
- 两者都是确定性的 —— **不含 LLM**。

## 边界 —— 不属于这里
不修改工作区；不含仓库知识。

## 依赖（允许）
`review/diff_summary`、`engine/step`、`._common`。

## 测试
`test_push_and_steps.py`（guard），diff-summary 经评审测试覆盖。

## 重构备注
平凡且正确。如果出现更多只读的"分析"类 step，可以共用这个文件。

## 精简 —— **K3**
`guard_clean`/`diff_summary` 各自重复了 `repo is None → BLOCKED` 这道守卫 →
应收敛为 `require_repo(ctx)`（K3 的 8 个现场之一）。
