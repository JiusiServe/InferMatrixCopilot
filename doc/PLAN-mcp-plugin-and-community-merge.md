# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo adapter contribution

Status: PROPOSED, revision 2 (planning only — nothing here is executed yet).
Revised after an external review (GPT) whose technical claims were confirmed
against the code (`cli/copilot.py`, `tracing.py`, `run_trace.py`). The changes
from rev 1 are summarized at the end.

Two independent workstreams. WS2 opens a PR against a repo we do not own and
therefore needs owner sign-off before the PR is filed.

---

## Workstream 1 — expose the copilot as an MCP server (Claude Code + Codex), keep standalone CLI

### Goal
One MCP server that exposes the copilot's governed **read-only** task kinds as
tools, usable from **both** Claude Code and Codex, while the `omni-copilot` CLI
keeps working unchanged. MCP is the only boundary both hosts speak; plugins are
Claude-Code-only, `AGENTS.md` is Codex-only. The whole governed pipeline
(scopes, plan-review, `guard_push`) stays **inside** the server — the host calls
it as a black-box capability and cannot widen its permissions.

### Non-goals (MVP)
- **No outward writes at all in v1.** No posting comments, no pushing. Debug is
  `report_only` only; review/issue/triage are read-only by construction. An MCP
  host toggling a `report_only=False` flag is **not** meaningful human approval,
  so we do not expose that surface until a later, explicitly human-gated
  release. (Matches the owner rule: reviewer is eval-only; never post/push
  without approval.)
- **stdio transport only.** No streamable-HTTP in v1 — HTTP pulls in auth,
  tenancy, persistence, and cancellation, none of which the MVP needs.
- Do **not** reimplement the pipeline as a Claude Code subagent (a subagent is a
  prompt+tools config in the host's own loop; it can't host an external agent).
- Do **not** change any existing CLI behavior or default. MCP is purely additive.

### The three lifecycle problems (and their fixes)
A review takes 5–12 min, so a synchronous MCP tool would hit the host's call
timeout: the shape must be **start + poll**. Rev 1 assumed the existing
`run_task`/`last_run_dir` could carry that. They cannot, for three reasons the
review surfaced and the code confirms:

1. **`run_task` can't return an id at start.** It generates `run_id`
   *after* the plan-review/confirm gate (`copilot.py:150`) and then blocks
   through `asyncio.run(executor.run(...))` to a bare exit code. A poll handle
   must exist *before* the run finishes.
   → **Fix:** split the run into two methods on `Copilot`:
   - `prepare_run(spec, *, assume_yes=True) -> PreparedRun` — resolve, run the
     plan-review gate, `mkdir` the run dir, write `task.json`, write an initial
     `run_status.json {state: "queued"}`, and return `{run_id, run_dir,
     resolution}` **immediately** (no execution).
   - `execute_prepared(prepared) -> int` — the current `_execute` body, called by
     the CLI inline and by the MCP server in a worker thread.
   `run_task` becomes `prepare_run` + `execute_prepared` composed, so the CLI
   path and all 227 tests are unchanged.

2. **Completion/failure is not detectable from files.** `RUN_REPORT.md` and
   `ESCALATION.md` are written only on the success and blocked paths; an
   exception in `executor.run` leaves neither, so polling for those files cannot
   distinguish "still running" from "crashed."
   → **Fix:** a durable, atomic `run_status.json` per run dir, written
   tmp-file-then-`os.replace`, transitioning `queued → running →
   {done|blocked|failed}` with the terminal write in a `finally` (so even an
   exception records `failed` + the traceback tail). `get_result` reads
   `run_status.json` as the source of truth, then attaches `RUN_REPORT.md` /
   `ESCALATION.md` when present. This is also the **durable run record** that
   replaces any in-memory run-id map — the server stays stateless across
   restarts by globbing `run_root` and reading each `run_status.json`.

3. **Two concurrent runs corrupt each other.** `self.last_run_dir` is shared
   mutable `Copilot` state, and — the real hazard — `tracing.init()` installs a
   **module-global** default tracer (`tracing.py:168–177`), so a second run's
   `init` clobbers the first and *all* `trace.jsonl` spans cross-route. (The
   per-run `RunTrace` writing `run_trace.jsonl` is safe; only the `tracing`
   module's `trace.jsonl` is the global hazard.)
   → **Fix (MVP):** **serialize** execution — a single worker/`asyncio` lock so
   at most one run executes at a time; concurrent `start_*` calls enqueue and
   return `queued` ids immediately (poll still works). Real parallelism is a
   later, separate change: make the `Tracer` run-scoped (thread the instance
   through `_execute` instead of the module global) and remove `last_run_dir`
   from the concurrent path.

### Tools exposed (v1, all read-only)
- `start_review(pr, repo) -> run_id` · `start_issue_answer(issue, repo) -> run_id`
- `start_issue_triage(repo) -> run_id` · `start_debug(pr, repo) -> run_id`
  (always `report_only=True`; the flag is not exposed)
- `get_result(run_id) -> {state, report?, escalation?}` (reads `run_status.json`)
- `get_status(run_id) -> progress` (reads `progress.json`) · `list_playbooks()`

### Phases & deliverables
1. **Programmatic surface** (`cli/copilot.py`): the `prepare_run` /
   `execute_prepared` split above + the atomic `run_status.json` writer. ~50
   lines; no behavior change to the CLI path (verified by the existing suite).
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): official `mcp` SDK
   (FastMCP) over **stdio**. `start_*` tools call `prepare_run`, launch
   `execute_prepared` on the single serialized worker, and return
   `run_id = run_dir.name`; `get_result` maps `run_status.json` → response.
   New `omni-copilot-mcp` console-script behind an **optional extra** in
   `pyproject.toml` (`pip install -e ".[mcp]"`), so standalone installs stay
   dependency-free.
3. **Packaging — Claude Code plugin** (`plugin/`): `.claude-plugin/plugin.json`,
   an `.mcp.json` that starts the stdio server, and thin convenience skills
   (`skills/pr-review/SKILL.md` → `start_review` then poll). **Prerequisite made
   explicit:** installing a plugin does *not* install the Python package, so the
   `.mcp.json` command must resolve — either document a one-time
   `uv tool install` / `pipx install` of `omni-copilot`, or make the command
   `uvx --from git+https://…/vllm-omni-copilot omni-copilot-mcp`. Exact
   marketplace/`/plugin` install syntax is **to be verified against current
   Claude Code docs** before we write it down (rev 1's `github:…` form was
   invented) — the always-available raw path is `claude mcp add`.
4. **Packaging — Codex**: a `docs/codex/config.toml` snippet for
   `[mcp_servers.omni_copilot]` (command/args/env) + an optional `AGENTS.md`.
   Codex gets no plugin (MCP + AGENTS.md only).
5. **Tests** (offline, extend the 227-test suite):
   - `prepare_run` returns an id + a `queued` `run_status.json` without executing.
   - state machine: `run_status.json` goes `queued → running → done`, and an
     injected exception in `execute_prepared` lands `failed` (not a hang).
   - MCP tool schemas present + typed (fake Copilot; no LLM); `get_result` on an
     unknown id is a clean error, not a crash.
   - serialization: two `start_*` calls don't interleave (one `running`, one
     `queued`); no post/push tool exists in the schema set.
   Plus one **live smoke**: `start_review` on a small merged PR, poll to `done`.
6. **Docs**: `doc/CODE_TOUR.md` §11 gets an MCP-server entry; new `doc/MCP.md`
   install/registration reference (both hosts, package-install prerequisite).

### Acceptance
- `omni-copilot -p "review pr N"` unchanged (all existing tests green).
- `pip install -e ".[mcp]"` then `omni-copilot-mcp` serves over stdio; both
  hosts connect; `start_review` → poll → real `RUN_REPORT` text.
- No post/push tool exists in v1; every run has a terminal `run_status.json`
  even on crash.

---

## Workstream 2 — contribute our adapter's net-new knowledge to `zuiho-kai/claude-workflow-starter` (fork → PR)

### Goal (narrowed)
**Knowledge-only PR first.** Contribute the copilot's *net-new* vllm-omni
knowledge into the community repo, as pages placed by *their* `layout.md`, each
with provenance — and nothing else. The broad reorganization from rev 1 is
**dropped from the initial PR**: an audit of their tree showed it already follows
its own `layout.md`, so a reorg is unrequested churn that raises maintainer
friction and collides with the "don't modify their info" constraint.

### Why the rev-1 reorg is gone
Rev 1 promised both "preserve every existing byte" **and** "repair `_index.md`
navigation + fix cross-links." Those contradict: editing an index *is* modifying
their content. Resolving it cleanly means **not** touching their existing pages
at all. So:
- The PR **adds new files only**. Existing pages are not moved, renamed, or
  edited.
- Surfacing the new pages in navigation is done with the **minimum** change that
  their `CONTRIBUTING`/`layout.md` require — ideally by adding a link line to the
  relevant `_index.md`. If even that is unwelcome, we add the pages and let the
  maintainer wire navigation (call it out in the PR). Either way we make no edit
  to any *knowledge* content.
- A **separate, later, optional** reorganization PR is proposed only if a
  concrete organizational problem is found — proposed, not imposed.

### Dedup against provenance loops (unchanged, still a hard gate)
Several of our adapter facts were *ingested from this very repo* (provenance
`community:zuiho-kai/…`). Those must NOT be contributed back. Only **net-new**
copilot knowledge — derived from vllm-omni code + eval ground truth (removed-API
sweep, PR-time review discipline, run-level/dummy-weights trap, stage-capacity
checks) — is eligible. A `MERGE-MATRIX.md` classifying each of our facts as
`already-in-theirs` / `sourced-from-theirs` (both → drop) vs `net-new` (→
contribute) ships in the PR for reviewer transparency.

### Format: their book, not our machine tree
Their repo is a human-readable knowledge book; our adapter is the copilot's
machine format (`profile.yaml`, `manifest.yaml`, …). "Contribute" means
**translate** our net-new curated facts into their markdown pages, placed by
`layout.md`. We do **not** drop our raw `profile.yaml` as a parallel machine
tree (their convention forbids it, and the default answer to rev-1's open
question is book-form-only).

### Phases & deliverables
1. **Fork & branch**: fork `zuiho-kai/claude-workflow-starter` → `tzhouam`;
   clone; branch `feat/vllm-omni-net-new-knowledge`.
2. **Audit / dedup matrix**: enumerate their `repos/vllm-omni/**` vs our adapter
   facts; produce `MERGE-MATRIX.md`; keep only `net-new`.
3. **Author net-new pages**: write each as a new page placed by `layout.md`,
   carrying provenance (`vllm-omni code @<sha>` / `eval GT #<n>`), *linking* to
   (never duplicating) any existing owner page. Respect their `page-rules.md` /
   `validation.md` / `CONTRIBUTING.md`.
4. **Minimal navigation**: add link lines for the new pages to the appropriate
   `_index.md` **only if** their contribution rules require it; touch no
   knowledge content. A pre/post SHA-256 manifest of every pre-existing file is
   attached to prove no existing page changed.
5. **Contribution hygiene**: run their linter/validation; match commit
   conventions (DCO/sign-off if required); PR body in **Chinese**, stating:
   "本 PR 仅新增 vllm-omni-copilot 提炼的净新增知识(附溯源),未改动任何现有
   内容;已排除源自本仓库的事实以避免回灌;不含目录重构。"
6. **Open PR**: `tzhouam:feat/vllm-omni-net-new-knowledge` → `zuiho-kai:master`
   — **only after owner sign-off** (external repo).

### Acceptance
- Diff is **new files only** (+ at most additive `_index.md` link lines);
  content-hash manifest shows zero edits to any pre-existing knowledge page.
- New pages sit where `layout.md` prescribes, with provenance, no duplication of
  owner content, no re-contribution of `sourced-from-theirs` facts.
- PR is self-explaining (matrix + hash manifest), Chinese body, passes their
  contribution checks.

---

## Sequencing & ownership
- WS1 and WS2 are independent.
- **WS1** is fully within our repo → proceeds on owner's go; delivered as a PR to
  `tzhouam/vllm-omni-copilot` per the standing deliver-as-PR rule. Land it in the
  order of the three lifecycle fixes above (prepare/execute split → status file →
  serialize) so each is independently testable.
- **WS2** touches an external repo → **requires explicit owner approval before
  the PR is opened**; the fork/branch/audit/authoring can be prepared and
  reviewed locally first.

## What changed from rev 1 (per the review)
1. WS1 lifecycle: `run_task_to_dir` → `prepare_run`/`execute_prepared` split so a
   poll id exists at start.
2. WS1 completion: added atomic `run_status.json` terminal states; poll no longer
   infers state from file presence; durable record replaces the in-memory map.
3. WS1 concurrency: **serialized** MVP (named the module-global `tracing` hazard);
   real parallelism deferred behind a run-scoped tracer.
4. WS1 safety: **read-only MVP** — no post/push surface at all in v1.
5. WS1 transport: **stdio only**; HTTP dropped from MVP.
6. WS1 packaging: made the plugin-≠-package prerequisite explicit; removed the
   invented `github:` install syntax (to verify against current docs).
7. WS2: **knowledge-only PR first**; broad reorg dropped (resolves the
   byte-preservation contradiction and respects an already-organized repo); reorg
   becomes a separate, optional, later PR only if demonstrably needed.

## Open decisions (need owner input)
1. WS1: ship the serialized MVP now and defer the run-scoped-tracer concurrency
   refactor, or do the tracer refactor up front so runs can overlap from day one?
2. WS2: may the knowledge PR add link lines to existing `_index.md` files, or
   should it add pages only and leave all navigation wiring to the maintainer?
