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

Point the harness at a deployed paired release. `REVIEWBOT_PYTHON` is the
absolute interpreter inside that release; the manifest is discovered only when
it is the `manifest.json` beside the same `.venv`, otherwise set it explicitly.
The environment file is optional when its values are already exported.

```bash
export REVIEWBOT_PYTHON=/workspace/wzr/omni-reviewbot/.venv/bin/python
export REVIEWBOT_RELEASE_MANIFEST=/workspace/wzr/omni-reviewbot/manifest.json
export REVIEWBOT_ENV_FILE=/workspace/wzr/omni-reviewbot/.env
```

```bash
bash eval/dataset/run_reviewbot_monthly.sh 2026-09
```

First time on a machine, smoke one item end-to-end first:

```bash
ONLY_ITEMS=4893 GEN_REPLICATES=1 bash eval/dataset/run_reviewbot_monthly.sh smoke
```

A non-month tag writes `results/reviewbot/REVIEWBOT_smoke.md` and never
touches the month-over-month `INDEX.md`.

The 15 frozen train+val PRs are now merged. The monthly command explicitly
uses `REVIEWBOT_EVAL_ARCHIVED_REPLAY=1`: an evaluation-only adapter presents
their pinned historical open snapshot to the installed ReviewBot Direct
pipeline. It requires `POST_MODE=shadow`, `REVIEW_CONTEXT_MODE=no_discussion`,
and `post=False`, and rejects every non-GET GitHub request. ReviewBot's
production rule remains open PRs only (drafts require an explicit request).
For a future live open-PR dataset, invoke `run_reviewbot_arm.py` directly
without the replay flag.

`goal-eval/expected_pr_bases.json` pins each historical merge base alongside
the existing head pins. The adapter reads the frozen `gt/pr<N>.diff` for file
metadata; GitHub's current file list has drifted for PRs 4816, 4926, and
4977. Before changing any pin, verify all 15 patches against a local
vllm-omni Git checkout:

```bash
python3 eval/dataset/verify_reviewbot_archived_bases.py --repo /path/to/vllm-omni
```

The verifier ignores only Git's display-only object IDs and optional hunk
function names. Each normalized historical `base..head` patch must exactly
equal its frozen ground-truth diff. The base-pin file, selected frozen diffs,
adapter SHA-256s, and replay mode are recorded in each arm manifest, so a
resumed campaign cannot silently mix historical snapshots or adapter versions.

`--dry-run` is deliberately planning-only: it does not require the release
interpreter or manifest and does not probe installed packages.

## Prerequisites

- A deployed/built **paired release artifact**, with `omni-reviewbot` and
  `infermatrix-copilot` installed into its `.venv`. Source checkouts and
  editable installs are not accepted. Set `REVIEWBOT_PYTHON`; set
  `REVIEWBOT_RELEASE_MANIFEST` unless it can be discovered at the same release
  app root. Set `REVIEWBOT_ENV_FILE` explicitly when configuration is not
  already exported.
- `AGENT_PROVIDER=codex` logged in and a bot build that has
  `REVIEW_CONTEXT_MODE` (PR #20+).
- The `claude` CLI logged in (judge, native auth).
- Cost: generation rides the Codex subscription, judging rides the
  Claude subscription — **zero API-key spend expected**. 15 items ×3
  generation ×3 judge ≈ 45 reviews + 135 judge calls; a few hours
  wall-clock at `ARM_JOBS=2`.

## What the harness enforces (all fail-closed, per item)

- The manifest release ID binds both 40-character Git SHAs; every wheelhouse
  artifact is size/SHA-256 checked, and the two root wheel METADATA versions
  match the installed ReviewBot/provider distributions.
- After checking the manifest, the harness copies the hashed wheelhouse into a
  private temporary release root and installs both root wheels plus dependencies
  into a fresh venv with pip indexes disabled. The selected release interpreter
  only bootstraps that venv; all doctor/review calls use the fresh interpreter.
  This prevents a tampered same-version installed package from borrowing a valid
  manifest identity.
- Runtime identity is queried from that fresh venv. Both modules must resolve
  inside it, and the provider's complete public capabilities — including
  `resource_revision` — must exactly equal the paired manifest. The manifest
  SHA-256 and both component SHAs/hashes are recorded in each arm manifest, so
  resume cannot mix releases. The private venv lives for the whole generation
  process and is removed only after all review subprocesses finish.
- Monthly report ingestion accepts only the runner's closed arm-manifest
  schema: no extra or missing top-level, config, behavior-env, release, or
  component fields; all values are type-checked, and stems, reviewed head SHAs,
  judge cap, replicate identity, and timestamp must have their runner-produced
  shapes. Stems are unique and numerically ordered, and reviewed-head keys must
  match them exactly. This strict envelope applies only to
  `reviewbot_YYYY-MM`; non-month smoke tags retain legacy-manifest compatibility.
- Child processes receive no `PYTHONPATH`, `PYTHONHOME`, provider source-path
  override, or user site. The harness runs the selected installed ReviewBot
  wheel through the evaluation-only archived adapter for these merged PRs;
  direct live-PR runs use `python -m omni_reviewbot`. It never imports a
  sibling ReviewBot checkout.
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
artifact/manifest fingerprint or configuration into a half-generated arm
(delete the `arms/<tag>_r*` dirs to restart a month from scratch).

For a deliberately unpaired local installation, only a non-month throwaway tag
may set `REVIEWBOT_EVAL_ALLOW_UNPAIRED=1`. The arm manifest records
`paired=false`, `throwaway=true`, and the reason; a `reviewbot_YYYY-MM` campaign
always rejects this escape hatch, so unpaired results cannot enter the monthly
series.

## Reading the report — three inherited rules

1. Compare only the **paired** deltas (arm − baseline inside one
   verdict); raw side means drift ±.08 across judge batches.
2. Replicates of one item are not independent: CIs are over **items**
   (n=15), which resolves ≈.06 — treat smaller movements as noise.
3. Months are comparable only under the same judge model and the same
   pinned baseline; both are recorded per row in `INDEX.md`.
