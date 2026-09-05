# engine/steps/report.py —— 规范

<!-- verified-against: 2026-09-06 -->

`LOC ~24 · step 库 · refactor-status: ok`

## 职责
`report.final_summary` —— 用累积的 step 输出写出 `RUN_REPORT.md`；repo-rebase
将既有 `FINAL_SUMMARY.md` 嵌入该 canonical 用户报告，不再产出空壳。

## Steps
`report.final_summary`（report/report）。

## 不变量
- 纯输出；**没有失败路径**（永远 ok）。
- 读 `ctx.state["outputs"]` 与同 run 的 rebase summary；只写 run 目录。

## 边界 —— 不属于这里
不做分析、不含仓库知识、除报告文件外没有任何副作用。

## 依赖（允许）
`engine/step`、`._common`。

## 测试
在 playbook 端到端测试中被覆盖。

## 重构备注
平凡。如果想要更丰富的报告，请保持**追加式且无副作用**。
