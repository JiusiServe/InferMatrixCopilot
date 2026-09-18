# RFC — SkillAdam as an external SKILL.md optimizer, gated by this repo's eval

- Status: **proposed, nothing implemented.** No code, no dependency, no fork
  exists yet; this RFC asks for agreement on the sequence before PR #1
- Owner: this repo owns the skill-injection budget, the governance gate, and
  the accept/reject decision. SkillAdam is an external, unmodified tool that
  may only *propose* candidate skill text — it is never imported by
  `src/infermatrix_copilot/` and never runs as a pipeline step
- Upstream: [ruc-datalab/SkillAdam](https://github.com/ruc-datalab/SkillAdam),
  MIT, Copyright (C) 2026 Tencent. Released 2026.09; BibTeX still "coming
  soon" and the README carries no quantitative result — treat it as alpha
- Evidence for every claim below: `engine/agent_runtime/knowledge.py:120,163`,
  `engine/agent_runtime/dispatch.py:70`, `config.py:336`,
  `eval/dataset/vllm_omni_dataset.yaml`, `eval/dataset/README.md`,
  `eval/dataset/run_copilot_arm.py`, `eval/dataset/judge_val.py`, and a
  read of the upstream tree at its 2026-09 release

## Motivation

Every `SKILL.md` in this repo is hand-written and hand-tuned. There is no
systematic search over that text, and no measurement that a given edit helped:
the six repo-neutral skills plus the vllm-omni adapter skill have been revised
by judgement alone.

SkillAdam optimizes exactly that artifact. Its loop is task rollouts →
trajectory condensation → a bounded unified diff → strict apply → an
acceptance gate comparing baseline and candidate → momentum over accepted and
rejected problems → an adaptive edit budget. The engine is fully open source
(`skilladam/core/`), `dependencies = []`, MIT.

Two facts make it worth evaluating *here* specifically rather than in the
abstract:

1. **We already have the artifact and its retrieval plumbing.** Seven
   `SKILL.md` files, retrieved top-k and injected into every agent step by
   `engine/agent_runtime/`.
2. **We already have the measurement discipline it assumes.**
   `eval/dataset/` is a SIP-Bench-style dataset — 20 `pr_review` + 20
   `issue_answer` items, each split 10 train / 5 val / 5 test, plus 40
   holdout PRs in waves 2–5 — with written anti-Goodhart rules: test is
   never read by a proposer, val is the promotion gate and never learning
   evidence, val/test are scored as replicate means (≥3 runs; single-run RQS
   noise is ±0.1), and the judge model must differ from the proposer.
   Upstream carries the same rule (`product/models.py:19` defines
   `TaskSplit = Literal["train", "validation", "test"]`; its architecture doc
   states "Test cases must never be used for optimization or patch
   selection"). The two protocols line up without adaptation.

## Three facts that shape the whole design

### 1. Only `description` is guaranteed to reach the model

There are exactly two channels from a `SKILL.md` to a model:

| Channel | What it sends | When |
|---|---|---|
| dispatch context (`knowledge.py:120` → `dispatch.py:70`) | `{name, description}`; falls back to `body[:200]` only when a skill has no description | **every agent step** |
| `skill_search` tool (`knowledge.py:163`) | `name + description + body[:1500]`, top-5 | only when the model chooses to call it |

So the body is *conditional* on a tool call and *truncated* at 1500
characters. The description — one frontmatter line — is the only text with
guaranteed delivery. Any optimization run that scores a full `SKILL.md` is
scoring text this runtime may never send.

### 2. The skills that overflow the cap are the ones the eval cannot see

| skill | body | over 1500 | on the measured path? |
|---|---|---|---|
| `pr-review-breaking-changes` | 1355 | — | yes (`pr_review` half) |
| `model-adaptation-review` (adapter) | 1452 | — | yes (`pr_review` half) |
| `issue-answer-contract` | 1420 | — | yes (`issue_answer` half) |
| `ci-debug-root-cause` | 531 | — | no |
| `docstring-conventions` | 2551 | 1051 | no |
| `knowledge-base-contribution` | 3570 | 2070 | no |
| `code-quality-review` | 4203 | 2703 | no |

The three skills whose tails are unreachable are all about maintaining *this
copilot's own source*, which `eval/dataset/` does not measure. That is a
real limit on stage 2 below: the ablation can only move numbers on skills
that were never truncated in the first place, so a small or null effect is
the expected outcome, not a surprise.

### 3. `pr-review-breaking-changes` is contaminated against val and test

Found while scoping this RFC, pre-existing, and **not** introduced by it: the
shipped skill body cites ground truth from held-out dataset items.

| cited in the skill | dataset item |
|---|---|
| `#4810 → issue #4891` | `pr_review`/**val**, `issue_answer`/**val** |
| `#4834 broke merge CI → #4905/#4912` | `pr_review`/**test**, `issue_answer`/**val** |
| `GT #4849` | `pr_review`/**test** |

A model carrying this skill has been told, in prose, what two test items and
two val items are supposed to find. Every val/test number ever produced by an
arm carrying it is contaminated to that degree, and no restriction on the
*task prompts* can undo it — the leak is in the artifact under optimization.

A scan of the other six skills found one further citation,
`model-adaptation-review` → `#5003`, which is an `issue_answer` **train**
item; train is the adaptation stream, so that one is legitimate.
`issue-answer-contract` cites no dataset item at all.

Two consequences, both binding on the design below:

1. **The trial target changes** to `adapters/vllm_omni/skills/model-adaptation-review/SKILL.md`
   — on the measured `pr_review` path, 1452 chars so not truncated, and clean.
2. **Repairing the leak is out of scope here and needs its own issue.** The
   dataset README's own rule governs it: *"If test saturates or leaks, retire
   and re-draw from the same class distribution; never 'fix' items in place."*
   Rewriting the skill to drop the citations does not restore the holdout —
   the items must be retired and redrawn, or that skill must be scored only
   on the wave 2–5 holdout sets, which it does not cite.

## Design

Four stages, each landing separately (`one fix, one PR`).

### Stage 1 — an injection-budget knob (PR #1)

Add `skills_body_chars: int = 0` to `config.py` and have the dispatch context
append `body[:skills_body_chars]` under that budget. **`0` reproduces today's
behavior byte for byte**, so the default path is unchanged and the knob is an
opt-in ablation switch.

This follows the repo's own idiom rather than inventing one:
`profile_briefing_enabled` exists precisely as the `{no-profile}` ablation
arm, and every capacity constant in `config.py` carries its eval citation
inline (`pr_diff 120k->260k: a 170k-char diff (pr4804) lost ~30% of its hunks
and recall collapsed to 0.16`). A cap in this codebase is changed by
measurement, never by argument.

`skill_search`'s own 1500 cap is **not touched in this PR** — one variable at
a time keeps the ablation interpretable.

Guardrails: a test pinning that at `0` no body text appears in the dispatch
context, and a test that at `n > 0` the body appears truncated at exactly `n`.

### Stage 2 — the ablation arm (parallel, non-blocking)

**Which harness.** `eval/run_eval_v3.py` and `eval/run_replicates.sh` are the
*legacy* benchmark: they re-score cached arm reviews for three hardcoded PRs
(4678 / 4679 / 4849) and know nothing about the dataset splits. They are not
the gate. The dataset harness is two scripts under `eval/dataset/`:

- `run_copilot_arm.py [splits]` — generation. Drives the shipped CLI
  end-to-end (intent → planner → executor, `ALLOW_POST`/`ALLOW_PUSH` off).
  `ARM_OUT` selects the output directory, which is how two configurations
  stay isolated; `test` is untouched unless asked for.
- `judge_val.py` — blind pairwise + rubric judging over `SPLIT` (default
  `val`), `REPLICATES=3`, judge `claude-sonnet-5` — a third model, distinct
  from both arms, satisfying the dataset's `judge ≠ proposer` rule.
  `ARM_A_DIR` / `ARM_B_DIR` / `JUDGE_OUT` select what is compared.

**`REPLICATES` does not cover generation variance.** `judge_val.py` re-judges
the *same saved arm outputs* N times, so `REPLICATES=3` measures judge noise
only. `run_copilot_arm.py` is resumable and skips existing non-empty outputs,
so re-running it into the same `ARM_OUT` regenerates nothing. Generation
variance — the dominant term, and the one that has repeatedly produced
champions resting on a single item — is only sampled by **independent
generation runs into distinct arm directories**:

```bash
for r in 1 2 3; do
  SKILLS_BODY_CHARS=0    ARM_OUT=copilot_body_off_r$r run_copilot_arm.py val
  SKILLS_BODY_CHARS=4500 ARM_OUT=copilot_body_on_r$r  run_copilot_arm.py val
  ARM_A_DIR=arms/copilot_body_on_r$r ARM_B_DIR=arms/copilot_body_off_r$r \
    JUDGE_OUT=judgments/val_bodyinject_r$r SPLIT=val REPLICATES=3 judge_val.py
done
```

Three generation runs per configuration, each judged three times; the
comparison is over the aggregate of the three runs, never a single one. A
default flip or a candidate promotion on one generation run is not evidence.

**`ARM_B_DIR` must be set explicitly.** Its default is the historical Opus 4.8
baseline, so an unset `ARM_B_DIR` silently judges against the wrong reference
and produces a plausible, meaningless number. Verify the recorded manifest
immediately after launch, not at the end of the run.

If full-body injection wins, the default flips in a follow-up PR with its
measurement cited in `config.py` alongside the others. If it does not, the
knob stays default-off and still serves stage 3.

Stage 3 does not wait on this result.

### Stage 3 — the SkillAdam trial (candidate generation only)

Run outside this repository, in a scratch worktree, using the upstream
product path (`integrations/claude-code/install.sh`, MCP server
`skilladam.product_mcp`). Nothing is vendored and nothing is forked.

- **Target**: `adapters/vllm_omni/skills/model-adaptation-review/SKILL.md` —
  on the measured `pr_review` path, not currently truncated, and free of
  holdout citations (see finding 3). `pr-review-breaking-changes` was the
  obvious first choice and is disqualified by that finding.
- **Tasks**: an 8-task manifest built from the **10 `pr_review` train items**.
  Upstream requires ≥2 capabilities and at least one boundary/adversarial/
  regression task, self-contained prompts, and `failure_feedback` on every
  evaluation. Inner rollouts run in temporary directories with no access to
  our workspace, so each prompt embeds its diff and the upstream excerpts it
  needs — the same technique already used for the sandboxed-Codex work.
- **Inner model**: the Claude Code CLI. Our judge is DeepSeek v4, so
  `judge ≠ proposer` holds by construction. The already-exhausted Codex
  GitHub-review quota is not touched.
- **What gates the loop**: upstream's own approximate `rubric_judge`, built
  from train-split ground truth. It *cannot* call our harness — that harness
  is a two-stage pipeline of shell entry points (generation, then judging),
  and the product path's evaluation kinds are a closed `Literal`
  (`programmatic / reference / rubric_judge / hybrid`) and its judge is an
  in-process `JudgeFunction`, with no shell-out. **SkillAdam is therefore a
  candidate generator, not an authority.** A candidate that passes its gate
  has proved nothing here until our own harness scores it.

### Stage 4 — landing

A surviving candidate is scored by the same two-stage dataset harness as
stage 2, and under the same replicate rule: three independent
`run_copilot_arm.py val` passes with the candidate skill in place, each into
its own `ARM_OUT`, judged against three matching passes of the current skill.
The aggregate is judged by inspection (see "Accepted risks"). Test is
generated and scored once at the end (`SPLIT=test`) and **not** used for
tuning.

The candidate text lands as a `_candidates.json` entry plus its own PR against
`skills/`. **SkillAdam never writes an active `SKILL.md`** — upstream will do
so by default once its gate passes, so the trial must run against a scratch
copy and the promotion must remain the human act.

## Fit with this repo's invariants

| Invariant | How this stays inside it |
|---|---|
| 3 — generation is structurally read-only | SkillAdam runs as an external tool in a scratch tree; it is never composed into a playbook or a step, so no write-risk step is ever generated |
| 6 — repo neutrality | `skills_body_chars` is a generic budget; no SkillAdam import, name, or path enters `src/infermatrix_copilot/` |
| 7 — fail-closed, never silently degrade | the knob defaults to `0`, which is today's behavior exactly; no path changes without an explicit env setting |
| read-wide / write-narrow | agents propose (`_candidates.json`), a human promotes via PR — unchanged; the whole point of running SkillAdam out-of-tree is that it cannot bypass this |
| one fix, one PR | stages 1, 2 (if the default flips), and 4 are separate PRs |

## What this RFC does not propose

- **Making skill optimization a copilot capability** — a `skill_optimize`
  task kind, a playbook, a write-gated promotion path. That is the follow-on
  ("phase B"), and it is deliberately blocked on trial data: it would need a
  new `KIND_TIER` entry and it sits uncomfortably against invariant 3.
- **Forking SkillAdam.** A faithful gate — a `BenchmarkAdapter` for
  vllm-omni PR review plus an `ExecutionBackend` that runs this copilot's own
  review step as the rollout — would let its loop optimize the true RQS
  metric instead of a proxy. It is the technically correct integration and it
  would make `eval/dataset/` a first-class SkillAdam benchmark, which is a
  real contribution back to the upstream authors rather than one-way use. It
  is also a project, not a trial, and belongs after evidence.
- **Raising `skill_search`'s 1500 cap.**

## Alternatives considered

- **Optimize within the deliverable budget** (`description` + `body[:1500]`,
  enforced by a `max_length` programmatic check) instead of changing the
  plumbing. Cheapest, needs no copilot change, and measures exactly the bytes
  that ship today — but it concedes that the 2703 unreachable characters in
  `code-quality-review` are dead text and compresses them away rather than
  asking whether they should be delivered. Rejected in favour of fixing the
  plumbing first.
- **Flip full-body injection on by default and argue it from first
  principles** ("more context cannot hurt"). Rejected: every other capacity
  constant in `config.py` carries a measurement, and the top-k body text
  competes for the same cached prefix as evidence (3 skills × up to 4203
  chars ≈ 3k tokens per agent step).
- **Expand `eval/dataset/` before measuring anything.** Highest confidence
  and the honest answer to the variance problem, but it is the generation-
  variance project — weeks — and would shelve this indefinitely.
- **Inject our own `JudgeFunction` into the upstream product path.** The
  `_rubric(judge=...)` seam exists, but no configurable entry point to it was
  found; it would require patching upstream. Not pursued for the trial.

## Rollout

1. This RFC.
2. A separate issue for the holdout leak in `pr-review-breaking-changes`
   (finding 3). It blocks nothing here — the trial target moved off that
   skill — but it silently taints existing val/test numbers for every arm
   carrying it, so it should not wait on this RFC's outcome.
3. PR #1 — the knob plus its two guardrail tests; full offline `pytest`
   locally before pushing.
4. Stage 3 trial and stage 2 ablation, in parallel; neither blocks the other.
5. If a candidate survives val across three generation runs, a skill-promotion
   PR; test scored once.

**Kill condition.** Two SkillAdam rounds producing no candidate that survives
our val scoring ends the trial. "This method does not clear our signal
strength" is a publishable-internally result and closes the question rather
than leaving it open.

**Accepted risks**, recorded deliberately rather than mitigated:

- **No pre-registered acceptance threshold.** The val delta is judged after
  the fact. This is a conscious choice, and it bounds what the trial's output
  can be used for: it supports *our* decision about whether to invest in
  phase B, and it is **not** evidence that SkillAdam works. Any report to the
  upstream authors or in a weekly update must say so.
- **The prior is against skill prose being the bottleneck.**
  `eval/dataset/judgments/T3_FORENSICS.md` found ~90% of judge penalties came
  from mechanical delivery problems, not weak analysis. Optimizing the text a
  reviewer reads is therefore working on the smaller of the two terms, and a
  null result would be consistent with what we already know. This is a reason
  to keep the trial bounded, not a reason to skip it — the delivery finding is
  itself a prompt-text question in part.
- **Quota.** Inner rollouts consume the Claude Code subscription; an 8-task
  manifest across several optimization rounds is not free.
- **Upstream maturity.** Alpha, no published numbers, no BibTeX. Running it
  out-of-tree means abandoning it costs one deleted scratch directory.
- **Queue contention.** PR #1 joins a queue that already has the knowledge-
  intake batch open ahead of it.

## Decisions already taken

Recorded so the sequence is not relitigated:

1. External optimizer first; copilot capability (phase B) only after trial data.
2. Fix the injection plumbing before optimizing, rather than optimizing
   inside today's delivered budget.
3. Ship the plumbing change as a default-off knob measured by an ablation
   arm, not as a default flip.
4. SkillAdam is a candidate generator; the dataset harness
   (`eval/dataset/run_copilot_arm.py` + `judge_val.py`) holds the
   accept/reject authority — not the legacy three-PR `run_eval_v3.py`.
5. No pre-registered threshold; val is judged by inspection. Test stays
   frozen regardless.
6. The trial target is `model-adaptation-review`, not
   `pr-review-breaking-changes`, because the latter cites held-out items.
