# run_trace.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~40 · 跨切（审计脊柱） · refactor-status: ok`

## 职责
仅追加的 JSONL 事件日志 —— 不可变的审计层。

## 功能
`record(event, **fields)` 追加一行 JSON；`events(name)` 按类型过滤。

## 公开契约
`RunTrace(path)`，带 `record`、`events`。

## 不变量
- **E1**：每一条治理主张都映射到一个 trace 事件（`agent_dispatch`/`agent_output`、
  `tool_call`/`tool_refused`/`out_of_scope_edit`/`full_file_write`、
  `patch_review*`、`push_requested`、`capability_gap`、`env_exported`、
  `posted_artifact`、`profile_*`）。
- 事实可以自由记录（**D1**）；这是精选 profile 之下的**不可变层**。

## 边界 —— 不属于这里
只负责记录。不含策略，不过滤"什么可以被记录"，也不做驱动控制流的读取
（`events()` 仅供 diff-summary / metrics 组装使用）。

## 依赖（允许）
仅 stdlib。

## 扩展点
新事件 → 在现场直接 `record("<name>", ...)`；如果它支撑某条保证，就在
`_CONSTRAINTS.md` §E1 里记下这个名字。

## 测试
全套测试通过 `trace.events(...)` 断言间接覆盖。

## 重构备注
**刻意保持平凡且无依赖 —— 请维持现状。** 它托着每一条治理主张，所以绝不能引入
可能失败、进而丢事件的逻辑。
