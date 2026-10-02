# knowledge_service/ops.py —— 规范

<!-- verified-against: 2026-10-02 -->

`LOC ~360 · Knowledge Ops API 2.0（类型化知识变更） · refactor-status: stable`

## 职责
`apply_operations(files, ops, release, today)` 是纯函数：输入知识相对路径到文本的映射与
类型化操作（`add`、`edit_same_meaning`、`replace`、`retire`、`purge`），输出变更后的文件。
随后写入机械结果：`updated:`、只追加的 `sources:`、新页面在同目录 `_index.md` 的一行、
purge 的 `_tombstones.yaml` 条目。
新规则页的 tags 继承同目录 owner `_index.md`，缺少时再使用同目录 canonical `rules.md`；
已有页保留原 tags。继承数据非法则拒绝，不发明分类；服务与发布器使用同一纯函数重建。

## 不变量
- 新 ID（含嵌套 `###`）在全树唯一，且不在 tombstones 中。
- `replace` 在一次调用内同时退役旧规则（`reason=superseded`、`superseded_by`）并添加带
  `supersedes` 的后继规则。
- `purge` 只针对已退役且 `retired_at` 不是本次发版的规则。
- `protected` 规则需 `allow_protected`（人工路径）。
- 超过拆分线（32 KiB / 500 非空行）的页面被拒绝，提示改用新的 `rules-<topic>.md`。
- 任何非法操作抛 `LifecycleError`，输入映射从不被修改（无部分应用）。
- 版本常量 `KNOWLEDGE_OPS_API_VERSION = 2.0.0`，与 v1 `KnowledgeCurator`（1.1.0）并存。

## 依赖（允许）
标准库 + PyYAML + `lifecycle`（验证包原样携带）。

## 测试
`test_knowledge_ops_l1.py`。
