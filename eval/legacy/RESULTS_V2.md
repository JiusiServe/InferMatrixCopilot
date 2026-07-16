# RQS v2 results

Metric: METRIC_V2.md. Jury: ['deepseek-v4-pro', 'deepseek-v4-flash'] (same family — all arms share one generator model, so judge-family bias shifts levels, not the arm ranking). Claims model: deepseek-v4-flash.

Inter-judge agreement (Cohen's kappa, pooled): validity=0.02, action=0.74, align=0.48

## PR #4678

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.25 | 1.00 | 0.50 | 0.00 | 0.00 | **0.43** | 4,246 |
| copilot_skill | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **0.00** | 31,550 |
| claudecode_skill | 3 | 0.00 | 0.83 | 1.00 | 0.11 | 0.33 | **0.00** | 490,291 |
| claudecode_opus_skill | 1 | 0.00 | 1.00 | 0.00 | 0.14 | 1.00 | **0.00** | 398,757 |
| copilot_v2 | 5 | 0.12 | 0.90 | 1.00 | 0.00 | 0.00 | **0.30** | 987,538 |

Weighted coverage: pure_copilot: gt1=0.5,gt2=0; copilot_skill: gt1=0,gt2=0; claudecode_skill: gt1=0,gt2=0; claudecode_opus_skill: gt1=0,gt2=0; copilot_v2: gt1=0.25,gt2=0

## PR #4679

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.20 | 0.75 | 0.50 | 0.11 | 0.50 | **0.36** | 19,173 |
| copilot_skill | 2 | 0.10 | 1.00 | 0.00 | 0.46 | 1.00 | **0.00** | 29,217 |
| claudecode_skill | 1 | 0.30 | 0.50 | 1.00 | 0.07 | 1.00 | **0.47** | 658,383 |
| claudecode_opus_skill | 2 | 0.30 | 0.50 | 0.50 | 0.00 | 0.00 | **0.41** | 4,340,800 |
| copilot_v2 | 3 | 0.20 | 0.67 | 1.00 | 0.14 | 0.50 | **0.40** | 1,006,569 |

Weighted coverage: pure_copilot: gt1=0.5,gt2=0,gt3=0,gt4=0; copilot_skill: gt1=0.25,gt2=0,gt3=0,gt4=0; claudecode_skill: gt1=0.75,gt2=0,gt3=0,gt4=0; claudecode_opus_skill: gt1=0.75,gt2=0,gt3=0,gt4=0; copilot_v2: gt1=0.5,gt2=0,gt3=0,gt4=0

## PR #4849

| arm | findings | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.00 | 0.75 | 0.50 | 0.00 | 0.00 | **0.00** | 7,146 |
| copilot_skill | 1 | 0.15 | 0.50 | 1.00 | 0.08 | 1.00 | **0.31** | 13,941 |
| claudecode_skill | 2 | 0.15 | 0.75 | 0.75 | 0.17 | 1.00 | **0.32** | 764,975 |
| claudecode_opus_skill | 2 | 0.00 | 1.00 | 1.00 | 0.17 | 1.00 | **0.00** | 704,305 |
| copilot_v2 | 3 | 0.30 | 1.00 | 1.00 | 0.21 | 0.50 | **0.56** | 388,286 |

Weighted coverage: pure_copilot: gt1=0,gt2=0; copilot_skill: gt1=0.25,gt2=0; claudecode_skill: gt1=0.25,gt2=0; claudecode_opus_skill: gt1=0,gt2=0; copilot_v2: gt1=0.5,gt2=0

## Aggregate (mean over PRs)

| arm | recall_w | precision | actionability | comprehensiveness | conciseness | **RQS** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.04 | 0.17 | **0.26** | 10,188 |
| copilot_skill | 0.08 | 0.50 | 0.33 | 0.18 | 0.67 | **0.10** | 24,903 |
| claudecode_skill | 0.15 | 0.69 | 0.92 | 0.12 | 0.78 | **0.27** | 637,883 |
| claudecode_opus_skill | 0.10 | 0.83 | 0.50 | 0.10 | 0.67 | **0.14** | 1,814,621 |
| copilot_v2 | 0.21 | 0.86 | 1.00 | 0.12 | 0.33 | **0.42** | 794,131 |
