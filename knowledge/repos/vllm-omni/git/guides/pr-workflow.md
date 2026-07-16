# PR Workflow 入口

本文件只保留路由。提交、push、PR body 或 reviewer follow-up 前，按场景打开对应专题页。

| 场景 | 读这个 |
|------|--------|
| 主仓/worktree 边界、自动 push、查 head branch、rebase 后 semantic audit | [branch_push_rebase.md](branch-push-rebase.md) |
| PR still not fixed、已测过仍有 bug、official 对齐测试踩坑 | [debugging_and_tests.md](debugging-and-tests.md) |
| PR 模板、渲染级验收、公开复现结构 | [pr_body_evidence.md](pr-body-evidence.md) |
| PR 性能/精度/图片证据、head/run/artifact provenance | [pr_body_provenance.md](pr-body-provenance.md) |
| 新模型 PR 的 source parity / stub smoke / real checkpoint 证据分层 | [pr_body_model_evidence.md](pr-body-model-evidence.md) |
| 公开 PR body/comment 隐私边界、远端/本地路径脱敏 | [pr_body_privacy.md](pr-body-privacy.md) |
| Reviewer 要求收窄 scope、废弃路线删除、diff gate | [scope_narrowing.md](scope-narrowing.md) |
| 多 PR / stacked PR / release-candidate 集成合入、superseded PR、ready 前 stale 状态审计 | [integration_pr_merge_vehicle.md](integration-pr-merge-vehicle.md) |

硬规则摘要：

- 框架代码主仓保持 `main`，业务修改进 `wt-*` worktree。
- 推送前查真实 PR head branch，不自造分支。
- PR body/comment 的性能、精度、图片证据必须绑定 head SHA、run SHA 和 artifact provenance。
- PR body/comment 只能写 reviewer-facing 可复现证据；禁止写本地用户路径、远端路径、venv/cache 路径、host/port、机器别名或内部探针噪音。
- 多 PR / stacked PR 先选唯一 merge vehicle；选 integration PR 后，窄 PR 只能作为历史切片，ready 前清 stale draft/WIP wording，合后 comment + close superseded PR。
- Reviewer follow-up 小修复走快速通道，但仍要最小 edit、targeted test/说明 blocker、ruff touched files、`commit -s`。
