# profiles/consolidate.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~52 · profile（Stage-4 helper） · refactor-status: ok`

## 职责
确定性的 Stage-4 helper：陈旧衰减 + 漂移检测。

## 公开契约
`decay_stale(store, days) -> stale ids`；`detect_drift(adapter, store) -> findings`。

## 不变量
- `decay_stale` 通过 store 的 `mark_stale` op，把超窗口的 active fact 翻成 `stale`
  （**排除，而不是删除**）（**D4**）。
- `detect_drift` **只报告**：已声明却消失的模块路径、挂到未知模块上的 fact；
  **它绝不做任何变更**。

## 边界 —— 不属于这里
只做确定性检测 —— 不含 LLM，不自动修（巩固是 `agent.profile_consolidate` step 的事）。

## 依赖（允许）
`adapters/base`、`profiles/store`；stdlib 的 `time`。

## 测试
`test_p3_machinery.py`。

## 重构备注
小而纯。**保持 `detect_drift` 只报告** —— "findings 变成刷新提案，绝不自动修"
这条规则正是它的全部意义（**D2**）。
