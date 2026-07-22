# PR Review Offline Evaluation v0.1

This package implements the versioned PR Review Metrics v0.1 design as a new,
self-contained evaluator. It does not import or reuse the legacy scripts directly
under `eval/`.

## Implemented pipeline

```text
GitHub historical data (benchmark build only)
  -> frozen benchmark item + private evidence
  -> fixed-SHA isolated read-only repository snapshot
  -> AgentAdapter + bounded static tools
  -> strict structured-output validation / one format repair
  -> candidate generation
  -> position-swapped multi-judge jury and evidence-enhanced round 2
  -> global one-to-one matching
  -> per-PR and benchmark metrics
  -> Markdown / JSON / repeated-run reports
```

The evaluator does not execute tests, compile code, import the target project, or
require vLLM/vLLM-Omni dependencies.

## Trust boundaries

- Benchmark GT, historical review data, and judge outputs are stored outside the
  snapshot and are never projected into `AgentInput`.
- The snapshot fetches only objects reachable from the authorized `base_sha` and
  `head_sha`; Review-after commits are absent from its object database. It is
  detached at `head_sha` and has write bits removed.
- `StaticToolExecutor` exposes only bounded file reads, directory listing, text
  search, and approved read-only Git subcommands. Refused attempts are recorded as
  policy violations.
- Network isolation must be applied to the process/container hosting a real model
  adapter. The Python evaluator deliberately does not claim that an in-process,
  trusted adapter is an OS security boundary.
- GitHub access exists only in `benchmark/builder`; an evaluation run uses a local
  bare repository cache and frozen artifacts.

## Contracts

- Benchmark item: `pr-review-item-v0.1`
- Agent input: `pr-review-input-v0.1`
- Agent output: `pr-review-output-v0.1`
- Rubric: `rubrics/pr-review-v0.1.yaml`
- Findings per PR: at most 20
- Verdicts: `APPROVE`, `REQUEST_CHANGES`
- Final statuses: `MATCHED_GT`, `VALID_PARTIAL`, `VALID_NEW`,
  `FALSE_POSITIVE`, `DUPLICATE`, `UNVERIFIABLE`

Unknown fields are rejected. Invalid JSON receives at most one deterministic,
semantics-preserving format repair. A second failure becomes
`OUTPUT_CONTRACT_FAILURE`.

## CLI

Run commands from the repository root.

```bash
# Build high-confidence buggy candidates from GitHub history.
# Judge plugins use module:object and implement JudgeBackend.
python -m eval.tasks.pr_review benchmark build \
  --repo vllm-project/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --judge my_eval_plugins:judge_a \
  --judge my_eval_plugins:judge_b \
  --judge my_eval_plugins:judge_c \
  --output eval-data/pr-review-v0.1

python -m eval.tasks.pr_review benchmark validate \
  --manifest eval-data/pr-review-v0.1/manifest.yaml

# Agent plugins implement AgentAdapter.
python -m eval.tasks.pr_review run \
  --manifest eval-data/pr-review-v0.1/manifest.yaml \
  --repository-cache ~/.cache/omni-copilot/repos \
  --adapter my_eval_plugins:review_agent \
  --output runs/reviewer-v1-run1

python -m eval.tasks.pr_review adjudicate \
  --manifest eval-data/pr-review-v0.1/manifest.yaml \
  --run-dir runs/reviewer-v1-run1 \
  --repository-cache ~/.cache/omni-copilot/repos \
  --judge my_eval_plugins:judge_a \
  --judge my_eval_plugins:judge_b \
  --judge my_eval_plugins:judge_c

python -m eval.tasks.pr_review score \
  --manifest eval-data/pr-review-v0.1/manifest.yaml \
  --run-dir runs/reviewer-v1-run1 \
  --output reports/reviewer-v1-run1

# Compare complete run bundles. VALID_NEW on a clean PR invalidates that PR
# globally for both arms before either score is computed.
python -m eval.tasks.pr_review compare \
  --manifest eval-data/pr-review-v0.1/manifest.yaml \
  --baseline-run runs/reviewer-v1 \
  --candidate-run runs/reviewer-v2 \
  --output reports/v1-v2

# Comparing already-scored summaries remains available when no campaign-level
# invalidation is needed.
python -m eval.tasks.pr_review compare \
  --baseline-summary reports/baseline/summary.json \
  --candidate-summary reports/candidate/summary.json \
  --output reports/compare.md

# Formal repeated-run statistics: mean, sample standard deviation, raw runs,
# and optional per-PR distributions.
python -m eval.tasks.pr_review replicates \
  --summary reports/run1/summary.json \
  --summary reports/run2/summary.json \
  --summary reports/run3/summary.json \
  --per-pr reports/run1/per_pr.json \
  --per-pr reports/run2/per_pr.json \
  --per-pr reports/run3/per_pr.json \
  --output reports/formal-replicates.json
```


## Evaluated-agent experiment arms

The evaluator now includes concrete, versioned subject adapters in
`eval/tasks/pr_review/subjects/` rather than only the `AgentAdapter` protocol.
The default experiment matrix compares the same model and frozen benchmark in
three conditions:

1. `copilot`: the real `agent.review_diff` product step, including the current
   Copilot profile, knowledge, builtin skills, adaptive depth, and ensemble.
2. `copilot_with_skill`: the same Copilot path plus the pinned external
   `vllm-omni-review/SKILL.md`.
3. `skill_only`: the generic model tool loop with only that external Skill as
   review guidance; no Copilot planner, ensemble, profile, or builtin skills.

All three arms receive the same public PR input and the same evaluator-owned
read-only repository tools. The Copilot step's normal live GitHub tools are
replaced by these static tools only during evaluation. The external Skill's
instructions to use GitHub, execute tests, access hardware, or post comments are
overridden by the offline benchmark policy.

The exact Skill snapshot is frozen under
`eval/resources/skills/vllm-omni-review/` with repository ref, Git blob SHA, and
SHA-256 provenance.

```bash
# Install the product package and development dependencies first.
python -m pip install -e '.[dev]'

# Populate the local bare cache from a checkout that contains every benchmark SHA.
python -m eval.tasks.pr_review repository import-local \
  --repo vllm-project/vllm-omni \
  --source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos

# One repetition per arm (candidate generation).
python -m eval.tasks.pr_review run-matrix \
  --matrix eval/configs/pr_review/experiments/three-arms-smoke.yaml \
  --manifest eval/data/pr_review/benchmarks/pr-review-pilot-v0.1.0-dev/manifest.yaml \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review

# One-command equivalent. Add --formal for three repetitions.
python eval/scripts/pr_review/run_three_arms.py \
  --repository-source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review
```

`ANTHROPIC_API_KEY` is required. `ANTHROPIC_BASE_URL` may point to any
Anthropic-SDK-compatible endpoint supported by the Copilot. The three arm YAML
files deliberately leave `model` empty, so all arms use the same process-level
model setting. Pin `model` explicitly in all three files for a formal campaign.

Candidate generation alone is not a complete metric run. Valid Finding
Precision and matching-dependent recall require independent `JudgeBackend`
plugins. The one-command script completes adjudication and scoring when the same
`--judge module:object` options are supplied. `score-matrix` scores every arm and
replicate in one campaign so clean-PR invalidation is globally consistent.

## Plugin contracts

An `AgentAdapter` has a `version` and a `review(...) -> str` method. The raw return
value must satisfy the output contract. Model usage and tool calls are written to
`TraceCollector`:

```python
trace.record(
    "model_usage",
    input_tokens=100,
    output_tokens=20,
    cached_tokens=0,
)
```

A `JudgeBackend` has stable `judge_id` and `model_family` values and returns a
`JudgeVote`. The backend must not reveal the evaluated agent's name/configuration
to the judge model. For matched/valid findings, votes should also populate
`severity`; match votes should populate `location_correct`; GT-building votes
should populate `category` and `merge_blocking`.

## Run bundle

```text
run-dir/
  run.json
  raw/<benchmark_id>.txt
  predictions/<benchmark_id>.json
  adjudications/<benchmark_id>.json
  metadata/<benchmark_id>.json
  traces/<benchmark_id>.jsonl
```

Judge tokens, time, and calls belong to evaluation overhead and are intentionally
not written into the tested agent's `RunMetadata`.

## Metric behavior

No composite score is produced. Core metrics, guardrails, diagnostics, and
evaluation-validity fields are emitted separately. `VALID_PARTIAL` contributes to
valid precision but never to recall. `VALID_NEW` on an Auto-certified Clean PR
invalidates that PR for every compared agent. Adjudication coverage below 98%
marks the result provisional.

## Deliberate integration boundaries

The evaluator supplies concrete orchestration and deterministic logic, while two
external capabilities remain plugin contracts because they depend on deployment
credentials and model providers:

1. `AgentAdapter`: invokes the PR-review agent/model in the project's chosen
   runtime and records model usage in `TraceCollector`.
2. `JudgeBackend`: invokes one independent judge configuration and returns a
   structured `JudgeVote`.

The code does not substitute fake model decisions for these integrations. GitHub
collection is implemented, but requires a token and is only used while building a
benchmark. Formal OS/network sandboxing must be configured by the process or
container launcher around the adapter.
