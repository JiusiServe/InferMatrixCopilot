# RQS v2 results

Metric: METRIC_V2.md. Jury: ['deepseek-v4-pro', 'deepseek-v4-flash'] (same family — all arms share one generator model, so judge-family bias shifts levels, not the arm ranking). Claims model: deepseek-v4-flash.

Inter-judge agreement (Cohen's kappa, pooled): validity=0.23, action=0.65, align=0.44

## PR #4678

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_skill | 1 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | **0.00** | 101,508 |
| pure_copilot | 2 | 0.25 | 1.00 | 0.50 | 0.00 | 0.00 | **0.43** | 4,246 |
| copilot_skill | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | 31,550 |

Weighted coverage: pure_skill: gt1=0,gt2=0; pure_copilot: gt1=0.5,gt2=0; copilot_skill: gt1=0,gt2=0

## PR #4679

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_skill | 1 | 0.00 | 1.00 | 1.00 | 0.04 | 0.50 | **0.00** | 163,116 |
| pure_copilot | 2 | 0.20 | 0.75 | 0.50 | 0.11 | 0.50 | **0.36** | 19,173 |
| copilot_skill | 2 | 0.10 | 1.00 | 0.00 | 0.46 | 1.00 | **0.00** | 29,217 |

Weighted coverage: pure_skill: gt1=0,gt2=0,gt3=0,gt4=0; pure_copilot: gt1=0.5,gt2=0,gt3=0,gt4=0; copilot_skill: gt1=0.25,gt2=0,gt3=0,gt4=0

## PR #4849

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_skill | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | 39,736 |
| pure_copilot | 2 | 0.00 | 0.75 | 0.50 | 0.00 | 0.00 | **0.00** | 7,146 |
| copilot_skill | 1 | 0.15 | 0.50 | 1.00 | 0.08 | 1.00 | **0.31** | 13,941 |

Weighted coverage: pure_skill: gt1=0,gt2=0; pure_copilot: gt1=0,gt2=0; copilot_skill: gt1=0.25,gt2=0

## Aggregate (mean over PRs)

| arm | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|
| pure_skill | 0.00 | 0.33 | 0.67 | 0.01 | 0.17 | **0.00** | 101,453 |
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.04 | 0.17 | **0.26** | 10,188 |
| copilot_skill | 0.08 | 0.50 | 0.33 | 0.18 | 0.67 | **0.10** | 24,903 |
