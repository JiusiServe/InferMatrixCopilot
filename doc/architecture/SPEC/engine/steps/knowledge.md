# engine/steps/knowledge.py —— 规范

<!-- verified-against: 2026-09-28 -->

`知识服务的 knowledge.* 步骤 · refactor-status: new`

## 职责
`kb-*` playbook 的薄步骤：`knowledge.collect_events`（risk read）、`knowledge.intake`
（agent，risk knowledge：起草类型化操作并运行质量门）、`knowledge.publish`（risk knowledge：
auto_merge 仓库写 outbox 的 `open_pr` 项，shadow 只记录）。逻辑全部在 `kb_service`。

## 不变量
- 只处理 `params.repo` 指定的一个仓库；未知或未启用的仓库 → BLOCKED。
- 步骤之间只经 `state_updates` 传递纯数据（`kb_repo`、`kb_changeset`、`kb_changeset_status`）。
- 从不直接写 GitHub；发布只经签名 outbox 由 GPU 盒发布器执行。

## 测试
`test_kb_intake_gate.py`。
