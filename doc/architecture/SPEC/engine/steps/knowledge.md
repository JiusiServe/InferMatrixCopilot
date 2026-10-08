# engine/steps/knowledge.py —— 规范

<!-- verified-against: 2026-10-08 -->

`知识服务的 knowledge.* 步骤 · refactor-status: new`

## 职责
`kb-*` playbook 的薄步骤：`knowledge.collect_events`（risk read）、`knowledge.intake`
（agent，risk knowledge：起草类型化操作并运行质量门）、`knowledge.publish`（risk knowledge：
auto_merge 仓库写 outbox 的 `open_pr` 项，shadow 只记录）。逻辑全部在 `kb_service`。
运行对象优先从 `StepContext.runtime` 注入，未注入时按当前步骤参数创建；
不使用进程全局运行对象或状态目录缓存，资源不进入可序列化状态。

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
异步等待 `init_stages.run_stage_async`，通过公共执行入口运行拆分计划；
兼容步骤设置 `checkpoint=False`，外层完成标记不能跳过内层当前门禁。
`InitError`/`NotImplementedError` 与状态 `blocked`/`partial` 的记录都返回 BLOCKED。`state_updates`：
`kb_init_stage`、`kb_init_status`、`kb_init_pr`。它是本模块里唯一直接写 GitHub 的步骤：经仓库主人的 `gh` 开一个由人合并的
PR，且只在 `ALLOW_PUSH=1` 与 `ALLOW_POST=1` 同时成立、非 dry run、上游非私有时。测试：`test_kb_init_skeleton.py`。
同一模块注册 `knowledge.init.prepare/draft/validate/prepare_publication/publish`，
由 `init_execution.step_specs` 提供处理函数；`prepare` 和 `publish` 每次运行。
初始化资源仍使用独立 `InitRuntime`，不借用维护服务账本。

`pr-history` 阶段另接收可选 `pr_count` 与 `budget_usd`，转成整数/浮点后传入 `run_stage`；非法值返回 BLOCKED。
历史 PR 的完整选择、逐 PR checkpoint、commit 串和 Codex 审阅均由 `kb_service.init_history` 负责。

`knowledge-deepen` 另接收 `budget_usd` 与 `retry_unfinished`，逐功能保存七维实现知识、
累计预算与草稿。`from_existing` 允许 knowledge/knowledge-deepen 从已合并 KB 开始。
`unlimited_subscription` 显式传入两角色订阅无限模式；预算和语义完成门槛由同一 stage owner 处理。
`kb widen` / `kb deepen` 经同一 playbook/step 指定这两个知识阶段，旧规则 deepen 保持原契约。

## 2026-10-06 显式基础知识部分发布

`foundation_mode` 缺省 `strict`，未显式选择时不添加部分发布参数。
`partial` 只允许订阅无限的 `knowledge`，或带原始 `foundation_record` 的
`knowledge-deepen`；CLI 的 `--foundation-record` 经步骤转换为 `Path`，以
`foundation_record_path` 传给 `run_stage`。不兼容的阶段、缺失记录和非法模式由
stage 拒绝，步骤返回 BLOCKED，不能以参数缺失自动降级为部分发布。

`knowledge` 的显式部分发布只重放原批次的真实任务和独立评审，不追加模型调用，
不重置修正次数，也不改变生成身份。新深度批次将模式及原发布记录/收据哈希纳入
身份；七维认可门槛和完整目录分母保持不变。`published` 只表示 PR 已发布，
仍须单独保留 `init_complete=false`、六维基础知识缺口与结构覆盖结果。
原始 `blocked`/`partial` 状态仍返回 BLOCKED；不能把这些状态当作已完成。

证明与发布收据契约由 [`foundation_publication`](../../kb_service/foundation_publication.md)
负责，使用入口见[部分发布说明](../../../../knowledge/partial-foundation.md)。
接口测试：`test_kb_foundation_partial_interfaces.py`；原生证明和门槛测试：
`test_kb_foundation_explicit_partial.py`。
