# 评测记录

**当前结论（2026-08-17）：Strict 评审在 recall 上落后 CC + Opus 5 基线约五个
rubric 点（Δrecall −.049 [−.097, −.001]），precision 打平（−.000），成本约为
基线的三分之一（$0.97 vs $3.09 每项）。**

这个数字来自预注册的 20 项测量。此前一次"优于基线"的宣称已被撤回——原始均值
支撑不了它。

## 边界：这里放什么

- **这里**（`doc/evaluation/`）：叙述性报告——一次战役做了什么、测出什么、
  该怎么读。**冻结**，各自停在自己的日期上。
- **[`eval/`](../../eval/README.md)**（顶层）：数据集、生成/判分脚本、arms、
  judgments、结果表。数字有出入时**以那边为准**，尤其是
  [`eval/dataset/results/model_comparison.md`](../../eval/dataset/results/model_comparison.md)。

结论摘要与方法论浓缩版在 [`GUIDE.md §8`](../GUIDE.md#8-性能对比)。

## 报告（新→旧）

| 报告 | 时间 | 结论 |
|---|---|---|
| [`EVAL-v14-v16-recall-campaign.md`](EVAL-v14-v16-recall-campaign.md) | 2026-08-15 | **最新**。召回攻坚：precision 打平，recall −.049，成本 1/3。附带三条会超出本战役的测量纪律 |
| [`EVAL-goal-strict-vs-opus5.md`](EVAL-goal-strict-vs-opus5.md) | 2026-08-13 | v7→v13：val 首胜 8—7，冻结 test 7—8，combined **15—15**。从"明显更差"走到"统计上无法区分" |
| [`EVAL-goal-report.md`](EVAL-goal-report.md) | 2026-07-20 | 早期一键 NL copilot vs CC+Opus 基线 |
| [`EVAL-PR20-report.md`](EVAL-PR20-report.md) | 2026-07-23 | 20 例 PR 评审全量重跑，含完整 trace |
| [`RESEARCH-reference-agents.md`](RESEARCH-reference-agents.md) | 2026-07-22 | 参考 agent 的机制调研（PR 评审与 issue 回答） |

## 读这些报告之前必须知道的三条

这三条是 v14→v16 战役用一次被撤回的结论换来的，且**超出该战役本身**：

1. **绝不拿一组 judgment 里 arm 的均值去比另一组里 baseline 的均值。**
   三组 wave-4 judgment 对**同一批**基线评审打分，基线 recall 均值分别是
   .335 / .338 / .416——±.08 的纯判官漂移，比所有被研究的效应都大。正确做法是
   在 verdict 内部配对（同一次判官调用同时给两个候选打分，宽严自然抵消）。
2. **同一个 item 的多个 replicate 不是独立观测。** 10 items × 3 replicates
   对 CI 来说是 n=10 而不是 n=30；当成 30 会把标准误低估约一倍。
3. **花掉 holdout 之前先算功效。** 在实测的 item 级 sd（.103–.127）下，分辨
   .05 的差异需要约 32–38 个 item。10-item 的门根本无法回答它被用来回答的问题。

配套的三道流程闸（2026-08-17 落地，每道对应一次真实事故）：manifest 记录
**解析后**的设置而非 env 字符串；余额预检**拒绝启动**而不是跑到一半死；
混合门覆盖 MoA 路径。
