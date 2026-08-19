# playbooks/store.py —— 规范

<!-- verified-against: 2026-08-18 -->

`LOC ~166 · 规划（注册表） · refactor-status: ok`

## 职责
带版本的 playbook 注册表：加载/解析/校验 YAML，按 kind+repo+capabilities 召回，
持久化 candidate。

## 公开契约
`Playbook`、`PlaybookStep`、`parse_playbook`、`playbook_to_doc`；
`PlaybookStore(dir, registry)`，带 `find(kind, repo, capabilities?)`、
`missing_capabilities(kind, capabilities)`、`get`、`all`、`save_candidate`、
`validate`。

## 不变量
- 状态为 `candidate | active | locked | retired`；`find` **只召回 active/locked**；
  candidate 只能经显式 `--playbook` 运行。
- `find`：精确 repo 优先；仓库无关的匹配仅当 `requires ⊆ capabilities`（已知时）；
  locked > active；高版本 > 低版本。
- `validate` 拒绝引用了未注册 step 的 playbook（**加载即失败**）。
- `save_candidate` 强制 `status=candidate`（**D1** —— 不允许自我晋升）。

## 边界 —— 不属于这里
不执行、不含规划策略（那是 planner 的）、不含 step 逻辑。

## 依赖（允许）
`engine/registry`、`pyyaml`。

## 扩展点
新增 playbook 字段 → `Playbook` + `parse_playbook` + `playbook_to_doc` **一起**扩展。

## 测试
`test_planner_playbooks.py`、`test_capabilities.py`、`test_review_step.py`。

## 重构备注
干净。`Playbook`/`PlaybookStep` 是数据，`PlaybookStore` 是机制 —— 保持两者可分离。
如果将来出现 DAG 形态的 playbook，`PlaybookStep` 会长出边，但 `find`/`validate`
的契约不变。
