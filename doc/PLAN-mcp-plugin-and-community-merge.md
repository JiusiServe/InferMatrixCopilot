# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo adapter contribution

Status: PROPOSED, revision 3 (planning only — nothing here is executed yet).
Rev 3 folds in a second external review (GPT). Its WS2 factual claims were
verified against the community repo's own rules (`contributing/page-rules.md`,
`layout.md`, `validation.md`, `CONTRIBUTING.md`): index-linking of new pages is
**mandatory**, and DCO `git commit -s` is **mandatory**. The WS1 blockers were
confirmed against `cli/copilot.py` / `tracing.py`. Changes from rev 2 are listed
at the end.

Two independent workstreams. Every WS2 mutation (fork, commit, push, PR) needs
owner approval; WS1 is in-repo and proceeds on owner's go.

---

## Workstream 1 — expose the copilot as an MCP server (Claude Code + Codex), keep standalone CLI

### Goal
One MCP server exposing the copilot's governed **read-only** task kinds over
**stdio**, usable from **both** Claude Code and Codex, while the `omni-copilot`
CLI keeps working unchanged. The governed pipeline (scopes, plan-review,
`guard_push`) stays **inside** each run; the host calls the server as a
black-box and cannot widen its permissions.

### Non-goals (MVP)
- **No outward writes in v1.** No posting, no pushing. Debug runs `report_only`
  and that flag is not exposed. A host toggling `report_only=False` is not human
  approval; outward actions wait for a later, explicitly human-gated release.
- **stdio only** — no streamable-HTTP (HTTP ⇒ auth/tenancy/persistence/
  cancellation, out of scope for MVP).
- Not a Claude Code subagent (can't host an external agent), and **zero** change
  to existing CLI behavior — MCP is purely additive.

### Execution model — subprocess-per-run behind a single-worker queue
The design decision that resolves three of the review's blockers at once:
**each run executes as a child process, not an in-process thread.**

- **Why subprocess.** (a) *Stdout isolation* — the copilot prints plans,
  progress, metrics, and results to stdout; an MCP stdio server must keep stdout
  exclusively for JSON-RPC framing. A child process sends all of that to
  `<run_dir>/console.log`, never touching the server's protocol channel.
  (b) *Global-state isolation* — `tracing.init()` installs a **module-global**
  `_default` tracer (`tracing.py:168–177`) and `Copilot.last_run_dir` is shared
  mutable state; in separate processes both are per-run by construction, so the
  cross-contamination hazard is gone (not merely serialized around).
- **Worker mechanism (made concrete).** One dedicated worker thread draining a
  `queue.Queue`; it `Popen`s the run subprocess and `.wait()`s, so exactly one
  run executes at a time (serialized MVP — for cost/simplicity, no longer for
  correctness). No `asyncio.Lock` shared across event loops (which would be
  unsafe).

### Run lifecycle — reserve fast, plan+execute in the worker
`start_*` must return an id in milliseconds, but `run_task` today mints `run_id`
*after* plan-review (`copilot.py:150`) and planning can invoke an LLM or fail.
So planning moves **into** the worker:

1. **`reserve_run(spec) -> run_id`** (server thread, no LLM): validate inputs,
   allocate `run_id`, `mkdir` the run dir under `run_root`, write `request.json`
   (validated spec) + `run_status.json {state:"queued", pid:null}`, return the
   id. Returns in ms. This is what `start_*` calls.
2. **Worker** pops the id, launches the run subprocess pointed at the reserved
   dir (`--run-dir`, `assume_yes`, stdout/stderr → `console.log`).
3. **Subprocess** (new thin entry, e.g. `omni-copilot --execute-reserved
   <dir>`): reads `request.json`, then transitions
   `queued → planning → running → {done|blocked|failed}`, doing resolution +
   plan-review under `planning` and execution under `running`. The terminal
   write is atomic (tmp-file + `os.replace`) in a `finally`.

`run_status.json` is the single source of truth for polling; `RUN_REPORT.md` /
`ESCALATION.md` are attached when present but never used to *infer* liveness.

### Durability is reconciliation, not resurrection
Reading status files after a server restart preserves **observability**, not
execution. So:
- On startup the server scans `run_root`; any run in a non-terminal state
  (`queued`/`planning`/`running`) whose recorded `pid` is not alive is marked
  **`interrupted`** (terminal, with a note). No silent "stuck running".
- A `finally` guarantees a terminal state for controlled completion and Python
  exceptions — but **not** SIGKILL / host death; those are caught by the
  startup reconciliation above. Acceptance is worded to that guarantee, not an
  absolute one.

### MCP boundary validation (untrusted host input)
- `run_id`: strict pattern, and its resolved real path must be contained under
  `run_root` (reject traversal); unknown id → clean error, not a crash.
- `repo`: must be in a configured **allowlist**.
- `pr`/`issue`: positive integers; triage `limit`: bounded.
- `get_result`: report text **size-capped** with a pointer to the archived full
  report (offset/artifact reference), never an unbounded dump over the protocol.

### Tools exposed (v1, all read-only)
- `start_review(pr, repo)` · `start_issue_answer(issue, repo)` ·
  `start_issue_triage(repo, limit?)` · `start_debug(pr, repo)` (report-only)
- `get_result(run_id, offset?)` (reads `run_status.json`; attaches capped report)
- `get_status(run_id)` (reads `progress.json`) · `list_playbooks()`

### Phases & deliverables
1. **CLI surface** (`cli/copilot.py`): `reserve_run` + the `--execute-reserved
   <dir>` entry that plans-then-executes into a pre-created dir with atomic
   `run_status.json` transitions. `run_task` is refactored to compose these, so
   the CLI path and all 227 tests are unchanged.
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): `mcp` SDK (FastMCP)
   over stdio; the single-worker `queue.Queue` + subprocess launcher; the tools
   above. New `omni-copilot-mcp` console-script behind an **optional extra**
   (`pip install -e ".[mcp]"`) so standalone installs stay dependency-free.
3. **Claude Code plugin** (`plugin/`): `.claude-plugin/plugin.json`, `.mcp.json`
   starting the stdio server, thin convenience skills. **Explicit prerequisite:**
   installing a plugin does *not* install the Python package, so the `.mcp.json`
   command must resolve — document a one-time `uv tool install`/`pipx install`,
   or use `uvx --from git+https://…/vllm-omni-copilot omni-copilot-mcp`. The raw
   always-available path is `claude mcp add`; exact marketplace/`/plugin` syntax
   is **to verify against current Claude Code docs** before writing it down.
4. **Codex**: `docs/codex/config.toml` snippet for `[mcp_servers.omni_copilot]`
   + optional `AGENTS.md`. No plugin (MCP + AGENTS.md only).
5. **Tests** (offline, extend the suite):
   - `reserve_run` returns an id + `queued` status **without** any LLM call.
   - state machine: subprocess drives `queued→planning→running→done`; an injected
     failure lands `failed` (no hang); a fake stale `running` with a dead pid is
     reconciled to `interrupted` on startup.
   - stdout hygiene: a run's copilot output lands in `console.log`, and the
     server's stdout carries only protocol bytes.
   - boundary: bad `run_id` / off-allowlist `repo` / negative `pr` rejected; no
     post/push tool in the schema set; `get_result` caps report size.
   Plus one **live smoke**: `start_review` on a small merged PR → poll to `done`.
6. **Docs**: `doc/CODE_TOUR.md` §11 MCP entry; new `doc/MCP.md` (both hosts,
   package-install prerequisite, stdout contract).

### Acceptance
- `omni-copilot -p "review pr N"` unchanged (existing tests green).
- Server stdout carries protocol bytes only; all copilot output is in
  `console.log`.
- Every run reaches a **terminal** `run_status.json` on controlled completion or
  a Python exception; SIGKILL/host-death runs are reconciled to `interrupted`
  on next startup.
- `start_review` → poll → real (size-capped) `RUN_REPORT`; no post/push tool
  exists in v1.

---

## Workstream 2 — contribute the copilot's net-new knowledge to `zuiho-kai/claude-workflow-starter` (fork → PR)

### Goal (knowledge-only)
Contribute the copilot's **net-new** vllm-omni knowledge as new pages placed by
*their* `layout.md`, each with **public** provenance, linked from the nearest
`_index.md` as their rules require. No broad reorganization (their tree already
follows its own `layout.md`); a reorg is at most a separate, later, optional PR.

### Index linking is mandatory (verified)
Their rules require every new page to be reachable from the nearest `_index.md`:
- `page-rules.md`: "分类 `_index.md` 必须列出里面的每篇当前有效页面"; new subdir ⇒
  "在上一层 `_index.md` 增加入口".
- `CONTRIBUTING.md` checklist: "最近 `_index.md` 能找到新页面".
- `validation.md`: "更新当前目录 `_index.md`".
So rev-2's "add pages only, leave nav to the maintainer" option is **removed**.
The PR makes the **minimal mandatory** `_index.md` edits (additive link rows,
and a parent-index entry when a new subdir is created) — nothing more.

### Content-preservation, reconciled with mandatory index edits
- **Navigation allowlist**: the specific `_index.md` files that must gain a link
  for our new pages. Edits to these are limited to **additive link rows**
  (verifiable in the diff).
- **Zero-edit hash gate on everything else**: a pre/post SHA-256 manifest of all
  other pre-existing files; any hash change outside the navigation allowlist
  blocks the PR. This removes rev-2's contradiction (no more "every byte
  unchanged" while editing indexes).

### Dedup against provenance loops (hard gate) + public provenance
- Facts whose provenance is `community:zuiho-kai/…` were ingested *from this
  repo* and must NOT be contributed back; only **net-new** copilot knowledge
  (removed-API sweep, PR-time review discipline, run-level/dummy-weights trap,
  stage-capacity checks) is eligible.
- **Provenance must be public**: cite public vllm-omni **commit / PR / issue /
  source links**, not internal labels (our "eval GT #n" maps to a real public
  PR/issue — cite that). Upstream maintainers can independently verify a link;
  they cannot verify an internal id.
- The **dedup matrix + hash manifest go in the PR body** (or an external gist),
  **not** committed into their tree — a `MERGE-MATRIX.md` file would itself
  violate their page/index rules.

### Format: their book, not our machine tree
"Contribute" = translate net-new curated facts into their markdown pages placed
by `layout.md`. We do **not** drop `profile.yaml`/`manifest.yaml` as a parallel
machine tree (their convention forbids it; book-form only).

### Phases & deliverables
1. **Local prep (no mutations)**: clone into scratch; assemble the net-new page
   drafts, the dedup matrix, and the hash manifest as working files.
2. **Audit / dedup**: classify each adapter fact `already-in-theirs` /
   `sourced-from-theirs` (drop) vs `net-new` (keep); resolve each kept fact to a
   public provenance link.
3. **Author pages**: new pages placed by `layout.md`, public provenance, linking
   to (never duplicating) existing owner pages; respect `page-rules.md` /
   `validation.md`.
4. **Mandatory minimal nav**: additive link rows in the nearest `_index.md`
   (+ parent entry if a subdir is new). Everything else hash-verified unchanged.
5. **Hygiene**: run their linter/validation; **DCO sign-off mandatory**
   (`git commit -s`); PR body in **Chinese** with the matrix + hash manifest
   inline, stating: "本 PR 仅新增 vllm-omni-copilot 提炼的净新增知识(附公开溯源
   链接),仅对相关 `_index.md` 追加导航链接,未改动任何其他现有内容;已排除源自
   本仓库的事实以避免回灌;不含目录重构。"
6. **Open PR** → `zuiho-kai:master`.

### Acceptance
- Diff = new files + additive link rows in allowlisted `_index.md` only; hash
  manifest shows zero change to every other pre-existing file.
- New pages sit where `layout.md` prescribes, each reachable from the nearest
  `_index.md`, with public provenance, no duplication, no `sourced-from-theirs`
  re-contribution, no `MERGE-MATRIX.md` committed.
- DCO-signed; Chinese PR body; passes their contribution checks.

---

## Sequencing & ownership
- WS1 and WS2 are independent.
- **WS1** is in-repo → proceeds on owner's go; delivered as a PR to
  `tzhouam/vllm-omni-copilot`. Land in lifecycle order: reserve/execute split →
  status file + reconciliation → subprocess+queue → MCP server → packaging.
- **WS2** touches an external repo. **Every mutation needs explicit owner
  approval before it happens** — not just the PR. Fork (creates a repo under
  `tzhouam`), any commit (owner rule: never commit a sub-repo without approval),
  branch push, and PR are all gated. Only local-only prep (scratch clone,
  authoring uncommitted drafts, building the matrix/manifest) proceeds
  unattended.

## What changed from rev 2 (per the review)
1. Subprocess-per-run isolates stdout from the stdio protocol (blocker 1) and
   makes the module-global tracer / `last_run_dir` per-process (de-risks 3).
2. `start_*` reserves the run (id + `queued`, no LLM) and does planning **in the
   worker** (`queued→planning→running`), so it returns immediately (blocker 2).
3. Startup **reconciliation** marks dead non-terminal runs `interrupted`;
   durability is observability + reconciliation, not resurrection (blocker 3).
4. Acceptance guarantees terminal status for controlled/exception paths only;
   SIGKILL handled by reconciliation (blocker 4).
5. Added MCP **boundary validation**: run_id containment, repo allowlist,
   positive pr/issue, bounded triage, capped report output (blocker 5).
6. Worker = dedicated **single worker thread + `queue.Queue`**, no cross-loop
   `asyncio.Lock` (blocker 6).
7. WS2 `_index.md` linking is **mandatory** (verified) — removed the
   "leave-nav-to-maintainer" option (7).
8. WS2 hash gate uses a **navigation allowlist** for the index files, hash-checks
   all others — contradiction resolved (8).
9. `MERGE-MATRIX.md` goes in the **PR body**, not the tree (9).
10. **DCO mandatory** `git commit -s` (verified), not "if required" (10).
11. **Public provenance** links, not internal `eval GT #n` (11).
12. WS2 approval gate covers **fork/commit/push/PR**, not just PR-open (12).

## Open decisions
Both rev-2 open decisions are now resolved: (1) ship the serialized
single-worker-subprocess MVP, defer real concurrency; (2) minimal `_index.md`
updates are mandatory (their rules require it). The only remaining gate is owner
approval — go for WS1, and per-mutation approval for WS2.
