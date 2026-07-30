---
title: "通用设计审查规则"
created: 2026-07-30
updated: 2026-07-30
type: rule
tags: [general, review]
sources: ["InferMatrixCopilot Issue #17", "InferMatrixCopilot Issue #24", "vllm-project/vllm-omni PR #5394", "zuiho-kai/claude-workflow-starter@c217fc6"]
confidence: high
---

# 通用设计审查规则

本页只放跨仓库都成立、能由代码结构触发的设计门禁。仓库、组件和模型专有不变量仍由
最近的 owner 规则负责。

## 同族实现覆盖

### REV-1a — 修改同族实现时先闭合同族集合

- 触发：改动共享同一公开合同、注册入口、基类或命名族的一部分实现，例如同目录的
  `pipeline_*`、同类 adapter/backend 或同一功能的多种输入模式。
- 强制：先从注册表、factory、基类或调用方枚举真实同族；逐项标记“同步修改”、
  “无需修改及原因”或“独立 owner”，再检查共享逻辑是否应上提到共同 owner。
- 禁止：只按 changed files 或当前调用路径收口；把目录相邻直接当成同族证据；用一个
  变体的绿测证明其他变体不受影响。
- 验收：审查记录包含完整同族清单和逐项结论；至少验证一个已修改变体，并对每个未修改
  变体提供代码边界、合同差异或最小回归证据。 ^[vllm-project/vllm-omni PR #5394]

## 条件分支对称

### REV-1b — 同一语义的条件分支必须证明分叉必要且合同对称

- 触发：同一职责按 TP size、设备、dtype、backend、feature flag 或兼容模式选择不同
  实现。
- 强制：写明为何不能共用一条实现，并逐项比较两边的输入、输出、状态、错误语义和
  下游 consumer；能够统一时删除分叉，不能统一时把差异固化为显式合同。
- 禁止：让默认配置或常用分支掩盖另一条路径；只测各分支“能运行”；用实现不同倒推
  语义必然不同。
- 验收：同一入口覆盖条件边界两侧及切换边界，断言用户可观察结果或明确允许的差异；
  新增共享行为时，两条路径的测试或不适用理由必须同时出现。 ^[vllm-project/vllm-omni PR #5394]

## 审查角色与减法

### REV-2a — 一次 Direct 审查必须同时完成 correctness 与 design/subtraction

- 触发：用户要求审核 PR，包括只提供 PR 链接；或交付前审查发现新增 public behavior、
  owner、abstraction、兼容路径或跨模块数据流。
- 强制：冻结 base/head 和授权合同；一次获取 PR 描述、changed files、diff、caller、
  tests 与已有 findings，并把精确 owner/model 规则组加入同一个 Codex review。主审查
  同时追行为和 producer→consumer，并完成项目级与模块级减法。
- 禁止：为 correctness 和 subtraction 各跑一篇通用审查；让不同 reviewer 重复读取
  同一文件、搜索 caller 或运行同一测试；分别发布多篇 review comment。
- 验收：一份内部报告覆盖 correctness 与 subtraction，一篇对外评论给出合并后的
  findings 和 verdict；任一维度缺失只能报 `partial review`。 ^[InferMatrixCopilot Issue #24]

### REV-2b — 减法先删越界 scope，再压缩模块设计

- 触发：PR 新增 production behavior、文件、测试、helper、class、normalizer、validator、
  allowlist、owner projection、中间 artifact 或末端补偿。
- 强制：先把每项变化映射到用户目标或当前 RFC/mini spec slice，未映射项
  `DELETE / DEFER`；再枚举保留 abstraction，写出不依赖当前实现的最小 owner 设计，
  逐项标记 `KEEP / INLINE / MERGE / MOVE / DELETE`，优先最小修改和复用既有 owner。
- 禁止：把字段丢失、默认值错误等 correctness bug 算作减法；用删局部变量、改名、
  换文件或多 caller 证明设计已经最简；让后续 RFC slice 因为已写完而混入当前 PR。
- 验收：报告先给 scope 删除项，再给模块 abstraction/owner/分支的净减少；没有可删项时，
  必须用完整 scope ledger、census 和最小设计证明当前已经最小。
  ^[zuiho-kai/claude-workflow-starter@c217fc6]

### REV-2c — 交互式 PR review 必须按时返回最小可用结论

- 触发：用户未指定深审或更长预算，只要求审核 PR。
- 强制：默认端到端预算 10 分钟；主审查先完成合并/CI/diff 快速检查并复用同一证据包。
  只有新颖、矛盾或未覆盖的高风险合同才允许在剩余预算内追加有边界的专项追问；截止时
  停止新工具调用，返回当前 finding、减法账本和未验证边界。
- 禁止：为了补齐外围 CI、全量测试、历史 thread 或额外专项无限延长；在 reviewer 已超时
  后继续无上限等待“完整结果”。
- 验收：10 分钟内给用户 actionable findings 或明确的 `partial review`；更深验证作为
  后续可选任务，不阻塞本轮答复。 ^[InferMatrixCopilot Issue #24]

具体审查执行顺序见[独立审查执行合同](guides/review-execution-contract.md)，输入、输出与
边界矩阵写法见[Reviewer Lens Contracts](guides/reviewer-lens-contracts.md)。
