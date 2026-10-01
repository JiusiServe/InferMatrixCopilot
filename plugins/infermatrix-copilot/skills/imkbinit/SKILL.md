---
name: imkbinit
description: Bootstrap a repository's InferMatrixCopilot knowledge base with `kb init`, one reviewed stage at a time (skeleton, modules, deepen, pr-history, harvest-calibration). Use when the user invokes /imkbinit or $imkbinit, asks to initialise or onboard a repository's knowledge base, or wants the next kb init stage run.
---

# InferMatrix knowledge-base init

```text
/imkbinit <repository> [--publish]
$imkbinit <repository> [--publish]
```

The installed InferMatrixCopilot root is:

```text
{{INFERMATRIX_COPILOT_ROOT}}
```

If that placeholder was not replaced, locate the InferMatrixCopilot checkout
containing `src/infermatrix_copilot/kb_service/init_stages.py`.

## Launcher

The MCP install only registers an isolated `uvx` server, so the CLI may not be
on `PATH`. Call it `<imc>` below and resolve it once:

1. `infermatrix-copilot`, if `command -v infermatrix-copilot` finds it (a full
   `install.sh` install).
2. Otherwise run it from the InferMatrixCopilot root above, so the CLI and
   the knowledge tree come from the same checkout:

   ```text
   uvx --from "<infermatrix-root>[kb]" infermatrix-copilot
   ```

Check it once with `<imc> kb --help`. If neither works, stop and say how to
install it (`bash install.sh` in the InferMatrixCopilot checkout).

This skill only drives the `kb init` CLI and reports what it did. The CLI owns
every decision: what to generate, the checks, the budget, publishing. Never
edit the generated pages, adapters, or stage records yourself.

## 1. Resolve the repository

`kb init` takes the knowledge repository name: the `repos/<name>` in an
adapter's `knowledge.repo_subdir`. Match the user's alias, `owner/name` or URL
against `repo.full_name` in `adapters/*/manifest.yaml`. With no match, stop: a
repository needs its own adapter PR (with a `knowledge_lifecycle.init` block)
before `kb init` can run. If that block has no `seeds`, mention that
`<imc> kb init <repo> --suggest-seeds` lists candidates (it only
prints them, and makes no model call).

## 2. Find the next stage

Stages run in this order: `skeleton` → `modules` → `deepen` → `pr-history` →
`harvest-calibration`. The record of each stage is
`<state-dir>/init/<repo>/<stage>.json`, where the state dir is `--state-dir`,
else `$KB_STATE_DIR`, else `~/.infermatrix-copilot/kb`.

Which stages count as done depends on the mode of this invocation:

- **Publishing** (the user asked for PRs): a stage is done only when its
  record's `pr.number` is set and `gh pr view <number> --json state`, run
  inside the InferMatrixCopilot checkout (the knowledge repository), says
  `MERGED`. Dry-run records don't count, so a previewed stage is published
  next rather than skipped.
- **Dry run** (the default): a stage is also done when its record exists with
  `status: dry_run`, so stages can be previewed end to end before any PR.

The next stage is the first one that isn't done. If an earlier stage's PR is
open, stop and say it's waiting for the owner's review. If a record says
`blocked`, report its `problems` and stop.

## 3. Run it

Dry run is the default:

```text
<imc> kb init <repo> --stage <next> --dry-run
```

Only publish when the user explicitly asks (`--publish`, "open the PR").
Publishing needs `ALLOW_PUSH=1`, `ALLOW_POST=1` and
`KB_INIT_GIT_AUTHOR='Name <email>'` in the environment. Tell the user which of
these are missing instead of setting them. Then run the command without
`--dry-run`. A private upstream always runs as a dry run.

What each stage opens:

- `skeleton`: the map, the doc invariants and the seeds.
- `modules`: one map card for every unrouted module.
- `deepen`: code rules for the hot modules, plus the adapter flip to
  `enabled: true, mode: shadow`.
- `pr-history`: reads the latest 1,000 merged upstream PRs as of the upstream
  pin, oldest first, with one extraction call per PR through `KB_GENERATOR`.
  `--pr-count N` overrides `init.pr_history_count` (default 1000). Executable
  rules go to their nearest component or offered model owner; model-specific
  contracts stay with that model. PRs yielding no upgrade are recorded and
  make no commit. One draft PR contains one commit per accepted upstream PR.
  The PR body shows counts and the first 20 upgrades; all upstream references
  remain in the commit trailers. Codex reviews its complete base-to-head diff,
  prior owner rules, routes and pinned source evidence;
  only approval of that exact head makes it ready. `KB_INIT_REVIEWER` may
  pin a Codex model/effort (`codex:model[:effort]`, default
  `codex:gpt-6-sol:medium`); it never changes reviewer provider. A failed review leaves
  the PR draft. Dry runs also perform the complete Codex review and write a
  `COMMITS.json` beside the preview. Raw PR evidence is transient.
- `harvest-calibration`: turns the merged review into
  `adapters/<adapter>/kb-calibration/cases/*.json`. It refuses to open a PR
  with fewer than five bad cases from the owner or from mutations.

`auto_merge` still needs `kb calibrate` and the shadow period. The skill never
flips it.

If the CLI or its run report blocks the stage, report the reason and stop.
Never work around it by hand.

For `pr-history`, a blocked record is a resumable checkpoint. When the user
requests a retry, rerun the same stage with the same pin/window/backend;
completed PRs and prepared commits are reused. The stage accounts cumulative
spend on its frozen knowledge baseline; unrelated main merges do not restart
the batch. Changing the baseline requires a new state directory.
`--budget-usd N` may raise the ceiling to continue after a budget stop.
Prepared publication retries also require the original immutable inputs.
It does not publish an incomplete window. Existing init runs with no history
record remain harvestable, and may add this phase after their earlier stages
have merged. Once a history record exists it must finish before harvest.

## 4. Report

Read the stage record and the PR body (`PR_BODY.md` under `pr.dry_run_dir` for
a dry run, otherwise the opened PR). Summarise:

- pin and status, plus the PR link or dry-run directory
- coverage: module and PR-weighted, routed and rule-bearing, before and after
- the judge table: pass, unsure, unjudged, and the rules stripped as fail
- dropped rules and their reasons
- the "needs human edit" checklist
- spend against the budget, and any `unfinished` units

## 5. Stop

Stop after one stage. The owner reviews and merges its PR before the next
stage can run. Never run two stages in one invocation, and never merge a PR.
