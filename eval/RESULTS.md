# PR-review eval results

Model: DeepSeek v4 pro (all arms + judge). Metric: see README.md.

## PR #4678  (2 ground-truth issues)

| arm | findings | recall_GT | precision | **F1** | specificity | tokens | seconds |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.00 | 1.00 | **0.00** | 1.00 | 4,246 | 34 |
| copilot_skill | 0 | 0.00 | 0.00 | **0.00** | 0.00 | 31,550 | 50 |
| claudecode_skill | 3 | 0.00 | 1.00 | **0.00** | 1.00 | 490,291 | 202 |
| copilot_v2 | 7 | 0.25 | 0.86 | **0.39** | 1.00 | 922,479 | 792 |

Per-issue coverage: pure_copilot: gt1=0,gt2=0; copilot_skill: gt1=0,gt2=0; claudecode_skill: gt1=0,gt2=0; copilot_v2: gt1=0.5,gt2=0

## PR #4679  (4 ground-truth issues)

| arm | findings | recall_GT | precision | **F1** | specificity | tokens | seconds |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.12 | 1.00 | **0.22** | 0.50 | 19,173 | 76 |
| copilot_skill | 2 | 0.00 | 1.00 | **0.00** | 0.00 | 29,217 | 69 |
| claudecode_skill | 1 | 0.12 | 0.00 | **0.00** | 1.00 | 658,383 | 156 |
| copilot_v2 | 3 | 0.12 | 0.67 | **0.21** | 1.00 | 870,446 | 800 |

Per-issue coverage: pure_copilot: gt1=0.5,gt2=0,gt3=0,gt4=0; copilot_skill: gt1=0,gt2=0,gt3=0,gt4=0; claudecode_skill: gt1=0.5,gt2=0,gt3=0,gt4=0; copilot_v2: gt1=0.5,gt2=0,gt3=0,gt4=0

## PR #4849  (2 ground-truth issues)

| arm | findings | recall_GT | precision | **F1** | specificity | tokens | seconds |
|---|---|---|---|---|---|---|---|
| pure_copilot | 2 | 0.25 | 0.50 | **0.33** | 1.00 | 7,146 | 47 |
| copilot_skill | 1 | 0.25 | 1.00 | **0.40** | 1.00 | 13,941 | 76 |
| claudecode_skill | 2 | 0.25 | 1.00 | **0.40** | 1.00 | 764,975 | 187 |
| copilot_v2 | 3 | 0.25 | 1.00 | **0.40** | 1.00 | 423,099 | 714 |

Per-issue coverage: pure_copilot: gt1=0.5,gt2=0; copilot_skill: gt1=0.5,gt2=0; claudecode_skill: gt1=0.5,gt2=0; copilot_v2: gt1=0.5,gt2=0

## Aggregate (mean over PRs)

| arm | recall_GT | precision | **F1** | specificity | tokens | seconds |
|---|---|---|---|---|---|---|
| pure_copilot | 0.12 | 0.83 | **0.19** | 0.83 | 10,188 | 52 |
| copilot_skill | 0.08 | 0.67 | **0.13** | 0.33 | 24,903 | 65 |
| claudecode_skill | 0.12 | 0.67 | **0.13** | 1.00 | 637,883 | 182 |
| copilot_v2 | 0.21 | 0.84 | **0.33** | 1.00 | 738,675 | 769 |
