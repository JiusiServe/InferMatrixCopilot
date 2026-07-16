# 2026-07-10 — 用户纠偏没有立刻升级成硬约束

- 编号：`inc-2026-07-10-jianghan-pipeline-01`
- 归属：`repos/jianghan-roleplay-data-pipeline/pipeline`
- 状态：已提炼
- 搜索词：用户纠偏没有立刻升级成硬约束
- 影响范围：Jianghan 数据管线

用户多次否定 CoSER、Top100、生成样本、短回复 target 后，旧路线仍反复回流。

以后强用户纠偏后必须写五行当前路线：

```text
Current route:
Stage:
Allowed sources:
Forbidden sources:
Output shape:
Review gate:
```

写不清就不能继续实现。
