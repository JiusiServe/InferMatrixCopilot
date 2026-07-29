---
title: "Config normalization parity"
created: 2026-07-23
updated: 2026-07-23
type: guide
tags: [vllm-omni, dev, config]
sources: ["claude-workflow-starter-private@e423b8d"]
---

# Config normalization parity

## 什么时候用

实现 [配置开发门禁](../rules.md) 时使用。本页只说明怎样收集最小证据，不扩大审查范围。
字段所有权的解释方法见 [config audit](config-audit-plain-language.md)，stage runtime 的严格
配置约束见 [Model Executor 规则](../../components/model-executor/rules.md)。

## 先写最小矩阵

只填写当前 diff 会改变的行，再加一个默认或相邻 control。入口、值状态和检查点是候选维度，不要求全部组合：

| 入口 | 本轮相关值状态 | 实际对象与 copy 边界 | 第一位 consumer | 最终 consumer | 期望 |
|---|---|---|---|---|---|
| deploy、`engine_extras`、nested config、CLI/runtime、direct factory 或默认 fallback 中受影响的一条 | 缺失、`null`、非默认值、冲突值或可转换标量中会改变分支的一项 | 哪个 dict/config 被原地修改，哪里复制 | preflight、validator 或 dispatcher | final config 或 worker | 保留值、派生值或错误 |
| 默认或相邻 control | 未受影响值 | 同上 | 同上 | 同上 | 行为不变 |

## 执行顺序

1. 先搜索 changed field 的现有字段集合、精确 schema 测试、constructor/factory 和 legacy/direct 入口。
2. 从入口追到第一位 consumer，记录每次 merge、copy、flat→nested 和类型转换；不要从最终 config 反推上游已经正确。
3. 在最早的共同边界实现归一化。ownership 校验先看 key 是否已知，再决定已知 `None` 是否丢弃；未知 `None` 仍按 strict contract 处理。
4. 回归测试至少穿过本轮真实入口和第一位 consumer，并再断言最终 config。helper 测试可以精确覆盖分支，但不能单独作为生产路径证据。
5. public dataclass/config schema 发生变化前，先检查现有精确字段集合、序列化和兼容测试。
6. 最后一次修改后实跑目标测试文件；本机缺 `vllm` 时立即切到已验证远端或 CI-like 环境，不能用 lint/compile 代替。
