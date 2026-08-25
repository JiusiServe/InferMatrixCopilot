# memory/curator.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~372 · 记忆（debug memory 的有节奏巩固层） · refactor-status: ok`

## 职责
对 debug-memory 库的**一次策展**（parent `agent/curator.py` 的仓库中立移植）：
合并近重复、按上游 commit 距离标 stale、休眠降级、模式提取成 skill 候选。

## 功能
`curate()` 依次跑四个规则式 pass（逐模块贪心单链聚类，Jaccard over
key+symptom+root_cause token），把全部变更凑成一个批次交
`dm.apply_curation()`，返回 `CuratorReport`。

## 公开契约
`DebugMemoryCurator(dm, *, repo, sim_threshold, propose_to, survivor_key, …)`
带唯一入口 `curate(recent_runs) -> CuratorReport`；`CuratorReport(.to_dict)`；
`SkillCandidate`。

## 不变量（**D1/D4**）
- **D4** —— 本类**就是**那个"有节奏的巩固层"：唯一被允许 merge/rewrite/
  mark-stale 的地方，且纯规则、**无 LLM**（连续 LLM 重写被 D4 明令禁止）。
  构造时强制 v2 schema，否则 `RuntimeError` —— 升级只走 sanctioned 入口。
- **退休、绝不删除**：被合并行变为 `status='retired'` +
  `derived_from=<幸存者 id>`；retired 行被排除出所有策展输入和检索，
  所以对已策展库再跑一遍是**严格 no-op**。
- **仓库限定**：每次读取都过 `entries(repo=…)` —— 外仓行原封不动。
- **D1** —— 模式提取只经 `propose_to.propose_if_new_identity` 写
  **candidate**，绝不自动生成生效 skill；身份是 `module+key`（非散文），
  check-allocate-write 是 store 候选 flock 内的一个临界区。
  已被现有 skill 覆盖（Jaccard 或 0.45 overlap）的簇不再提议。
- 休眠只在**提供了 run 窗口时**判定；迁移来的行
  （source ∈ parent-db/copilot-global/adapter-tree）豁免休眠钟
  （其 run id 属外来 id 空间 —— F12），commit 距离 staleness 仍适用。
- stale 只在 `merge-base --is-ancestor` 成立且距离超阈时标记；
  diverged/未知 → **绝不标**（parent parity）。
- `survivor_key` 默认最新 id 胜出；迁移传入来源优先序，新导入的低优先级行
  **绝不**退休更高优先级的运行时知识（F11）。

## 边界 —— 不属于这里
不是逐 run 写入路径（`debug_memory.record`，追加式）；不是 skill 晋升
（`SkillStore.promote`，人类动作）；不是迁移编排
（`rebase_engine/knowledge_migrate.py` 调用它）；不做 schema 升级。

## 依赖（允许）
`.debug_memory`、`.skills`；stdlib（`re`、`subprocess` 只为 git 距离）。

## 测试
`test_curator.py`（退休带血统、二次策展 no-op、外仓不动、非可行动过滤、
schema-v2 门、slug 冲突共存等 16 个）；迁移侧策展在 `test_knowledge_migrate.py`。

## 重构备注
`_extract_patterns` 一个方法背着 聚类+覆盖检查+提议 三件事，是最先该拆的；
`_non_actionable` 的 pattern/tag 表是 parent-verbatim 数据 —— 若继续膨胀，
考虑挪进 adapter 数据而非在此续表。
