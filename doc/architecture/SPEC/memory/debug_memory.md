# memory/debug_memory.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~106 · 记忆（失败→修复库） · refactor-status: ok`

## 职责
以 FTS5 存放"失败 → 修复"经验。

## 公开契约
`DebugMemory(db_path)`，带 `search(query, k)` 和一个要求必填字段的写入方法。

## 不变量（**D1/D3**）
- 一次写入必须包含
  repo/module/run_id/symptom/root_cause/fix_summary/files/verification/status。
- 检索是按相关度取 top-k，**摘要优先**。
- 事实可自由记录；晋升为 skill 是**另一个**受门禁的动作。

## 边界 —— 不属于这里
不做按仓库的命名空间隔离（由 agent 运行时的 `_ScopedKnowledge` 施加）；不含 LLM。

## 依赖（允许）
stdlib 的 `sqlite3`。

## 测试
`test_memory.py`。

## 重构备注
写入契约（必填字段）就是 D3 保证 —— **在写入时强制它，绝不接受残缺的记忆**。
按仓库的 DB 路径由调用方选择（`adapter.debug_memory_db`）—— 本类保持路径无关。
