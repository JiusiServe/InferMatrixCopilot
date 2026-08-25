# memory/skills.py —— 规范

<!-- verified-against: 2026-08-25 -->

`LOC ~384 · 记忆（程序性知识） · refactor-status: ok`

## 职责
程序性知识，门禁比 debug memory 更严。

## 公开契约
`SkillStore(dir)`，带 `find(query, module, k, extra_run_counts?)`、`propose`、
`propose_if_new_identity`（身份去重的提案入口，curator 用）、`promote`、`touch`、
`candidates`、`load_all`、`render_for_prompt`；`Skill`（带用于召回的 `trigger`）；
模块级 usage-journal 原语 `read_usage_counts` / `append_usage`（seed skill 的
使用计数走 journal，seed 文件在运行时保持逐字节不变——消费方是
`_ScopedKnowledge`）。

## 不变量（**D1**）
- agent **只能 `propose`**（写入 candidates 文件）；把它 `promote` 成一个生效的
  `SKILL.md` 是**策展人/人类**的动作。
- `find` 按 模块命中 + 文本命中 + run_count 排序；只有 `status: active` 的 skill
  才会被加载；`extra_run_counts` 把 journal 计数叠加在冻结的 seed frontmatter
  计数之上（使用先验，round-2 F8）。
- **候选写入是崩溃可幸存的**：`_write_durable`（tmp + fsync + replace + 目录
  fsync），candidates 文件在 store flock 下互斥更新。
- `touch` 只在本 store 拥有该 skill 时返回 True —— 调用方据此把 seed 使用
  路由到 journal。

## 边界 —— 不属于这里
不做按仓库的命名空间隔离（由 `_ScopedKnowledge` 施加）；不含 LLM；不是策展 UI。

## 依赖（允许）
`pyyaml`；stdlib。

## 测试
`test_memory.py`。

## 重构备注
propose→promote 这道门很干净 —— **不要**加一个 agent 可调用的 `promote`。
`trigger` 字段是 Devin 式的召回线索；随着更多触发式检索落地，请让它保持一等地位。
按仓库的目录由调用方选择（`adapter.skills_dir`）—— 本类保持路径无关。
