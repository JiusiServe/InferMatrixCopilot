# memory/debug_memory.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~465 · 记忆（失败→修复库，schema v2） · refactor-status: ok`

## 职责
以 FTS5 存放"失败 → 修复"经验。

## 公开契约
`DebugMemory(db_path)` / `DebugMemory.open_readonly(db_path)`，带 `record`（必填
字段强制）、`search(query, k, repo?)`、`get`、`count`、`entries(repo?, ...)`、
`apply_curation(updates)`、`schema_v2` / `ensure_schema_v2()`；模块级 helper：
`readonly_uri`、`strip_sql_comments`、`is_fts5_table`、`fts5_unindexed_columns`
（供 attest/迁移侧做 FTS5 完整性检查）。

## 不变量（**D1/D3**）
- 一次写入必须包含
  repo/module/run_id/symptom/root_cause/fix_summary/files/verification/status。
- 检索是按相关度取 top-k，**摘要优先**。
- 事实可自由记录；晋升为 skill 是**另一个**受门禁的动作。
- **schema v2 升级只走显式维护入口**（`ensure_schema_v2()`）：打开既有 DB 绝不
  作为副作用改 schema —— report-only 路径必须能证明零写入（**D4**）。
- `open_readonly` 经 `readonly_uri`（路径百分号转义的 `file:...?mode=ro`）打开；
  只读句柄上的写入（含 `apply_curation`）**抛错**。
- `apply_curation` 单事务写策展字段（status/tags/watch_outs/derived_from 等
  additive 列），随后**一次性重建** FTS 镜像；status 域为
  candidate/active/stale/retired。

## 边界 —— 不属于这里
不做按仓库的命名空间隔离（由 agent 运行时的 `_ScopedKnowledge` 施加）；不含 LLM。

## 依赖（允许）
stdlib 的 `sqlite3`。

## 测试
`test_memory.py`、`test_curator.py`、`test_knowledge_migrate.py`、
`test_knowledge_readcompat.py`。

## 重构备注
写入契约（必填字段）就是 D3 保证 —— **在写入时强制它，绝不接受残缺的记忆**。
按仓库的 DB 路径由调用方选择 —— 运行时经 `KnowledgePaths.resolve(...)`
（PR4d cutover 之后是 `shared_write_db`），本类保持路径无关。
