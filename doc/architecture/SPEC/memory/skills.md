# memory/skills.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~120 · 记忆（程序性知识） · refactor-status: ok`

## 职责
程序性知识，门禁比 debug memory 更严。

## 公开契约
`SkillStore(dir)`，带 `find`、`propose`、`promote`、`candidates`、`load_all`、
`render_for_prompt`；以及 `Skill`（带用于召回的 `trigger`）。

## 不变量（**D1**）
- agent **只能 `propose`**（写入 candidates 文件）；把它 `promote` 成一个生效的
  `SKILL.md` 是**策展人/人类**的动作。
- `find` 按 模块命中 + 文本命中 + run_count 排序；只有 `status: active` 的 skill
  才会被加载。

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
