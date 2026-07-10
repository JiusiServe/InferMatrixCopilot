# Design

This repo implements the **vLLM-Omni Copilot** design
(`vllm-omni-rebase-agent/docs/copilot/copilot_design`, plus its
`implementation/` milestone plan). This document maps the design onto the code
here; the rationale lives in those source docs.

Part I below describes the v1 architecture as built. **Part II (Design v2,
2026-07-10)** extends it with three goals: fix the known v1 problems, make the
copilot **repo-invariant** (stable task performance across repositories), and
give it the ability to **establish a repo profile** (code format, skills,
constraints, module analysis, and supporting artifacts) for any repository it
is pointed at.

---

# Part I — v1 architecture (as built)

## Architecture

```
 user NL ──► intent.py ──► TaskSpec (task_spec.py)          §3.Y CLI layer
                              │  tier fixed by kind (L0/L1/L2), confirm gates
                              ▼
                     engine/planner.py                      §3.2 reuse>adapt>generate
              reuse ─────────┼───────── generate (read-only kinds only)
                              ▼
                  playbooks/store.py registry               §3.2 candidate/active/locked
                              ▼
                    engine/executor.py                      §3.X engine substrate
        per-step checkpoint/resume · retries · typed failures · escalation
                              ▼
             engine/builtin_steps.py (Step library)         §3.X.1 Steps
      tools.py + scopes.py (ToolScope/PathScope choke point) §3.3(2)
      review/ (diff summary → triggers → read-only reviewer) §3.3(3)
      memory/ (RunTrace, DebugMemory FTS5, gated skills)     §3.3(4)
      plugins/ (repo knowledge, draft bootstrap)             plugin layer
      push.py  (PushPolicy + guard_push)                     push authorization
      notify.py (ESCALATION.md + email, exit 3)              goal #4
```

## Key decisions

1. **Wrap, don't rewrite the rebase.** The locked `repo-rebase` playbook
   delegates to the existing 5-phase orchestrator via `rebase.run_external`
   (`REBASE_ORCHESTRATOR_CMD`). Zero regression: this repo adds orchestration
   *around* the proven pipeline, it does not fork it. Native step-level
   decomposition of the rebase (waves, module agents) migrates later per the
   milestone plan.
2. **Own executor instead of LangGraph.** The design (§3.X.5) is explicit that
   LangGraph is a possible backend, not the domain abstraction. The executor
   here is ~150 lines, async, with per-step checkpoint/resume — dependency-free
   and fully testable. A LangGraph backend can be swapped in behind the same
   `Playbook`/`StepSpec` contracts if/when this merges with the parent agent.
3. **Tier is derived, never parsed.** `TaskSpec` has no tier field an LLM or
   user could set; `tier` is a property of the task kind. Natural language can
   therefore never widen permissions (§3.Y.4).
4. **Generation is structurally read-only.** The planner's generate path
   raises if any composed step has `risk` ∈ {write_workspace, push}; write-capable
   kinds without a vetted playbook escalate instead of improvising.
5. **Fail-closed reviews.** `run_patch_review` returns `unavailable` without a
   reviewer LLM; unparseable reviewer output degrades to `revise`. Push gates
   treat anything but `lgtm` as not-passing.
6. **Untrusted data is fenced.** GitHub-fetched text enters agent prompts inside
   `<untrusted_data>` markers with an explicit "not instructions" preamble, and
   only terminal input reaches the intent parser (channel separation, §3.Y.4).
   Intent classification is **LLM-only** (no deterministic keyword parser); a
   low-confidence or suspicious command clarifies rather than runs, and no
   configured LLM → clarify (never a guessed execution). Injection resistance
   comes from channel separation, not from the parser.

## Module map

| Path | Design concept |
|---|---|
| `src/omni_copilot/task_spec.py`, `intent.py`, `cli.py` | §3.Y conversational CLI, TaskSpec, clarify-not-guess (intent classification is LLM-only) |
| `src/omni_copilot/engine/step.py`, `registry.py` | §3.X Step abstraction, vetted step library |
| `src/omni_copilot/engine/executor.py` | engine substrate: checkpoint/resume, typed failure routing |
| `src/omni_copilot/engine/planner.py` | §3.2 reuse > adapt > generate, L0/L1/L2 |
| `src/omni_copilot/engine/builtin_steps.py` | initial step palette (guard, rebase, review gate, push, gh reads, agent steps) |
| `src/omni_copilot/engine/agent_runtime.py` | unified Agent-Step runtime (修正方案): AgentDispatchContext, evidence pack (cap+archive), skill/memory retrieval + gated candidates, enforced scopes, structured output contract, full RunTrace; `run_agent_step_ensemble` — perspective-diverse fan-out + verify-and-merge for run-to-run robustness (eval-informed; any list-output agent step) |
| `src/omni_copilot/playbooks/store.py`, `playbooks/*.yaml` | Playbook registry: versioned, provenance, candidate/active/locked/retired |
| `src/omni_copilot/scopes.py`, `tools.py`, `agent_loop.py` | 框架层改进 (2): ToolScope/PathScope at one choke point |
| `src/omni_copilot/review/` | 框架层改进 (3): diff summary → trigger rules → read-only patch reviewer |
| `src/omni_copilot/run_trace.py`, `memory/` | 框架层改进 (4): RunTrace / DebugMemory / gated skills |
| `src/omni_copilot/plugins/` | RepoPlugin: plugin zero, registry, deterministic bootstrap → draft |
| `src/omni_copilot/push.py` | Push authorization: `PushPolicy` + unified `guard_push` (no separate Target layer) |
| `src/omni_copilot/notify.py` | goal #4: escalation channel, blocked exit code 3 |

## Data & artifacts per run

`~/.omni-copilot/runs/run-<ts>/`: `run_trace.jsonl` (facts), `progress.json`
(step checkpoints — resume re-enters the first incomplete step),
`RUN_REPORT.md`, `ESCALATION.md` (only when blocked).

---

# Part II — Design v2: repo-invariant copilot (2026-07-10)

v1 already states the multi-repo success criterion ("onboarding a second repo
must not touch the core engine — only a new plugin"). v2 strengthens it from
*runs at all* to **runs with stable, measured performance**, and closes the
gaps that currently make that impossible. Three workstreams:

1. **§V2.1 Fix the existing problems** — correctness bugs, repo-knowledge
   leaks into the core, and v1 boundaries left open.
2. **§V2.2 Repo invariance** — an enforceable contract that the engine is
   repo-neutral and that quality is measured per repo, not assumed.
3. **§V2.3 Repo profile** — the copilot can establish, maintain, and consume
   a full profile of any repo: code format, skills, constraints, module
   analysis, and the other artifacts tasks need.

## V2.0 Prior art and evidence (survey, 2026-07-10)

What the field has learned about repo context for agents — each point below
changed a v2 decision. Sources at the end of the section.

1. **Auto-generated repo context files HURT.** The ETH Zurich study
   ([arXiv:2602.11988](https://arxiv.org/html/2602.11988v1), 438 tasks,
   4 agents) found LLM-generated AGENTS.md-style files *reduce* resolve rates
   (−0.5 to −2%) while adding 20–23% inference cost and 2–4 extra steps;
   agents dutifully follow the extra instructions (more greps, more tests)
   without accuracy gains. Codebase/directory overviews — present in ~100% of
   generated files — showed **zero** effect on how fast agents reach the
   relevant code. Human-written files help only mildly (+4%) and only when
   they carry *non-redundant, repo-specific tooling facts* (which package
   manager, exact build/test commands); when the same info already exists in
   README/docs, the context file is pure cost. GitHub's own guidance for
   `copilot-instructions.md` agrees: start with 10–20 short imperative
   directives, iterate against observed behavior.
   → **v2 consequence**: the profile is NOT a prompt dump. Most of it must be
   machine-consumed or retrieved-on-demand; the always-on prompt slice is
   minimal, curated, and must prove itself on the eval (§V2.3.4, §V2.3.5).
2. **The useful "map" is computed per task, not written once.** Aider's repo
   map (tree-sitter symbol graph + personalized PageRank, sized to a token
   budget per conversation) and the RepoGraph line
   ([arXiv:2410.14684](https://arxiv.org/html/2410.14684v1), +32.8% relative
   on SWE-bench; CodexGraph [arXiv:2408.03910](https://arxiv.org/abs/2408.03910))
   both show repo *structure* pays off as a queryable graph ranked against
   the current goal — not as a static overview document.
   → **v2 consequence**: `modules.yaml` is a machine artifact (feeds
   fan-out, patch triggers, wave scheduling) plus an on-demand `repo_map`
   tool for agent steps; it is never injected wholesale into prompts.
3. **Trigger-gated knowledge beats always-on knowledge.** OpenHands
   microagents/skills (keyword-triggered .md files), Devin's Knowledge Base
   (every item = content + a *trigger description*, recalled semantically
   when relevant), and Agent Workflow Memory
   ([arXiv:2409.07429](https://arxiv.org/html/2409.07429v1), workflows
   induced from successful trajectories, +24.6–51.1% relative on web-agent
   benchmarks and robust cross-domain) converge on the same shape: small
   knowledge units, each carrying its own recall condition, injected only
   when triggered. Our skills store already has this shape — v2 extends it
   with per-repo namespacing and induction from successful RunTraces.
4. **Per-repo performance variance is the norm, not the exception.**
   SWE-bench-family analyses show resolve rates swinging from <10% to >50%
   across repositories for the same model, systematic language effects, and
   sizable drops on private/unseen codebases (e.g. Opus 4.1 22.7%→17.8% on
   SWE-bench Pro's private set). Repo properties — architectural complexity,
   plugin/hook systems, API surface clarity — predict difficulty.
   → **v2 consequence**: invariance must be *measured* per repo (§V2.2.5);
   an agent that is only ever evaluated on vllm-omni has unknown performance
   everywhere else, and profile quality is a first-order lever on the gap.
5. **Curated-top-layer-over-evidence is the converging memory architecture.**
   The 2026 agent-memory literature and shipping systems (Zep/Graphiti, Mem0,
   Letta sleep-time agents; continuous LLM rewriting *corrupts* memory —
   arXiv:2605.12978) converge on: an immutable evidence store under a small,
   curated, human-readable profile; typed patch operations as the only write
   surface; scheduled (not per-interaction) consolidation; provenance and
   stability scores gating rewrites. Our own personal-agent implements
   exactly this and it works in production (§V2.3.2 borrows its skeleton).

Sources: [ETH AGENTS.md study](https://arxiv.org/html/2602.11988v1) ·
[Aider repo map](https://aider.chat/docs/repomap.html) ·
[RepoGraph](https://arxiv.org/html/2410.14684v1) ·
[CodexGraph](https://arxiv.org/abs/2408.03910) ·
[OpenHands repo skills](https://docs.openhands.dev/overview/skills/repo) ·
[Devin Knowledge/DeepWiki](https://docs.devin.ai/work-with-devin/deepwiki) ·
[Agent Workflow Memory](https://arxiv.org/html/2409.07429v1) ·
[SWE-bench Pro](https://scale.com/blog/swe-bench-pro) ·
[Cline memory bank](https://docs.cline.bot/best-practices/memory-bank) ·
[Copilot custom instructions](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)

## V2.1 Existing problems and fixes

### (a) Correctness bugs (P0 — fix before anything else)

| # | Problem | Evidence | Fix |
|---|---|---|---|
| 1 | **Resume loses in-memory state.** Steps hand results to later steps by writing `ctx.state` directly (`pr.fetch_diff` → `diff_text`, `issue.fetch` → `issue_text`, `pr.gate_check` → `gate_report`, `pr.checkout_branch` → `push_policy`/branch refs, `agent.review_diff` → `review_text`), but the executor's resume path restores only `outputs.state_updates`. `--resume` past a completed fetch re-enters `agent.review_diff` with no `diff_text` → spurious BLOCKED; resuming pr-rebase at the push step sees the default (deny-all) `PushPolicy` → spurious FORBIDDEN. | `executor.py` resume branch vs. `builtin_steps.py`/`pr_steps.py` state writes | Contract: **every state key a later step consumes must be published via `outputs.state_updates`** (JSON-simple; `PushPolicy` serialized). Enforced by a resume-integrity test per playbook: run to step N, drop the process, resume, assert no BLOCKED-on-missing-state at any N. |
| 2 | **`foreach` fan-out drops `state_updates`.** `_merge` re-keys item outputs by index, so `state_updates` published by fan-out items never reach `state.update(...)`. | `executor.py::_merge` | Merge `state_updates` across items explicitly (last-writer-wins per key is acceptable; conflicts traced). Covered by the same resume-integrity test. |
| 3 | **`when:` silently evaluates against TaskSpec only.** A condition on a computed state key (e.g. `has_conflicts`) evaluates false with no error. | `executor.py::_eval_when` | Evaluate against `state` with TaskSpec fallback; unknown key → planning-time error, not a silent skip. |
| 4 | **Per-repo knowledge is designed but not wired.** `RepoPlugin.skills_dir` and `RepoPlugin.debug_memory_db` exist, but `agent_runtime` reads the *global* `settings.skills_dir` / `settings.memory_db` — every repo shares one skill store and one debug memory. | `plugins/base.py` vs `engine/agent_runtime.py::_retrieve_skills/_retrieve_memories` | Resolve knowledge stores through the active plugin/profile first, global shared pool second (§V2.2.6). |
| 5 | **High-risk-module list is hardcoded vLLM-Omni names in core settings**, so the patch-review `high_risk_modules` trigger silently never fires on any other repo. | `config.py::high_risk_modules` | Move to the profile (`modules.yaml` risk tiers, §V2.3); the setting becomes a fallback only. |

### (b) Repo-knowledge leaks in the core (violate "knowledge at the edge"; block invariance)

These are not bugs on vllm-omni, but each one is a place where a second repo
gets silently degraded behavior. All are resolved by **profile injection**
(§V2.3) — the core keeps only repo-neutral scaffolding:

- `_REVIEW_SYSTEM` and `_REVIEW_LENSES` hardcode "vLLM-Omni" and a
  Python/ML-repo review checklist inside `engine/builtin_steps.py`. → Split
  into a repo-neutral core prompt + profile-supplied domain sections
  (`review.md`: domain checklist, lens extensions, severity norms).
- `_sweep_targets` assumes Python surface syntax (`xs[0]`, `elif`,
  `tests/` layout). → Language-keyed extractor selected by
  `profile.language`, with a generic diff-heuristic fallback.
- `TaskSpec.repo` / `Settings.default_repo` default to `"vllm-omni"`; the
  intent parser cannot extract a repo at all ("review pr 12 in repo-b" is
  unparseable). → Intent gains repo extraction; default comes from the single
  configured profile when only one exists.
- Playbooks declare `repos: [vllm-omni]`, so a second repo needs copy-pasted
  playbooks that will drift. → Repo-neutral playbooks (§V2.2.3).
- `gh` is assumed as the only forge and Buildkite handling is scattered/stub.
  → Forge/CI adapters declared by the profile (§V2.2.4).

### (c) v1 boundaries to close

- **Buildkite log download** (stubbed; PR-debug reads `gh pr checks` only) →
  a `CIProvider` adapter interface (fetch failing jobs, download logs, poll a
  build), implementations for GitHub Actions and Buildkite, selected by
  `profile.ci.provider`. The parent rebase-agent's known baseline-signature
  weakness (exact-string compare misclassifying flaky/known failures) must
  not be inherited: signature matching in the adapter is normalized
  (timestamps/hashes/paths stripped) before comparison.
- **Metrics feedback collectors** (per METRICS_RESEARCH roadmap): gh
  collector filling useful/accepted/conflict online, post-push CI snapshot.
- **Native-rebase prelude env export** mutates the copilot's own process env
  → run the prelude/phases in a subprocess with an explicit env, keeping the
  traced `env_exported` delta.
- **Ensemble coverage**: `run_agent_step_ensemble` is wired only for review.
  Triage and debug-hypothesis steps adopt lens ensembles once their run-to-run
  variance is measured (same replicate-mean discipline as the review
  campaign; do not ship unmeasured "improvements").

## V2.2 Repo invariance

**Definition.** For every task kind the copilot supports, quality on a new
repo with an established profile stays within a declared band of the
reference repo (vllm-omni), and onboarding a repo requires zero core-code
changes. Invariance is a *contract plus a measurement*, not an aspiration —
the benchmark literature (§V2.0.4) shows same-model resolve rates swinging
<10%→>50% across repos, so unmeasured cross-repo claims are worthless.

1. **Repo-neutral core, enforced.** No repo-specific literal (repo names,
   module names, domain prompts, absolute paths) anywhere in
   `src/omni_copilot/` — such knowledge lives only under `plugins/<repo>/`.
   Pinned by a `test_repo_neutral_core` test that scans the source for the
   known-leak patterns and fails on new ones. Prompts in the core may state
   *how to review/debug/triage*; only the profile states *what this repo is*.
2. **Single injection path.** Everything repo-varying reaches steps through
   the DispatchContext `profile` section (§V2.3.4): domain prompt sections,
   module map, risk tiers, test/format commands, CI/forge adapters,
   conventions. A step that needs repo knowledge and finds none in the
   profile must degrade explicitly (see 4), never guess.
3. **Repo-neutral playbooks.** Playbooks declare `repos: ["*"]` plus a
   `requires:` list of profile capabilities (e.g. `ci.provider`,
   `upstream.fork_tracking` for repo-rebase). `PlaybookStore.find()` matches
   task kind + capability satisfaction instead of repo name; a repo-specific
   playbook override (exact repo match) still wins when present. The locked
   `repo-rebase` playbook stays vllm-omni-specific by declaration — it
   `requires` the external orchestrator capability that only the vllm-omni
   profile provides; zero-regression is untouched.
4. **Graceful capability degradation.** Missing capability → a *declared*
   downgrade recorded as a `capability_gap` RunTrace event and surfaced in
   the run report: no CI provider → pr-debug runs report-only triage; no
   upstream declared → repo_rebase refuses at planning time with the reason;
   unknown language → generic sweep extractor, flagged in the review output.
   Degraded ≠ silently worse: every gap is visible.
5. **Measured invariance.** Extend the eval harness to a cross-repo
   benchmark: the same arms and RQS3/RQS3e/CATQ metrics per repo, scored on
   replicate means (the campaign's hard lesson: single rolls are ±0.1 noise).
   Report an **invariance index** = min(repo score) / mean(repo score) per
   task kind; target ≥ 0.8. A new repo's profile is promoted
   (draft → active) only after its eval run lands within the band — the
   profile promotion gate *is* the invariance gate.
6. **Knowledge namespacing.** Skills and debug memories resolve per-repo
   first (`plugins/<repo>/skills/`, `plugins/<repo>/store/debug_memory.db` —
   the already-designed fields from §(a)4), then a shared general pool.
   Writes always land in the active repo's namespace; promotion of a repo
   skill to the shared pool is a curator decision (it must be genuinely
   repo-agnostic, e.g. "how to bisect a flaky test" vs. "HunyuanImage SSIM
   threshold").

## V2.3 Repo profile

The profile generalizes plugin zero + Phase-0 bootstrap into the copilot's
full picture of a repository. Two evidence-driven design rules govern
everything below (§V2.0.1–2):

- **Rule 1 — a profile is not a prompt.** Most profile content is consumed
  by *code* (step logic, adapters, triggers) or retrieved *on demand*; the
  always-on prompt slice is a curated minimum of non-obvious, non-redundant
  directives. Auto-generated overviews injected wholesale are measured to be
  worse than nothing.
- **Rule 2 — no fact without provenance, no rewrite without stability.**
  Every fact cites how it was derived and when it was last confirmed;
  curated summaries are rewritten only by a scheduled consolidation tier,
  never continuously. This is the personal-agent profile architecture, which
  is running in production and whose failure modes (fragmentation,
  evidence dumps, continuous-rewrite corruption) are already mapped.

### V2.3.1 Layout

```
plugins/<repo>/
  plugin.yaml            identity, repo/upstream paths, push policy   (human-gated)
  profile/
    profile.yaml         the curated core (small, human-readable): per-fact
                         provenance fields — see §V2.3.2
    briefing.md          RENDERED always-on prompt slice: 10-30 short
                         imperative directives (tooling commands, hard
                         constraints, known traps). Budgeted (<400 words),
                         non-redundant with repo docs — validated, see §V2.3.5
    format.yaml          formatters/linters + exact commands, naming and
                         comment conventions          (machine: validation cmds)
    constraints.md       protected branches, review/merge norms, required
                         checks, licensing/DCO, never-touch paths (machine:
                         push guard + PathScope; plus briefing lines)
    modules.yaml         module map (paths -> module), import-graph waves,
                         module -> test commands, ownership, risk tiers
                         (machine: fan-out, triggers, scheduling; never
                         injected as prose)
    review.md            domain review checklist + lens extensions + severity
                         norms                        (retrieved by pr_review)
    ci.yaml              provider(s), pipelines, log access, required checks,
                         normalized flaky-signature baseline (machine)
    PROFILE_REPORT.md    rendered provenance view: how each fact was derived
                         (deterministic | agent | human), evidence, confidence
  skills/                per-repo skills, each with a TRIGGER description
                         (Devin-style: content + when to recall it)
  store/debug_memory.db  per-repo debug memory
  repo_map/              cached symbol graph for the on-demand repo_map tool
                         (Aider/RepoGraph-style, ranked per query, token-
                         budgeted; rebuilt on drift)
```

`plugin.yaml` keeps its v1 role and high-risk human-only sections
(`repo`/`upstream`/`push`); `profile/` holds the establishable knowledge.

### V2.3.2 Profile memory architecture (borrowed from the personal agent)

The personal agent (`/rebase/personal-agent`, `profile_store.py` +
`RESEARCH_AGENT_MEMORY_2026.md`) maintains a person-profile with exactly the
lifecycle a repo profile needs. We adopt its skeleton wholesale, translated
to repo terms:

| Personal-agent mechanism | Repo-profile translation |
|---|---|
| Immutable evidence store (`events.db`) under a small curated `profile.yaml` | RunTraces + Stage-1 evidence archives are the immutable layer; `profile.yaml` is the curated layer. Facts summarize evidence, never replace it |
| **Typed patch ops as the only write surface** (`add_evidence`, `bump_last_seen`, `merge_*`, `mark_dormant`; malformed ops rejected) | Profile mutations are typed ops validated by the store (`add_fact`, `add_evidence`, `bump_confirmed`, `merge_facts`, `mark_stale`, `update_command`); agents never free-edit profile files |
| **Two write tiers**: daily additive (no rewrite) vs. weekly consolidation (only tier allowed `rewrite_entry`) — continuous LLM rewriting measurably corrupts memory | Per-run tier: runs may only *add* evidence/candidates. Consolidation tier (scheduled or post-eval): dedupe, merge, rewrite `briefing.md` — the only place prose is regenerated |
| **Join key against fragmentation**: owner-editable `aliases.yaml`; every op must name its initiative | The **module map is the join key**: every profile op names the module (or `repo-wide`) it concerns, so knowledge converges per module instead of fragmenting |
| Provenance per entry: `evidence[]`, `first_seen`, `last_seen`, `confirmations: n` | Same fields per fact, plus `source: deterministic|agent|human` and source commit |
| **Stability gate**: entries with ≥3 confirmations can't be rewritten to cite less evidence | Same rule: a consolidation rewrite may not drop cited evidence from a stable fact; superseded text goes to `history[]`, never deleted |
| **Dormancy decay, never delete** (30/60-day windows) | Facts unconfirmed past their window flip to `stale` (excluded from injection/consumption, kept for audit); refresh re-confirms or retires them |
| Protected sections the LLM cannot touch (`identity`, `preferences`) | `plugin.yaml` high-risk sections (already enforced in `update_manifest`) + human-authored constraint lines marked `source: human` |
| **Read-only LLM judge** (weekly): reports contradictions/stale claims, never auto-fixes | Profile judge audits profile vs. last N RunTraces (commands that failed, modules that moved, checklist items that never fire) — findings become refresh proposals |
| Git repo per profile: every save a commit, weekly diff emailed, `git revert` rollback | `plugins/<repo>/` is committed; every consolidation is one reviewed commit with the diff in the run report — rollback is `git revert` |

### V2.3.3 Establishment pipeline (extends Phase-0 bootstrap)

- **Stage 0 — deterministic fingerprint** (exists: `fingerprint_repo`):
  language mix, layout, CI systems, remotes, default branch. Extended with
  the deterministic parts of `modules.yaml` (directory clustering,
  import-graph waves via static analysis) and `repo_map/` construction. No
  LLM, no writes to the target repo.
- **Stage 1 — profiling agents** (new): read-only governed agent steps, one
  per profile artifact, through the unified agent runtime: *structure*
  (module semantics + test mapping on top of the Stage-0 graph), *format*
  (detect config files, infer unwritten conventions, emit exact check
  commands), *constraints* (CONTRIBUTING/CODEOWNERS/PR templates/branch
  protection via forge API), *ci* (pipelines, log access), *review* (domain
  checklist from docs + recent human review threads). Every emitted fact
  must cite its evidence — uncited facts are rejected at the contract layer.
- **Stage 1.5 — redundancy filter** (new, the ETH-study lesson): a
  deterministic pass drops any candidate briefing/checklist line whose
  content is already stated in the repo's README/docs/AGENTS.md (the agent
  reads those anyway) and any codebase-overview prose. What remains is the
  non-obvious residue — tooling commands, traps, invariants. If an
  `AGENTS.md`/`CLAUDE.md`/`.github/copilot-instructions.md` exists, it is
  ingested as *human-authored* briefing input (highest-trust source) rather
  than re-derived.
- **Stage 2 — human review gate** (exists, extended): profile lands as
  `status: draft` + `PROFILE_REPORT.md`; high-risk sections human-only.
  Human review flips draft → candidate.
- **Stage 3 — live calibration**: first N runs treat low-confidence facts as
  hypotheses; corrections (module map fixes, commands that actually pass,
  flaky baseline entries) are proposed as candidates through the curator
  gate. Successful-run RunTraces feed **skill induction** (AWM-style):
  recurring resolution patterns become per-repo skill candidates with
  trigger descriptions. Passing the eval band (§V2.2.5 + §V2.3.5) promotes
  candidate → active.
- **Stage 4 — consolidation & refresh** (the personal agent's weekly pass):
  scheduled consolidation dedupes/merges facts per module, regenerates
  `briefing.md` under its word budget, applies dormancy decay; drift
  detectors (module path gone, format command fails, CI pipeline renamed,
  N profile-contradicting runs, judge findings) trigger targeted re-runs of
  the affected Stage-1 agent. One reviewed commit per cycle.

### V2.3.4 Consumption: three channels

The ETH result forces the discipline; every artifact declares its channel:

1. **Machine-consumed (never prose-injected)**: `modules.yaml` → fan-out,
   wave scheduling, patch-review `high_risk_modules`, retrieval queries;
   `format.yaml` → post-edit validation commands run before the patch gate;
   `ci.yaml` → adapter selection, required-checks list, flaky filtering;
   `constraints.md` machine lines → push guard + PathScope.
2. **Always-on prompt slice**: only `briefing.md` (word-budgeted, curated,
   redundancy-filtered) enters every DispatchContext for the repo, plus the
   handful of constraint lines relevant to the step's risk level.
3. **Triggered/on-demand**: per-repo skills recalled by trigger match;
   `review.md` retrieved only by pr_review steps; the `repo_map` tool
   answers structure queries ranked against the step's goal under a token
   budget — agents pull structure when they need it instead of being fed an
   overview.

### V2.3.5 Profile efficacy is measured, not assumed

The same study showed even human-written context files can be net-negative
per repo. So the profile itself is an eval arm: on each profiled repo, the
task-kind eval runs {no profile} vs {profile} (replicate means, as always).
A profile (or a briefing revision) is promoted only if it is non-negative on
quality **and** does not blow the cost budget (CATQ's C term already prices
the +2–4 extra steps context files induce). Consolidation-tier briefing
rewrites re-run the ablation. This closes the loop that AGENTS.md authors
skip: we never assume injected context helps.

### V2.3.6 Governance

No new machinery — profiles reuse the existing gates: profile edits are
knowledge edits (already a patch-review trigger); agents propose typed-op
candidates only (`update_manifest` already rejects agent writes to high-risk
sections); draft/candidate/active/retired mirrors the playbook lifecycle;
every accepted fact is traceable via `PROFILE_REPORT.md`; every
consolidation is one reviewed, revertable commit.

## V2.4 Milestones and acceptance

- **P0 — correctness**: §V2.1(a) fixes + resume-integrity test per playbook +
  `test_repo_neutral_core` (initially xfail-listing the known leaks so the
  list can only shrink).
- **P1 — profile substrate**: profile store with typed patch ops +
  provenance fields (§V2.3.2), `profile/` schema + loader, Stage-0/1
  establishment + Stage-1.5 redundancy filter + PROFILE_REPORT,
  DispatchContext `briefing` injection, review/sweep/intent
  parameterization off the profile (de-leaking §V2.1(b)).
- **P2 — repo-neutral execution**: playbook `requires:` capability matching,
  CI/forge adapter interface (GitHub Actions + Buildkite), capability-gap
  degradation paths, per-repo knowledge namespacing wired, `repo_map`
  on-demand tool.
- **P3 — measured invariance**: cross-repo eval harness (reference repo + at
  least one structurally different second repo), invariance index reporting,
  **profile ablation arm** (§V2.3.5), promotion gates bound to the eval
  band; Stage-3 live calibration + AWM-style skill induction; Stage-4
  consolidation/judge/refresh loops on a schedule.

**Acceptance criteria**

1. A second repository is onboarded end-to-end (fingerprint → profile →
   active) with **zero commits to `src/omni_copilot/`**.
2. All six task kinds execute on the second repo — at full capability where
   the profile provides it, and with *recorded* `capability_gap` degradation
   where it does not; no silent quality loss.
3. pr-review RQS3 (replicate mean) on the second repo within the declared
   band of the vllm-omni reference; invariance index ≥ 0.8.
4. Resume-integrity tests green for every playbook (no BLOCKED/FORBIDDEN
   caused by resume itself).
5. The locked `repo-rebase` nightly remains byte-identical in behavior
   (zero-regression constraint carries through v2 unchanged).
6. The profile earns its keep: on every profiled repo the {profile} eval arm
   is non-negative vs {no profile} on quality at acceptable cost (§V2.3.5),
   and every `briefing.md` stays within budget with zero doc-redundant lines.
