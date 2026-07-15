# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo adapter contribution

Status: PROPOSED, revision 4 (planning only — nothing here is executed yet).
Rev 4 folds in a third external review (GPT). Its two code-level claims were
verified against the source and are **real**:
- The report-only `pr-debug` playbook is **not** read-only: `pr.checkout_branch`
  (`rebase.py:28`, mislabeled `"read"`) adds a fork remote, `git fetch`es, and
  `git checkout -B`s, and the `pr-debug.yaml` `checkout` step has no
  `when: not report_only` guard.
- `start_issue_triage(limit)` would be **ignored**: `issue.fetch` reads
  `ctx.params` (step params, `issue.py:40`), and `issue-triage.yaml` passes none,
  so a `TaskSpec`-level `limit` never reaches it.

Changes from rev 3 are listed at the end.

Two independent workstreams. Every WS2 mutation (fork, commit, push, PR) needs
owner approval; WS1 is in-repo and proceeds on owner's go.

---

## Workstream 1 — expose the copilot as an MCP server (Claude Code + Codex), keep standalone CLI

### Goal
One MCP server exposing the copilot's **genuinely read-only** task kinds over
**stdio**, usable from **both** Claude Code and Codex, while the `omni-copilot`
CLI keeps working unchanged and **in-process**. The governed pipeline (scopes,
plan-review, `guard_push`) stays inside each run; the host calls the server as a
black-box and cannot widen its permissions.

### V1 tool set — verified read-only only
- `start_review(pr, repo)` — pr-review playbook (read-only).
- `start_issue_answer(issue, repo)` — issue-assist (read-only; never auto-posts).
- `start_issue_triage(repo)` — issue-triage (read-only). **No `limit` param in
  V1**: it isn't plumbed (`issue.fetch` reads step params, not `TaskSpec.params`),
  so exposing it would be a dead knob. Uses the playbook default (20). Exposing
  `limit` later needs a one-line plumb (fall back to `spec.params["limit"]` in
  `issue.fetch`, or pass it into the step's params).
- **`start_debug` is NOT in V1.** The report-only `pr-debug` playbook mutates the
  working tree (remote add + fetch + `checkout -B`) before it groups CI failures,
  so it is not read-only, and in report-only mode the failure groups land in
  DIAGNOSTICS rather than the (thin) RUN_REPORT. Re-adding debug is a **defined
  follow-up**: a dedicated `pr-debug-report` playbook that skips `checkout`
  entirely (its `fetch_ci_failures`/`group_failures` read CI by PR number, not the
  worktree) and renders the groups **into** the report. Only then does
  `start_debug` return as read-only.
- `get_result(run_id, offset?)` · `get_status(run_id)` · `list_playbooks()`.

### Non-goals (MVP)
- **No outward writes in v1** (no posting/pushing; no `report_only=False` surface
  — a host toggling a flag is not human approval).
- **stdio only** (no HTTP: auth/tenancy/persistence/cancellation out of scope).
- Not a Claude Code subagent; **zero** change to existing CLI behavior.

### Execution model — CLI in-process, MCP launches a subprocess
- **CLI unchanged & in-process.** `run_task` composes `reserve_run` + an
  **in-process** execute (today's behavior). The CLI never spawns a subprocess,
  so "CLI unchanged" stays literally true and all 227 tests hold.
- **MCP launches a subprocess per run.** Only the server path runs each execution
  as a child process, which (a) keeps the copilot's stdout — plans/progress/
  metrics/results — in `<run_dir>/console.log`, leaving the server's stdout
  exclusively for JSON-RPC framing; (b) makes the module-global `tracing._default`
  and `Copilot.last_run_dir` per-process, removing the cross-contamination
  hazard by construction.
- **Launch mechanism.** `sys.executable -m omni_copilot.<reserved-exec-entry>
  --run-id <id>` — the current interpreter/module, never a PATH `omni-copilot`
  that could be a different install.
- **Worker.** One dedicated worker thread draining a `queue.Queue`; it `Popen`s
  the child and `.wait()`s, so exactly one run executes at a time (serialized —
  for cost/simplicity, not correctness). No cross-loop `asyncio.Lock`.
- **Serialization scope caveat.** The queue serializes only *within one server
  process*. Claude Code and Codex each launch their own server → two queues →
  concurrent runs. That is correctness-safe (subprocess isolation), only a
  cost/resource concern; machine-wide serialization would need a filesystem lock
  (`run_root/.worker.lock`). Deferred unless cost demands it.

### Run lifecycle — reserve fast, plan+execute in the child, reconcile on exit
1. **`reserve_run(spec) -> run_id`** (server thread, no LLM): validate inputs,
   allocate `run_id`, `mkdir` its dir under `run_root`, write `request.json` +
   `run_status.json {state:"queued", pid:null}`; return the id in ms.
2. **Child** (`--run-id <id>`): **validate the id and derive+contain** the run
   dir under `run_root` *inside the child* (never accept a raw `--run-dir` — that
   is a second path-traversal boundary). Read `request.json`, then transition
   `queued → planning → running → {done|blocked|failed}`; resolution + plan-review
   under `planning`, execution under `running`; the terminal write is atomic
   (tmp + `os.replace`) in a `finally`.
3. **Parent reconciles on exit.** After `.wait()`, the worker reads
   `run_status.json`; if the child died before its `finally` left a terminal
   state (SIGKILL/crash → still `planning`/`running`), the parent **atomically
   marks it `interrupted`/`failed` immediately** — not only on the next restart.
4. **Startup reconciliation** remains the backstop for runs orphaned by a
   *server* death: scan `run_root`, mark non-terminal runs with a dead `pid` as
   `interrupted`.

Durability = observability + reconciliation, not resurrection. A `finally`
covers controlled completion and Python exceptions; SIGKILL/host death is caught
by parent-on-exit (child died, parent alive) or startup (both died).

### MCP boundary validation (untrusted host input)
- `run_id`: strict pattern; resolved real path must be contained under `run_root`
  (reject traversal); unknown id → clean error.
- `repo`: must be in a configured **allowlist** — a new explicit setting
  `mcp_repo_allowlist` (defaults to the adapters present); off-list → refused.
- `pr`/`issue`: positive integers.
- **Report pagination contract (explicit):** `get_result` returns at most
  `mcp_report_max_bytes` (default e.g. 64 KiB) of report text, plus
  `next_offset` (int|null) and `report_path` (the archived full report) so the
  host can page or fetch the artifact; never an unbounded dump.
- `get_status` returns **`run_status.json`** (state/pid/timestamps) plus
  `progress.json` **when present** — queued/planning runs have no progress file.

### Phases & deliverables
1. **CLI surface** (`cli/copilot.py`): `reserve_run` + a reserved-exec module
   entry (`--run-id`, id-validated, dir contained in-child) that plans-then-
   executes with atomic `run_status.json` transitions; `run_task` composes
   `reserve_run` + in-process execute. CLI path and all 227 tests unchanged.
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): `mcp` SDK (FastMCP)
   over stdio; single-worker `queue.Queue` + `sys.executable -m` subprocess
   launcher + parent-on-exit reconciliation; the V1 tools above; the allowlist +
   pagination settings. New `omni-copilot-mcp` console-script behind an optional
   `[mcp]` extra so standalone installs stay dependency-free.
3. **Claude Code plugin** (`plugin/`): `.claude-plugin/plugin.json`, `.mcp.json`,
   thin skills. **Prerequisite explicit:** a plugin does not install the package —
   document `uv tool install`/`pipx install`, or `uvx --from git+…
   omni-copilot-mcp`; raw path is `claude mcp add`; marketplace/`/plugin` syntax
   to verify against current docs.
4. **Codex**: `docs/codex/config.toml` `[mcp_servers.omni_copilot]` + optional
   `AGENTS.md`. No plugin.
5. **Tests** (offline): `reserve_run` returns id + `queued` with **no LLM**;
   `queued→planning→running→done`; injected child crash → parent-on-exit marks
   `failed` (no hang); dead-pid stale run → startup marks `interrupted`; stdout
   hygiene (copilot output in `console.log`, protocol-only on server stdout);
   boundary (bad id / off-allowlist repo / negative pr rejected; report size
   capped with `next_offset`); no post/push/debug tool in the V1 schema set. Plus
   one **live smoke**: `start_review` on a small merged PR → poll to `done`.
6. **Docs**: `CODE_TOUR.md` §11 MCP entry; new `doc/MCP.md`.

### Acceptance
- `omni-copilot -p "review pr N"` unchanged, runs **in-process** (tests green).
- Server stdout is protocol-only; copilot output is in `console.log`.
- Every V1 tool is read-only; **no `start_debug` in V1**; triage exposes no dead
  `limit` knob.
- Every run reaches a terminal `run_status.json` on controlled completion,
  Python exception, or child death (parent-on-exit); server-death orphans
  reconciled to `interrupted` on startup.
- `get_result` is size-capped with `next_offset` + `report_path`.

---

## Workstream 2 — contribute the copilot's net-new knowledge to `zuiho-kai/claude-workflow-starter` (fork → PR)

### Goal (knowledge-only)
Contribute the copilot's **net-new** vllm-omni knowledge as new pages placed by
*their* `layout.md`, each with **public** provenance, linked from the nearest
`_index.md` as their rules require. No broad reorganization; a reorg is at most a
separate, later, optional PR.

### Index linking is mandatory (verified in their repo)
- `page-rules.md`: "分类 `_index.md` 必须列出里面的每篇当前有效页面"; new subdir ⇒
  "在上一层 `_index.md` 增加入口".
- `CONTRIBUTING.md` checklist: "最近 `_index.md` 能找到新页面".
- `validation.md`: "更新当前目录 `_index.md`".
So the PR makes the **minimal mandatory** `_index.md` edits (additive link rows,
+ a parent entry when a new subdir is created) — nothing more.

### Content-preservation, reconciled with mandatory index edits
- **Navigation allowlist**: the specific `_index.md` files that must gain a link.
  Edits limited to **additive link rows**.
- **Zero-edit hash gate on everything else**: a pre/post SHA-256 manifest of all
  other pre-existing files; any change outside the allowlist blocks the PR.

### Dedup + public provenance (hard gates)
- Facts with provenance `community:zuiho-kai/…` were ingested *from this repo* —
  never contributed back; only **net-new** copilot knowledge is eligible.
- Provenance must be **public**: cite public vllm-omni **commit / PR / issue /
  source links** (our internal "eval GT #n" maps to a real public PR/issue — cite
  that), so a maintainer can independently verify.

### Format: their book, not our machine tree
Translate net-new curated facts into their markdown pages placed by `layout.md`;
do **not** drop `profile.yaml`/`manifest.yaml` as a parallel machine tree
(book-form only).

### Phases & deliverables
1. **Local prep (no mutations)**: clone into scratch; assemble net-new page
   drafts, the dedup matrix, and the hash manifest as working files.
2. **Audit / dedup**: classify each adapter fact; keep only `net-new`; resolve a
   public provenance link for each.
3. **Author pages** by `layout.md`, public provenance, linking to (never
   duplicating) existing owner pages.
4. **Mandatory minimal nav**: additive link rows in the nearest `_index.md`
   (+ parent entry if a subdir is new); everything else hash-verified unchanged.
5. **Hygiene**: run their linter/validation; **DCO sign-off mandatory**
   (`git commit -s`, confirmed required by their `CONTRIBUTING.md`); PR body in
   **Chinese**. **Do not commit `MERGE-MATRIX.md`** into their tree (a review
   artifact would itself break their page/index rules). The PR body carries the
   **verification command + result summary + a compact list of the allowlisted
   `_index.md` link additions**; the full hash manifest + dedup matrix are kept as
   local review artifacts (or an external gist), not pasted wholesale.
   PR body line: "本 PR 仅新增 vllm-omni-copilot 提炼的净新增知识(附公开溯源链
   接),仅对相关 `_index.md` 追加导航链接,未改动任何其他现有内容;已排除源自本
   仓库的事实以避免回灌;不含目录重构。"
6. **Open PR** → `zuiho-kai:master`.

### Acceptance
- Diff = new files + additive link rows in allowlisted `_index.md` only; the hash
  check (command + summary in the PR body) shows zero change elsewhere.
- New pages sit where `layout.md` prescribes, each reachable from the nearest
  `_index.md`, with public provenance, no duplication, no `sourced-from-theirs`
  re-contribution, no `MERGE-MATRIX.md` committed.
- DCO-signed; Chinese PR body; passes their contribution checks.

---

## Sequencing & ownership
- WS1 and WS2 are independent.
- **WS1** is in-repo → proceeds on owner's go; delivered as a PR to
  `tzhouam/vllm-omni-copilot`. Land in order: reserve/in-process-execute split →
  status file + parent-on-exit + startup reconciliation → MCP subprocess+queue →
  boundary/pagination → packaging. (The read-only `pr-debug-report` playbook +
  `start_debug` is a fast-follow after V1 ships read-only.)
- **WS2** touches an external repo. **Every mutation needs explicit owner
  approval before it happens** — fork (creates a repo under `tzhouam`), any commit
  (owner rule: never commit a sub-repo without approval), branch push, and PR.
  Only local-only prep (scratch clone, uncommitted drafts, matrix/manifest)
  proceeds unattended.

## What changed from rev 3 (per the review)
1. **`start_debug` dropped from V1** — the report-only `pr-debug` playbook
   mutates (verified: `checkout_branch` add-remote/fetch/`checkout -B`, ungated by
   `report_only`). A read-only `pr-debug-report` playbook (no `checkout`, groups
   rendered into the report) is the defined follow-up (B1).
2. **Parent-on-exit reconciliation** — after `.wait()`, mark any still-non-
   terminal run `interrupted`/`failed` immediately, not only on restart (B2).
3. **Child takes a validated `--run-id`**, derives+contains its dir under
   `run_root` internally — no raw `--run-dir` traversal boundary (B3).
4. **CLI stays in-process**; only MCP launches the subprocess, so "CLI unchanged"
   is literal (IC1).
5. **`get_status` returns `run_status.json` + optional `progress.json`** (queued/
   planning have no progress file) (IC2).
6. **Triage `limit` removed from V1** — it isn't plumbed (verified: `issue.fetch`
   reads step params); noted the one-line plumb to expose it later (IC3).
7. **Child launched via `sys.executable -m`**, not a PATH executable (IC4).
8. **Explicit `mcp_repo_allowlist` setting + pagination contract**
   (`max_bytes`/`next_offset`/`report_path`) (IC5).
9. **Serialization-scope caveat**: the queue serializes one server process only;
   two hosts = two servers; filesystem lock for machine-wide (IC6).
10. **WS2**: PR body carries the hash **verification command + summary + compact
    allowlisted-index list**, not the full manifest; full manifest stays a local
    artifact.

## Open decisions
None blocking. Rev-2/3 decisions are resolved (serialized single-worker-subprocess
MVP; mandatory minimal `_index.md` updates). One product choice for later, not V1:
whether the fast-follow re-adds `start_debug` via the read-only `pr-debug-report`
playbook, or debug stays CLI-only. The only remaining gate is owner approval — go
for WS1, per-mutation approval for WS2.
