# 2026-07-10 — 依赖命令被并行跑

- 编号：`inc-2026-07-10-jianghan-pipeline-06`
- 归属：`repos/jianghan-roleplay-data-pipeline/pipeline`
- 状态：已提炼
- 搜索词：依赖命令被并行跑
- 影响范围：Jianghan 数据管线

曾经把 promote smoke 和 score-apply 并行，consumer 先跑导致输入不存在。

规则：只有独立读/独立检查可以并行；producer -> consumer 必须顺序执行。
