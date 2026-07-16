# 2026-07-10 — Reference quality 被误当成 training suitability

- 编号：`inc-2026-07-10-jianghan-pipeline-02`
- 归属：`repos/jianghan-roleplay-data-pipeline/pipeline`
- 状态：已提炼
- 搜索词：Reference quality 被误当成 training suitability
- 影响范围：Jianghan 数据管线

SillyTavern/worldbook prompt 运行时表现好，是因为 inference context 大，不代表它的生成回复能做 fine-tune gold。

区分：

```text
good reference != training gold
```
