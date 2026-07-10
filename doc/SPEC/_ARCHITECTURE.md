# 00 — Architecture, Scope, Functionality

## 1. What the system is

A playbook-driven repo-maintenance copilot for vLLM-Omni (and, by design, any
repo with an established profile). It turns a natural-language or flag command
into a governed, resumable, auditable pipeline of vetted steps, and escalates
rather than guesses when blocked.

## 2. Functionality (the task kinds)

Exactly seven task kinds exist; each has a fixed blast-radius **tier** that no
input can change (see `task_spec.py`):

| Kind | Tier | Read-only | What it does |
|---|---|---|---|
| `repo_rebase` | L0 | no | rebase the fork onto upstream (delegates to the locked 5-phase orchestrator) |
| `pr_rebase` | L1 | no | replay a PR branch onto its latest base |
| `pr_debug` | L1 | no | diagnose & fix a PR's failing CI |
| `pr_review` | L2 | yes* | evidence-grounded inline review |
| `issue_answer` | L2 | yes* | draft an answer to an issue |
| `issue_filter` | L2 | yes* | triage/label/route issues |
| `repo_profile` | L2 | no** | establish/refresh a repo's profile |

\* read-only unless the explicit `post` intent is set. \*\* reads the target
repo but writes knowledge under `plugins/<repo>/`.

Tiers (`§3.2` of DESIGN): **L0** reuse a locked playbook verbatim; **L1** adapt
a vetted playbook (plan-review gated); **L2** may fall back to generation, but
only for read-only kinds.

## 3. The three layers + the engine substrate

```
 Interface   cli.py / chat.py / ui.py            NL & flags -> one dispatcher
     │
 Task        task_spec.py / intent.py            NL -> TaskSpec (tier from kind)
     │
 Planning    engine/planner.py / playbooks/      reuse > adapt > generate
     │
 Engine      engine/{step,registry,executor}     run steps: checkpoint, foreach,
     │       engine/agent_runtime.py              typed failures, governed agents
     │       agent_loop.py, tools.py, scopes.py
     │
 Steps       engine/steps/*                       the vetted step library
     │
 Edge        plugins/, ci/, profiles/             repo knowledge & capabilities
             review/, memory/, run_trace, notify, metrics   cross-cutting
             scopes.py, push.py                   pure safety primitives
```

There are three code layers (Interface / Task+Planning / Engine+Steps) over an
edge of repo knowledge and cross-cutting services. The design's "Target layer"
is **not** a code layer: its task-definition role is carried by `TaskSpec` +
`Playbook`, and its only surviving artifact — push authorization — is the
`push.py` safety primitive (sibling of `scopes.py`).

- **Engine is a substrate, not a pipeline.** It provides a vetted step library,
  task-agnostic execution guarantees (checkpoint/resume, typed failure routing,
  scope enforcement, escalation, RunTrace), and a plan→execute loop. It does not
  hold repo knowledge and does not let the planner compose raw tools.
- **Knowledge lives at the edge.** Repo-specific facts (modules, CI, prompts,
  conventions, push policy) live under `plugins/<repo>/` (manifest + profile),
  never in the core. Adding a repo is an edge addition, not a core change.

## 4. Dependency rules (enforced layering)

Imports may only point **down and outward**. Verified constraints a change may
not violate:

1. Leaf edge packages (`profiles/`, `ci/`, `plugins/`, `review/`, `memory/`)
   and safety primitives (`scopes.py`, `push.py`) MUST NOT import `engine/`.
   The engine depends on them.
2. Interface (`cli.py`, `chat.py`) MUST NOT be imported by any lower layer.
   `chat.py` may reference `cli.Copilot` under `TYPE_CHECKING` only.
3. `engine/step.py` is the base vocabulary: it may depend only on `run_trace`
   and `scopes`. Nothing task- or repo-specific.
4. `engine/steps/*` compose tools and edge packages; they reach the agent
   runtime via `engine.agent_runtime`. A step MUST NOT be imported by the
   engine substrate (steps sit above it).
5. Cross-step shared helpers live in `engine/steps/_common.py` — step modules
   MUST NOT import each other (the old `pr_steps -> builtin_steps` late import
   is gone and may not return).

## 5. Scope

**In scope:** the seven task kinds above; a single orchestration engine;
repo-profile establishment/maintenance; conversational + flag CLIs; multi-repo
support via profiles; safety guardrails (plan/patch review, scope enforcement,
push guard, escalation); per-run metrics.

**Out of scope (by design):** reimplementing the nightly rebase (it is
delegated, wrapped-not-rewritten); a general agent framework; running paid
evals from inside the app (eval harness is offline machinery in `eval/`);
being a forge other than what a CI/forge adapter declares; storing secrets
(only `.env`, git-ignored, never committed).

## 6. Data & artifacts (the ground truth)

- **Per run** — `~/.omni-copilot/runs/run-<ts>/`: `run_trace.jsonl` (append-only
  facts), `progress.json` (step checkpoints), `RUN_REPORT.md`, `metrics.json`,
  `ESCALATION.md` (only when blocked), plus step-specific artifacts
  (`rebase_status.json`, `COMPARISON.md`, evidence archives).
- **Per repo (knowledge)** — `plugins/<repo>/`: `plugin.yaml` (identity, human-
  gated sections), `profile/` (`profile.yaml`, `PROFILE_REPORT.md`,
  `JUDGE_REPORT.md`, `ops_log.jsonl`, `format.yaml`/`review.md`/… as
  established), `skills/`, `store/debug_memory.db`, `repo_map/` cache.
- **Governance rule:** RunTrace/evidence are the immutable layer; the profile is
  the curated layer over it. Facts summarize evidence, never replace it.

## 7. Safety model (defense in depth)

Five independent gates, ANDed — a change may strengthen but not remove any:

1. **Tier from kind** — NL/user text can never widen permissions
   (`_CONSTRAINTS.md` C1).
2. **Plan review** — adapted/generated plans are reviewed before execution;
   generation is structurally barred from write/push steps.
3. **ToolScope/PathScope** — every tool call passes one dispatcher; out-of-scope
   writes execute but are recorded, never silent.
4. **Patch review** — conditional on 7 risk triggers, fail-closed before pushes.
5. **Push guard** — one choke point; protected branches never pushed to; force
   is with-lease only; dry-run unless `ALLOW_PUSH=1`.

Blocked runs write `ESCALATION.md`, notify, and exit 3 — notify, never guess.

## 8. Repo invariance (the multi-repo contract) [partly planned]

Quality on a profiled repo must stay within a declared band of the reference
repo, and onboarding a repo requires **zero** edits under `src/omni_copilot/`.
Enforced by: repo-neutral core (`test_repo_neutral_core`), capability-matched
playbooks, explicit `capability_gap` degradation, per-repo knowledge
namespacing. Measured by the cross-repo eval + invariance index
(`eval/invariance.py`) — the eval campaign itself is `[planned]`.
