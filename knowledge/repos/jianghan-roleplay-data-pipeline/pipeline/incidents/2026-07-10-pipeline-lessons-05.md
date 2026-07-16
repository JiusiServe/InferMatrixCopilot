# 2026-07-10 — Training 早于 review gates

- 编号：`inc-2026-07-10-jianghan-pipeline-05`
- 归属：`repos/jianghan-roleplay-data-pipeline/pipeline`
- 状态：已提炼
- 搜索词：Training 早于 review gates
- 影响范围：Jianghan 数据管线

训练前必须已存在：

```text
source policy documented
candidate JSONL
review markdown
review scores or explicit owner acceptance
promoted train JSONL non-empty
audit JSON/MD without hard stop
stage-matched eval JSONL
```

缺一个都不能“先训看看”。
