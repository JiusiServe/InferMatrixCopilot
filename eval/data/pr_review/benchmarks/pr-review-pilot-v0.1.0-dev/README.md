# PR Review Pilot Benchmark v0.1.0 (Dev)

This directory is the first **loadable, hash-frozen PR Review pilot benchmark** for `vllm-omni-copilot`.
It implements the structure and data rules in the two planning documents under `eval/docs/`.

## Scope

- 5 frozen PR items
- 3 buggy PRs, 6 GT findings
- 2 Auto-certified Clean PRs
- 4 merge-blocking findings
- Categories: `compatibility_api`, `correctness`, `test`

This is a **Dev pilot**, not the 25–30 PR formal v0.1 benchmark and not a hidden Test Set. It is suitable for
validating the loader, runner, adjudication, metrics and report pipeline.

## Jury provenance and ranking boundary

- Clean PRs use three independent legacy Reviewer Agent outputs plus explicit candidate-finding adjudication.
- Buggy PR GT uses verified GitHub snapshots, historical/legacy review evidence, and a versioned migration Jury.
- The future formal Test Set must still replay the planned 3 Judge configurations × 2 position swaps and remain physically hidden.
- Therefore this version is usable for development evaluation, but is not eligible for formal model ranking.

## Data boundaries

- `manifest.yaml` and `items/*.yaml`: formal scoring data loaded by the evaluator.
- `private/`: GitHub snapshots, historical evidence, GT jury records, clean certification and provenance.
- Runner input must never expose `expected_verdict`, `clean_status`, `gt_findings` or any file under `private/`.

## Validation

```bash
python -m eval.tasks.pr_review benchmark validate \
  --manifest eval/data/pr_review/benchmarks/pr-review-pilot-v0.1.0-dev/manifest.yaml

pytest -q test/eval/tasks/pr_review/test_benchmark_data.py
```

## Item selection

| PR | Label | Snapshot | Why included |
|---:|---|---|---|
| 3094 | Buggy | pre-review | Historical maintainer review plus post-review fix; two merge blockers. |
| 4810 | Buggy | merged head | Incomplete removed-API migration plus ineffective delegated-loader regression test. |
| 4834 | Buggy | merged head | Default sleep level becomes unrecoverable; hardware-only tests leave control-plane logic unprotected. |
| 4816 | Auto-certified Clean | merged head | Three independent reviewers found no actionable issue. |
| 4825 | Auto-certified Clean | merged head | No merge blockers; all four candidate comments were adjudicated invalid or pure non-problems. |

See `private/provenance/` for migration choices and exclusions.
