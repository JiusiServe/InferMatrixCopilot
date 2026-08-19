# review/diff_summary.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~62 · 评审（always-on 阶段） · refactor-status: ok`

## 职责
patch review 里那个**廉价、常开**的第一阶段。

## 公开契约
`build_diff_summary(repo, base_ref, primary_files, trace) -> DiffSummary`
（改动文件、增删行数、越界文件、整文件写、已跑测试、是否请求推送）。

## 不变量
- 确定性；**不含 LLM**。
- 读取 git diff + RunTrace 事件（`out_of_scope_edit`、`full_file_write`、
  `test_run`、`push_requested`）来构建摘要。

## 边界 —— 不属于这里
不做触发判断（那是 `triggers`），不出裁决（那是 `reviewer`）。

## 依赖（允许）
`run_trace`；stdlib 的 `subprocess`/`fnmatch`。

## 测试
`test_review.py`。

## 重构备注
单阶段，很干净。**保持它便宜（不调 LLM）** —— 它每道门都会跑；只有当这份摘要触发了
某条规则时，LLM 才会跑。
