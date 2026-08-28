---
title: "发布规范"
created: 2026-08-28
updated: 2026-08-28
type: guide
tags: [vllm-omni, release]
sources: []
---

# 发布规范

vLLM-Omni 版本 **release 前**必须满足以下门禁。标注 `(Guide)` 的项按当期迭代指南解释与举证；其余为硬性门槛。
相关入口：[rules 索引](_index.md)、[CI](../ci/_index.md)、[DI 计算说明](../../../general/bug/guides/di-calculation.md)、[benchmark](../benchmark/_index.md)。

## Release 前门禁

| # | 要求 | 类型 | 说明 |
|---|---|---|---|
| 1 | UT coverage meets this iteration requirement | Guide | 单元测试覆盖率达到当期迭代要求；具体阈值与举证方式以当期 Guide 为准 |
| 2 | Performance regression < 10% | Guide | 性能回退小于 10%；对比基线、指标与证据口径以当期 Guide 为准 |
| 3 | Latest CUDA L1& L2 & L3 & L4 & L5 (excluding Non-critical) pass rate = 100% | Gate | 最新一轮 CUDA L1/L2/L3/L4/L5 中，排除 Non-critical 后通过率必须为 100% |
| 4 | Latest NPU L1 & L2 & L4 pass rate = 100% | Gate | 最新一轮 NPU L2/L4 通过率必须为 100% |
| 5 | Requirement completion rate > 85% | Gate | 需求完成率大于 85% |
| 6 | Remaining DI < 30 | Gate | 剩余 DI 小于 30；DI 计算见 [DI 计算说明](../../../general/bug/guides/di-calculation.md) |
| 7 | No remaining critical issues | Gate | 无未关闭的 critical 问题 |
| 8 | All remaining bugs have assignees | Gate | 所有剩余 bug 均已指派负责人 |

## 验收记录

发布前在发布说明或 checklist 中逐项给出：

- 是否通过（Pass / Fail / N/A）
- 证据链接（CI run、benchmark 报告、需求看板、DI 统计、issue 列表）
- Guide 项写明当期 Guide 版本或链接
