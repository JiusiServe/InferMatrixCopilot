# 2026-07-10 — 原文高可信被误当成原样可训练

- 编号：`inc-2026-07-10-jianghan-pipeline-03`
- 归属：`repos/jianghan-roleplay-data-pipeline/pipeline`
- 状态：已提炼
- 搜索词：原文高可信被误当成原样可训练
- 影响范围：Jianghan 数据管线

Stage3 v1 把原文场景压成“江涵下一句直接台词”，出现大量 `嗯……`、`吃。`、`好的。`。这些在小说里有上下文支撑，单独训练会教模型安全短答和低主动性。

正确转换：

```text
原文 evidence -> mechanism / reaction_intent -> complete narrative target
```
