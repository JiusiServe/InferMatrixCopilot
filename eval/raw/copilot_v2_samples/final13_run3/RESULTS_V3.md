# RQS v3 results

Metric: METRIC_V3.md (anchored-rubric multi-trial validity, decision correctness, arithmetic aggregate). Jury: ['deepseek-v4-pro', 'deepseek-v4-flash'] x 3 validity trials.

Validity reliability: validity_self kappa=0.34, validity_cross kappa=0.63

## PR #4678

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.25 | 1.00 | 0.50 | 0.0 (approve) | **0.44** | 4,246 |
| copilot_skill | 0 | 0.00 | 0.00 | 0.00 | 0.0 (approve) | **0.00** | 31,550 |
| claudecode_skill | 3 | 0.00 | 1.00 | 1.00 | 0.0 (approve) | **0.45** | 490,291 |
| claudecode_opus_skill | 1 | 0.00 | 1.00 | 0.00 | 0.0 (approve) | **0.25** | 398,757 |
| copilot_v2 | 2 | 0.00 | 1.00 | 1.00 | 1.0 (request_changes) | **0.65** | 1,113,425 |

## PR #4679

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.20 | 0.75 | 0.50 | 0.0 (approve) | **0.36** | 19,173 |
| copilot_skill | 2 | 0.10 | 1.00 | 0.00 | 0.5 (none) | **0.39** | 29,217 |
| claudecode_skill | 1 | 0.30 | 0.50 | 1.00 | 0.0 (approve) | **0.43** | 658,383 |
| claudecode_opus_skill | 2 | 0.30 | 0.42 | 0.50 | 0.0 (approve) | **0.31** | 4,340,800 |
| copilot_v2 | 2 | 0.10 | 0.92 | 1.00 | 1.0 (request_changes) | **0.66** | 756,962 |

## PR #4849

| arm | findings | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.00 | 0.67 | 0.50 | 0.0 (approve) | **0.27** | 7,146 |
| copilot_skill | 1 | 0.15 | 0.83 | 1.00 | 0.0 (approve) | **0.46** | 13,941 |
| claudecode_skill | 2 | 0.15 | 0.92 | 0.75 | 0.0 (approve) | **0.43** | 764,975 |
| claudecode_opus_skill | 2 | 0.00 | 1.00 | 1.00 | 0.0 (approve) | **0.45** | 704,305 |
| copilot_v2 | 1 | 0.30 | 1.00 | 1.00 | 1.0 (request_changes) | **0.76** | 279,201 |

## Aggregate (mean over PRs)

| arm | recall_w | precision | actionability | decision | **RQS3** | tokens |
|---|---|---|---|---|---|---|
| pure_copilot | 0.15 | 0.81 | 0.50 | 0.00 | **0.35** | 10,188 |
| copilot_skill | 0.08 | 0.61 | 0.33 | 0.17 | **0.28** | 24,903 |
| claudecode_skill | 0.15 | 0.81 | 0.92 | 0.00 | **0.44** | 637,883 |
| claudecode_opus_skill | 0.10 | 0.81 | 0.50 | 0.00 | **0.34** | 1,814,621 |
| copilot_v2 | 0.13 | 0.97 | 1.00 | 1.00 | **0.69** | 716,529 |

## Efficiency — RQS3e headline (cost/time folded in)

RQS3e = RQS3 x f($) x f(min), f(x) = 1/(1 + log10(1 + x/ref)); refs: $1.0/review, 10.0 min/review (env-overridable). Cost model: Opus arm = actual CLI-billed USD; DeepSeek arms = token estimate at $0.28/M in, $1.1/M out (cache-miss list rate — an upper bound). cost-of-quality = $/RQS3 point; frontier per Cost-of-Pass.

| arm | RQS3 | $/review | min/review | **RQS3e** | $-of-quality | min-of-quality | Pareto ($,RQS3) |
|---|---|---|---|---|---|---|---|
| pure_copilot | 0.35 | $0.01 | 0.9 | **0.34** | $0.01 | 2.5 | frontier |
| copilot_skill | 0.28 | $0.01 | 1.1 | **0.27** | $0.04 | 3.8 | dominated |
| claudecode_skill | 0.44 | $0.19 | 3.0 | **0.37** | $0.43 | 6.9 | frontier |
| claudecode_opus_skill | 0.34 | $3.20 | 5.5 | **0.17** | $9.50 | 16.3 | dominated |
| copilot_v2 | 0.69 | $0.25 | 4.9 | **0.54** | $0.36 | 7.2 | frontier |
