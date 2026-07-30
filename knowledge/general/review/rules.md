---
title: "通用设计审查规则"
created: 2026-07-30
updated: 2026-07-30
type: rule
tags: [general, review]
sources: ["InferMatrixCopilot Issue #17", "vllm-project/vllm-omni PR #5394"]
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

具体审查执行顺序见[独立审查执行合同](guides/review-execution-contract.md)，输入、输出与
边界矩阵写法见[Reviewer Lens Contracts](guides/reviewer-lens-contracts.md)。
