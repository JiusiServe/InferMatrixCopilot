# Blind PR-review replay

This harness measures a narrow claim: when the reviewer sees the same PR-time
code again, can it recover the same substantive review opinions without seeing
the target PR's raw historical review discussion during the run?

Two knowledge policies are intentionally separate:

- `same_pr_distilled` is the requested retention test: maintainers' earlier
  review has been converted into a generalized, provenance-bearing knowledge
  guide. The second review may use that guide, but not the raw target comments,
  replies, later code, or label file.
- `cross_pr_only` is a transfer test: the knowledge snapshot excludes anything
  learned from the target PR. This is a harder generalization benchmark, not the
  MVP success condition for second-read consistency.

It deliberately separates four artifacts:

| artifact | visible to reviewer | purpose |
|---|---:|---|
| `cases.jsonl` | yes | repository, PR number, base SHA, and the exact PR-time head SHA |
| knowledge snapshot | yes | pinned distilled knowledge allowed by `knowledge_policy` |
| `labels.jsonl` | no | target PR's historical comments, normalized as hidden findings |
| `predictions.jsonl` / `judgments.jsonl` | after run | model findings and semantic matches |

Never put raw target-review text, resolved-thread text, later fix commits, merge
results, or a label summary into `cases.jsonl` or the checkout. Under
`same_pr_distilled`, the knowledge snapshot may contain the generalized lesson
and PR provenance, but must not quote the hidden label or expose the later patch.
Run the reviewer with GitHub comment/timeline tools disabled. GitHub metadata may
be collected by an outer controller, but the reviewer receives only the PR diff
at `review_sha`, the repository tree at that SHA, deterministic gate facts
captured at that time, and an explicitly pinned knowledge snapshot.

## Data format

All files are JSON Lines (one object per line). See `examples/`.

`cases.jsonl` public record:

```json
{"case_id":"pr-123@abc1234","repo":"vllm-project/vllm-omni","pr":123,"base_sha":"...","review_sha":"...","mode":"performance","knowledge_policy":"same_pr_distilled","knowledge_snapshot":"sha256:...","prompt":"Review this PR at the supplied SHA. Do not use PR comments or later history."}
```

`base_sha` must be an ancestor of `review_sha`. For a historical review whose
current PR base has moved, pin `git merge-base <current-base> <review-head>`.
Using a later non-ancestor base mixes unrelated main-branch changes into the
replay diff; the runner rejects that case instead of producing a misleading
score. Each snapshot also includes `REPLAY_SCOPE.json`, a changed-file ledger
grouped by review scope and ordered by churn.

`labels.jsonl` private record:

```json
{"case_id":"pr-123@abc1234","findings":[{"id":"g1","severity":"major","root_cause":"normalized cause","impact_path":"input -> changed code -> failure","evidence":"historical comment URL or thread id"}]}
```

`predictions.jsonl` contains one record per replicate. Findings should split the
review into atomic opinions rather than copying rendered Markdown wholesale.

```json
{"case_id":"pr-123@abc1234","run_id":"r1","findings":[{"id":"p1","severity":"major","root_cause":"model's cause","impact_path":"model's affected path","comment":"full review comment"}]}
```

An independent judge compares each hidden gold finding with at most one
prediction. The judge sees labels only after the reviewer has finished:

```json
{"case_id":"pr-123@abc1234","run_id":"r1","gold_id":"g1","prediction_id":"p1","root_cause":2,"impact_path":2,"rationale":"same bug and same failing path"}
```

`root_cause` and `impact_path` are ordinal semantic scores: `0` unrelated, `1`
partially equivalent, `2` materially the same. Use `prediction_id: null` with
both scores zero for a miss. Severity agreement is computed mechanically by
`score_replay.py`: exact = 1, adjacent = 0.5, otherwise = 0.

## Metrics and acceptance gate

For every gold/prediction match:

```
semantic_match = 0.45 * root_cause/2
               + 0.40 * impact_path/2
               + 0.15 * severity_agreement
```

A **hit** requires both root cause and impact path to be non-zero and a score of
at least 0.65. A **same opinion** is stricter: root cause = 2, impact path = 2,
and exact severity. Gold recall is severity weighted (`blocker=4`, `major=2`,
`minor=1`, `nit=0.5`). Unmatched predictions count against precision.

For the initial MVP, use at least three performance-mode replicates per case and
gate a knowledge revision on all of:

- weighted hit recall >= 0.80;
- weighted same-opinion recall >= 0.60;
- precision >= 0.70;
- all-run weighted recall >= 0.60 (the finding appears in every replicate);
- mean pairwise hit-set Jaccard >= 0.70;
- no label-leakage validation error.

These thresholds measure semantic reproducibility, not wording identity. Keep
both macro (case-level) and micro (finding-level) results; a large PR must not
hide complete failure on smaller PRs.

## Commands

Validate the split before any expensive run:

```powershell
python eval/replay_review/score_replay.py validate `
  --cases eval/replay_review/examples/cases.jsonl `
  --labels eval/replay_review/examples/labels.jsonl
```

Score completed replicates and judge decisions:

```powershell
python eval/replay_review/score_replay.py score `
  --labels eval/replay_review/examples/labels.jsonl `
  --predictions eval/replay_review/examples/predictions.jsonl `
  --judgments eval/replay_review/examples/judgments.jsonl
```

The examples are synthetic plumbing fixtures. Real retention cases and hidden
labels are in `data/vllm_omni_{cases,labels}.jsonl`; validation/scoring tools may
open the labels, but the review runner must receive only the cases file.
