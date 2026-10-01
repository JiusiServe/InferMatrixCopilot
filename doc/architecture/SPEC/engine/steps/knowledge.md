# engine/steps/knowledge.py —— 规范

<!-- verified-against: 2026-10-01 -->

`知识服务的 knowledge.* 步骤 · refactor-status: new`

## 职责
`kb-*` playbook 的薄步骤：`knowledge.collect_events`（risk read）、`knowledge.intake`
（agent，risk knowledge：起草类型化操作并运行质量门）、`knowledge.publish`（risk knowledge：
auto_merge 仓库写 outbox 的 `open_pr` 项，shadow 只记录）。逻辑全部在 `kb_service`。

## 不变量
- 只处理 `params.repo` 指定的一个仓库；未知或未启用的仓库 → BLOCKED。
- 步骤之间只经 `state_updates` 传递纯数据（`kb_repo`、`kb_changeset`、`kb_changeset_status`）。
- 从不直接写 GitHub；发布只经签名 outbox 由 GPU 盒发布器执行（唯一例外：`knowledge.init`，见下）。

## 测试
`test_kb_intake_gate.py`。

## 2026-09-28 合并、巡检、激活步骤
新增 `knowledge.advance_merges`、`knowledge.sweep`、`knowledge.activate`；`kb run` 路径自行持有租约，调度器路径复用其租约。

## 2026-09-30 `knowledge.init`（kb init）
参数 `repo`、`stage`、`dry_run`（缺省 true）、`pin`。用自己的 `InitRuntime`（`kb_service/init_support.py`），**不**经
`_runtime`/`_lifecycle`：服务运行时会打开 `kb.db`，且 `_lifecycle` 拒绝未启用的仓库，而为未启用的仓库建库正是 init 的目的。
调 `init_stages.run_stage`；`InitError`/`NotImplementedError` 与状态 `blocked` 的记录都返回 BLOCKED。`state_updates`：
`kb_init_stage`、`kb_init_status`、`kb_init_pr`。它是本模块里唯一直接写 GitHub 的步骤：经仓库主人的 `gh` 开一个由人合并的
PR，且只在 `ALLOW_PUSH=1` 与 `ALLOW_POST=1` 同时成立、非 dry run、上游非私有时。测试：`test_kb_init_skeleton.py`。

`pr-history` 阶段另接收可选 `pr_count` 与 `budget_usd`，转成整数/浮点后传入 `run_stage`；非法值返回 BLOCKED。
历史 PR 的完整选择、逐 PR checkpoint、commit 串和 Codex 审阅均由 `kb_service.init_history` 负责。
