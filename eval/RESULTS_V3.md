# RQS v3 results

Metric: METRIC_V3.md (anchored-rubric multi-trial validity, decision correctness, arithmetic aggregate). Jury: ['deepseek-v4-pro', 'deepseek-v4-flash'] x 3 validity trials.

Validity reliability: validity_self kappa=0.23, validity_cross kappa=0.00

## PR #4678

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.25 | 1.00 | 0.50 | 0.0 (approve) | **0.44** | 4,246 |
| copilot_skill | 0 | 0.00 | 0.00 | 0.00 | 0.0 (approve) | **0.00** | 31,550 |
| claudecode_skill | 3 | 0.00 | 1.00 | 1.00 | 0.0 (approve) | **0.45** | 490,291 |
| claudecode_opus_skill | 1 | 0.00 | 1.00 | 0.00 | 0.0 (approve) | **0.25** | 398,757 |
| copilot_v2 | 7 | 0.38 | 0.57 | 0.93 | 0.0 (approve) | **0.46** | 922,479 |

## PR #4679

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.20 | 0.75 | 0.50 | 0.0 (approve) | **0.36** | 19,173 |
| copilot_skill | 2 | 0.10 | 0.42 | 0.00 | 0.5 (none) | **0.24** | 29,217 |
| claudecode_skill | 1 | 0.30 | 0.67 | 1.00 | 0.0 (approve) | **0.47** | 658,383 |
| claudecode_opus_skill | 2 | 0.30 | 0.33 | 0.50 | 0.0 (approve) | **0.29** | 4,340,800 |
| copilot_v2 | 3 | 0.20 | 0.72 | 0.83 | 1.0 (request_changes) | **0.62** | 870,446 |

## PR #4849

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.00 | 0.75 | 0.50 | 0.0 (approve) | **0.29** | 7,146 |
| copilot_skill | 1 | 0.15 | 0.83 | 1.00 | 0.0 (approve) | **0.46** | 13,941 |
| claudecode_skill | 2 | 0.15 | 1.00 | 0.75 | 0.0 (approve) | **0.45** | 764,975 |
| claudecode_opus_skill | 2 | 0.00 | 1.00 | 1.00 | 0.0 (approve) | **0.45** | 704,305 |
| copilot_v2 | 3 | 0.00 | 0.94 | 1.00 | 0.0 (approve) | **0.44** | 423,099 |

## Aggregate (mean over PRs)

| arm | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|
| pure_copilot | 0.15 | 0.83 | 0.50 | 0.00 | **0.36** | 10,188 |
| copilot_skill | 0.08 | 0.42 | 0.33 | 0.17 | **0.23** | 24,903 |
| claudecode_skill | 0.15 | 0.89 | 0.92 | 0.00 | **0.46** | 637,883 |
| claudecode_opus_skill | 0.10 | 0.78 | 0.50 | 0.00 | **0.33** | 1,814,621 |
| copilot_v2 | 0.19 | 0.75 | 0.92 | 0.33 | **0.50** | 738,675 |

## Efficiency (cost/time taken into the comparison)

Cost model: Opus arm = actual CLI-billed USD; DeepSeek arms = token estimate at $0.28/M in, $1.1/M out (cache-miss list rate — an upper bound). cost-of-quality = $/RQS3 point (lower is better); frontier per Cost-of-Pass.

| arm | RQS3 | $/review | min/review | $-of-quality | min-of-quality | Pareto ($,RQS3) |
|---|---|---|---|---|---|---|
| pure_copilot | 0.36 | $0.01 | 0.9 | $0.01 | 2.4 | frontier |
| copilot_skill | 0.23 | $0.01 | 1.1 | $0.04 | 4.6 | dominated |
| claudecode_skill | 0.46 | $0.19 | 3.0 | $0.41 | 6.6 | frontier |
| claudecode_opus_skill | 0.33 | $3.20 | 5.5 | $9.70 | 16.7 | dominated |
| copilot_v2 | 0.50 | $0.24 | 12.8 | $0.48 | 25.4 | frontier |
