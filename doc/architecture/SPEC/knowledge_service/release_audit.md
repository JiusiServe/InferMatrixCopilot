# knowledge_service/release_audit.py —— 规范

<!-- verified-against: 2026-09-28 -->

`LOC ~120 · 仓库中立的发版审计插件契约 · refactor-status: stable`

## 职责
加载仓库 adapter 目录下的发版审计插件（随 wheel 打包的运行时数据）并调用其
`audit_for_knowledge(*, upstream_repo, from_ref, to_ref, knowledge_root, project_root)`，
返回 `ReleaseAuditResult`（`issues` 强制、`reconciliation` 仅报告、`generated_baseline`、
审计的 SHA 对）。插件以 generated-baseline 模式运行，知识变更不必等待 adapter 基线推进。

## 不变量
- 插件路径必须是 adapter 目录内的 `.py` 相对路径；绝对路径、`..`、逃逸与缺失均抛
  `ReleaseAuditPluginError`；缺少入口函数或返回格式不符同样报错。
- 模块中不出现任何仓库名；没有插件的仓库由 L1 的通用引用存在性检查兜底。

## 测试
`test_release_audit.py`（generated 模式不因未推进的已提交基线阻塞、知识修复后 clean、
未路由路径进入 reconciliation、CLI 两种模式、插件加载与路径拒绝）。
