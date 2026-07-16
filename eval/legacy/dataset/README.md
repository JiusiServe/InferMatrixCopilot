# vllm_omni_dataset — 20 PR reviews + 20 issue answers, each 10 train / 5 val / 5 test

Dataset for **training and evaluating agent self-improvement** on real
`vllm-project/vllm-omni` history. Two task kinds × 20 items each, both split
10/5/5. Constructed 2026-07-11 from live GitHub state.
Manifest: [`vllm_omni_dataset.yaml`](vllm_omni_dataset.yaml).

## Partition semantics (SIP-Bench-style)

| Partition | n per kind | Role | Rules |
|---|---|---|---|
| **train** | 10 | adaptation stream | The agent (or an evolution proposer) may learn from these: distill skills, profile facts, checklist/prompt updates, debug memories. Weak-GT items (open issues) are deliberately concentrated here. |
| **val** | 5 | promotion gate | Candidate improvements (a new skill, an updated checklist, a prompt change) are accepted only if val scores don't regress. Never used as learning evidence. |
| **test** | 5 | **frozen holdout** | Never read by any proposer; results never flow back into training. Evaluate only at checkpoints (T0 = pre-adaptation, T1 = post-adaptation, ...) to measure held-out gain and backward retention. Strong ground truth only (all test issues are closed with maintainer resolutions). |

Anti-Goodhart rules (from the self-improvement measurement literature):
1. Test results are reported, never inspected for error analysis that feeds proposals.
2. Judge model ≠ proposer model where feasible.
3. Score val/test as replicate means (≥3 runs) — single-run RQS noise is ±0.1.
4. If test saturates or leaks, retire and re-draw from the same class distribution; never "fix" items in place.

## Run commands

```bash
omni-copilot -p "review pr <N>"                # pr_review items
omni-copilot -p "answer issue <N>"             # issue_answer items (dry-run; ALLOW_POST stays off)
```

## Ground truth per kind

- **pr_review**: human review comments on the merged PR (count in manifest), plus
  three GOLD latent-gap items — history proves what human review initially missed,
  distributed one per partition (train #4870, val #4810, test #4834):
  - **#4870** → follow-up #4910 fixed a missed dual-batch-axis case.
  - **#4810** → issue #4891 ("missed by #4810") — one caller of the removed
    `get_cache_scale` API escaped the sweep.
  - **#4834** → its own safeguard broke merge CI (#4905 → relaxed by #4912);
    questioning the guard's strictness counts as a hit.
  Score a gap-hit when the review identifies the area (file/axis/caller), not the exact eventual diff.
- **issue_answer**: maintainer answers/resolution on closed issues (13/20;
  `resolution_pr` recorded where a fix PR closed it); open issues (7/20, all in
  train) are judged by evidence-grounding rubric only. One deliberate
  triage-class item (#4842, closed INVALID) where the correct answer is a verdict,
  not a fix. One RFC-class item (#4802) judged on design engagement.

## Selection criteria

1. **Class typicality** — mirrors real repo traffic: post-rebase regressions,
   upstream-API drift, CI-expectation failures, version-mismatch user issues,
   config-interaction bugs, new-model requests, one docs PR, one RFC.
2. **Module diversity** — adapter-zero modules (worker_runner, model_executor,
   online_serving, model_config, platform, scheduler, input_output, benchmarks)
   plus `diffusion/` and `docs` (not adapter modules — recorded as-is).
3. **Size diversity** — review PRs range from a 2-line config deletion (#4970)
   to a 3.2k-line feature (#4804).
4. **Split stratification** — every partition mixes classes, modules, and sizes;
   GOLD items one per partition; open/weak-GT issues only in train; test is
   all-closed for reliable scoring.

## Cross-split couplings (do not reshuffle)

- **issue #4905 (val) is the same event as test-GOLD PR #4834's latent gap.**
  It must never move to train — an agent learning from it would be handed the
  test item's gap answer. Val is safe (never used as learning evidence).
- issue #4891 (val) is val-GOLD PR #4810's gap — same-split, no constraint.
- Two test items have verdict-type GT, not fix-type: issue #4957 (closed NOT
  reproducible) and, in val, issue #4842 (closed INVALID). Score these on the
  triage verdict.

## Reproducibility caveats

- **GT leakage**: for merged PRs / closed issues, the fix exists in repo history.
  Point runs at the *pre-merge* head SHA (`gh pr checkout <N>` then reset to the
  head commit, or use the merge commit's first parent) so the agent cannot read
  its own answer. For closed issues, run against the last commit *before* the
  `resolution_pr` merged.
- **Live drift**: the 7 open train issues reflect 2026-07-11 state; snapshot
  thread state per run. If one closes, it gains GT — regenerate its record but
  keep it in train.
- Comment counts are as-of construction and can grow.
