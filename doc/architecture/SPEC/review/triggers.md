# review/triggers.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~50 · 评审（触发规则） · refactor-status: ok`

## 职责
决定 LLM patch review 什么时候触发。

## 公开契约
`evaluate_triggers(summary, settings, *, touched_modules, pre_push,
knowledge_edit, high_risk_modules?) -> fired[]`；`ALL_RULES`（7 条）。

## 不变量
- 七条规则：`out_of_scope_edits`、`high_risk_modules`、`large_diff`、
  `tests_unavailable`、`full_file_fallback`、`before_push`、`knowledge_edit`。
- 高风险模块来自**调用方**（adapter），settings 只作为兜底（**A5**）。

## 边界 —— 不属于这里
不构建 diff（那是 `diff_summary`），不调 LLM（那是 step 的事 —— 触发时它才调
`reviewer`）。

## 依赖（允许）
`config`、`review/diff_summary`。

## 测试
`test_review.py`。

## 重构备注
**这套规则集就是契约** —— 增删一条触发器就改变了安全姿态（**C6**），必须是刻意且
有记录的变更。保持它是 (summary, settings, 调用方标志) 的纯函数。
