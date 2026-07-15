# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo reorg + adapter merge

Status: PROPOSED (planning only — nothing here is executed yet).
Two independent workstreams; Workstream 2 opens a PR against a repo we do not
own and therefore needs owner sign-off before the PR is filed.

---

## Workstream 1 — expose the copilot as an MCP server (Claude Code + Codex), keep standalone CLI

### Goal
One MCP server that exposes the copilot's governed task kinds as tools, usable
from **both** Claude Code and Codex, while the `omni-copilot` CLI keeps working
unchanged. MCP is the only boundary both hosts speak; plugins are Claude-Code-
only, `AGENTS.md` is Codex-only. The whole governed pipeline (scopes,
plan-review, `guard_push`, `ALLOW_POST`/`ALLOW_PUSH`) stays **inside** the
server — the host calls it as a black-box capability and cannot widen its
permissions.

### Non-goals
- Do **not** reimplement the pipeline as a Claude Code subagent (a subagent is a
  prompt+tools config in the host's own loop; it can't host an external agent).
- Do **not** change any existing CLI behavior or default. MCP is purely additive.
- No outward writes by default over MCP (posting/pushing stay double-gated).

### Design
- **Long-running is the hard constraint.** A review takes 5–12 min; a synchronous
  MCP tool will hit the host's call timeout. The copilot already writes each run
  to `~/.omni-copilot/runs/run-<ts>-<uuid>/RUN_REPORT.md` and tracks
  `Copilot.last_run_dir` — a natural **start + poll** shape.
- Tools exposed (start/poll pairs for the slow ones):
  - `start_review(pr, repo) -> run_id` · `start_debug(pr, repo, report_only=True) -> run_id`
  - `start_issue_answer(issue, repo) -> run_id` · `start_issue_triage(repo) -> run_id`
  - `get_result(run_id) -> {status: running|done|blocked, report?: str}` (reads RUN_REPORT.md / ESCALATION.md)
  - `list_playbooks() -> [...]` · `get_status(run_id) -> progress` (read-only introspection)
- **Safety mapping** (non-interactive ⇒ no `[y/N]`): every outward action is an
  explicit tool param + env gate, defaulting off — `post=False`, `report_only`
  defaults true for debug, `ALLOW_POST=0`/`ALLOW_PUSH=0` in the server env.
  The copilot's `_gate_and_confirm`/plan-review still run inside; the host's
  confirmation is *not* a substitute and cannot loosen them.

### Phases & deliverables
1. **Programmatic surface** (`src/omni_copilot/cli/copilot.py`): add a thin
   `run_task_to_dir(spec, *, assume_yes=True) -> Path` (runs `run_task`, returns
   `last_run_dir`) so callers get the run dir without parsing stdout. Reuse the
   existing `/status` progress reader for `get_status`. ~30 lines, no behavior
   change to the CLI path.
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): FastMCP (or the
   official `mcp` SDK) server implementing the tools above over **stdio**
   (default) and optionally streamable-HTTP. Start-tools launch the run in a
   worker thread and return `run_id = run_dir.name`; `get_result` maps run-dir
   state → status. Add `omni-copilot-mcp` console-script + an **optional extra**
   in `pyproject.toml`: `pip install -e ".[mcp]"` (so standalone installs stay
   dependency-free).
3. **Packaging — Claude Code plugin** (`plugin/`): `.claude-plugin/plugin.json`
   (name/description/version), `.mcp.json` (the stdio server), and thin
   convenience skills (`skills/pr-review/SKILL.md` → `start_review` then poll).
   Installable via `claude /plugin install github:tzhouam/...` or a team
   marketplace.
4. **Packaging — Codex**: a `docs/codex/config.toml` snippet for
   `[mcp_servers.omni_copilot]` (command/args/env) + an optional `AGENTS.md`
   with review-workflow rules. Codex gets no plugin (MCP + AGENTS.md only).
5. **Tests** (offline, extend the 227-test suite):
   - MCP tool schemas present + typed (fake Copilot; no LLM).
   - start/poll state machine: `running` → `done` (report present) → `blocked`
     (ESCALATION.md present); `get_result` on an unknown run_id is a clean error.
   - safety: `post`/push params default off; server env forces `ALLOW_POST=0`.
   Plus one **live smoke**: `start_review` on a small merged PR, poll to `done`,
   assert the RUN_REPORT text comes back.
6. **Docs**: extend `doc/CODE_TOUR.md` §11 with an MCP-server entry, and a
   `doc/MCP.md` install/registration reference (both hosts).

### Acceptance
- `omni-copilot -p "review pr N"` unchanged (all existing tests green).
- `pip install -e ".[mcp]"` then `omni-copilot-mcp` serves; `claude mcp add` and
  `codex mcp add` both connect; `review_pr` returns a real RUN_REPORT via poll.
- No outward write possible without an explicit param **and** env flag.

### Risks / mitigations
- **Host call timeout on a 10-min review** → start/poll split (primary), MCP
  Tasks primitive as a later option. Never return synchronously.
- **`mcp` dependency creep on standalone installs** → gate behind the `[mcp]`
  extra; core imports stay clean.
- **Concurrency** (host fires several tools) → each run already gets its own
  uuid run-dir; the server holds no shared mutable state beyond a run-id map.

---

## Workstream 2 — reorganize `zuiho-kai/claude-workflow-starter` + merge our adapter (fork → PR)

### Goal
Make the community repo's information **clearer and better organized**, and
**merge our local `adapters/vllm_omni/` knowledge into it** — via a PR from our
fork. Two hard constraints:
- **Do NOT modify their existing information.** Reorg = moves + navigation +
  grouping only (content bytes preserved); merge = *adding* our net-new facts.
- Follow **their own** `contributing/layout.md` placement rules (one canonical
  knowledge tree; single source of truth; machine info stays in ignored
  `local/`, no parallel private tree).

### Format reconciliation (the crux)
Their repo is a **human-readable knowledge book** (`framework/<topic>/`,
`repos/vllm-omni/<topic>/`, `components/`, `models/`, `_index.md`, `rules.md`,
`guides/`, `incidents/`). Our adapter is the copilot's **machine format**
(`manifest.yaml`, `profile.yaml` typed facts with provenance, `review.md`,
`constraints.md`, `ci.yaml`, `modules.yaml`). "Merge" therefore means
**translate our curated facts into their book**, placed by `layout.md`, NOT drop
our raw `profile.yaml` as a second tree (their convention forbids that).
- **Dedup against provenance loops**: several of our facts were *ingested from*
  this very repo (provenance `community:zuiho-kai/...`). Those must NOT be merged
  back (they'd duplicate their own content). Only **net-new** copilot knowledge
  (from vllm-omni code + eval ground truth: e.g. removed-API sweep, PR-time
  review discipline, run-level/dummy-weights trap, stage-capacity checks) is
  contributed.

### Phases & deliverables
1. **Fork & branch**: fork `zuiho-kai/claude-workflow-starter` → `tzhouam`;
   clone; branch `feat/vllm-omni-adapter-merge` (or two branches if the reorg and
   the merge should be separately reviewable — see "open decisions").
2. **Audit / dedup matrix**: enumerate their `repos/vllm-omni/**` files vs. our
   adapter facts; classify each of ours as `already-in-theirs` /
   `sourced-from-theirs` (both → drop) vs. `net-new` (→ merge). Output a
   `MERGE-MATRIX.md` in the PR for reviewer transparency.
3. **Layout clarity pass (zero content edits)**: repair/add `_index.md`
   navigation, group loose pages under the correct `framework/` vs
   `repos/vllm-omni/<topic>/` vs `components/` vs `models/` per *their*
   `layout.md`, and fix cross-links. **All moves via `git mv`, never rewrite** —
   a per-file content hash before/after proves bytes are unchanged.
4. **Merge net-new facts**: write our net-new knowledge as new pages in their
   book, placed by `layout.md`, each carrying provenance
   (`vllm-omni code @<sha>` / `eval GT #<n>`), and only *linking* to (never
   duplicating) any existing owner page. Respect their `page-rules.md` /
   `validation.md` / `CONTRIBUTING.md`.
5. **Contribution hygiene**: run any repo linter/validation; match their commit
   conventions (DCO/sign-off if required); write the PR body in **Chinese** to
   match the repo, stating explicitly: "布局仅移动/加索引,未改动任何原文;
   仅新增 vllm-omni-copilot 提炼的净新增知识(附溯源),已排除源自本仓库的
   事实避免回灌。" Attach the dedup matrix and a moves-only diffstat.
6. **Open PR**: `tzhouam:feat/vllm-omni-adapter-merge` → `zuiho-kai:master`.

### Acceptance
- Every pre-existing content byte is preserved (verified by a content-hash diff
  that shows only path changes + net-new files, no in-place edits to their text).
- New pages sit in the layout their `layout.md` prescribes, with provenance and
  no duplication of owner content.
- PR is self-explaining (matrix + diffstat), Chinese body, and passes their
  contribution checks.

### Risks / mitigations
- **Accidental content modification** → tooling: `git mv` only; a pre/post
  SHA-256 manifest of all pre-existing files checked in CI-style before PR; if
  any existing file's hash changes, block.
- **Provenance loop (re-merging their own facts)** → the dedup matrix is a hard
  gate; nothing classified `sourced-from-theirs` is contributed.
- **Layout disagreement with the maintainer** → keep the reorg and the
  content-merge on separate commits (or PRs) so they can accept one without the
  other; propose, don't impose.
- **We don't own the repo** → this is a fork→PR, and per the owner rule
  ("never commit in a sub-repo without approval") the PR is filed only after
  owner sign-off.

---

## Sequencing & ownership
- WS1 and WS2 are independent and can run in parallel.
- **WS1** is fully within our repo → can proceed on owner's go, PR to
  `tzhouam/vllm-omni-copilot` per the standing deliver-as-PR rule.
- **WS2** touches an external repo → **requires explicit owner approval before
  the PR is opened**; the fork/branch/audit/reorg/merge can be prepared and
  reviewed locally first.

## Open decisions (need owner input)
1. WS2: one PR (reorg + merge) or two (reorg first, merge second)? Two is safer
   for the maintainer but slower.
2. WS1 transport default: stdio only, or also ship a streamable-HTTP mode for
   remote/team use?
3. WS2: contribute a documented "machine mirror" pointer to the copilot adapter
   format, or keep the contribution purely in their book form? (Their `layout.md`
   discourages a parallel machine tree, so default = book form only.)
