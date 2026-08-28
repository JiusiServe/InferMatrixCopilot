# Reviewbot monthly review-quality probe

Judges the **live omni-reviewbot configuration** (its Direct pipeline:
Codex + InferMatrix knowledge routes + its own gates) against the pinned
`baselines/claudecode_opus5`, on the dataset's **train+val PR items**
(15; test stays frozen), with the pinned `claude-sonnet-5` judge and the
campaign's paired/clustered statistics.

**These are loop+model numbers.** They live in `results/reviewbot/` and
are never merged into `results/model_comparison.md` (generator ablations
ride our own pipeline and swap only the model — 2026-08-14 decision).

## The one command

```bash
bash eval/dataset/run_reviewbot_monthly.sh 2026-09
```

First time on a machine, smoke one item end-to-end first:

```bash
ONLY_ITEMS=4893 GEN_REPLICATES=1 bash eval/dataset/run_reviewbot_monthly.sh smoke
```

A non-month tag writes `results/reviewbot/REVIEWBOT_smoke.md` and never
touches the month-over-month `INDEX.md`.

## Prerequisites

- An installed omni-reviewbot checkout (default: the sibling
  `omni-reviewbot/` next to this repo; override `REVIEWBOT_DIR`) with its
  `.venv` and `.env` set up, `AGENT_PROVIDER=codex` logged in, and a bot
  build that has `REVIEW_CONTEXT_MODE` (PR #20+).
- The `claude` CLI logged in (judge, native auth).
- Cost: generation rides the Codex subscription, judging rides the
  Claude subscription — **zero API-key spend expected**. 15 items ×3
  generation ×3 judge ≈ 45 reviews + 135 judge calls; a few hours
  wall-clock at `ARM_JOBS=2`.

## What the harness enforces (all fail-closed, per item)

- `POST_MODE=shadow` asserted from CLI output — nothing can reach GitHub.
- `REVIEW_CONTEXT_MODE=no_discussion` asserted (`review_context:
  no_discussion (0 threads)`): on these PRs the historical review
  threads ARE the ground truth; reading them measures leakage.
- Reviewed head == `goal-eval/expected_pr_heads.json`, and the bot's
  `changed_files` == the frozen GT diff's file count.
- Sanitized artifacts (markers stripped, neutral heading) must fit the
  judge's 24k cap — over-cap is a campaign failure, not a silent
  truncation.
- Before reporting, `build_reviewbot_report.py --verify` audits exact
  denominators, pinned judge identity, and fresh candidate sha256s in
  every verdict (judge_val skips existing files, so its exit code is not
  a completeness proof).

## On partial failure

Everything is resumable: rerun the same command. Generated arm files and
existing verdicts are skipped; the manifest refuses to mix a changed bot
configuration into a half-generated arm (delete the `arms/<tag>_r*` dirs
to restart a month from scratch).

## Reading the report — three inherited rules

1. Compare only the **paired** deltas (arm − baseline inside one
   verdict); raw side means drift ±.08 across judge batches.
2. Replicates of one item are not independent: CIs are over **items**
   (n=15), which resolves ≈.06 — treat smaller movements as noise.
3. Months are comparable only under the same judge model and the same
   pinned baseline; both are recorded per row in `INDEX.md`.
