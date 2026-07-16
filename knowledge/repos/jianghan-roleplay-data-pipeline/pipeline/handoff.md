# Jianghan 当前交接与远端卫生

## 当前交接状态

Stage3 narrative seed：

```text
file: data/role/jianghan_narrative_review_seed_v1.jsonl
rows: 6
status: review proposals only
source_kind: original_novel_evidence_manual_proposal
review_score: null
```

audit：

```text
file: data/role/jianghan_narrative_review_seed_v1_audit.json
row_count: 6
output_length_min: 239
output_length_median: 309
<=12_chars_ratio: 0
<=20_chars_ratio: 0
generic_reply_count: 0
hard_stop: none
```

promoted train：

```text
file: data/train/jianghan_stage3_narrative_seed_v1.chat.jsonl
rows: 0
reason: no user review scores have been applied yet
```

零行是正确状态：未审阅的行不能进训练。

下一步：

1. 让用户审 `data/role/jianghan_narrative_review_seed_v1.compact.md`。
2. 用 `0001=2,0002=1,0003=0` 形式打分。
3. `review_score = 2` 才能默认 promote 成 gold。
4. 继续构建更大的 original-novel-only Stage3 candidate set。
5. 重新 audit，无 hard stop 后才训练。

## 远端卫生

远端项目文件必须留在用户批准的项目目录下，不要散到 `/root` 或 filesystem root。

远端训练前确认：

```text
review artifacts
train data
eval data
audit report
complete Qwen/Qwen3.5-4B snapshot
```

缺完整 Qwen3.5-4B 权重时，不能用 Qwen2.5 或别的模型代替做质量结论。
