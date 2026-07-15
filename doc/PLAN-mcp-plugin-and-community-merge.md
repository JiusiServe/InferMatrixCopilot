# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo adapter contribution

Status: PROPOSED, revision 5 (planning only — nothing here is executed yet).
Rev 5 folds in a fourth external review (GPT). Its two blockers were real design
gaps — both consequences of rev 4 explicitly allowing **multiple server
processes** (Claude Code and Codex each launch their own server): an untrusted
`request.json`, and unsafe cross-server reconciliation. WS2 was declared ready
and is unchanged. The Claude Code plugin/marketplace syntax (rev-4's open item)
is now **verified** and written in. Changes from rev 4 are listed at the end.

Two independent workstreams. Every WS2 mutation (fork, commit, push, PR) needs
owner approval; WS1 is in-repo and proceeds on owner's go.

---

## Workstream 1 — expose the copilot as an MCP server (Claude Code + Codex), keep standalone CLI

### Goal
One MCP server exposing the copilot's **genuinely read-only** task kinds over
**stdio**, usable from **both** Claude Code and Codex, while the `omni-copilot`
CLI keeps working unchanged and **in-process**. The safety guarantee — *the host
cannot widen the server's permissions* — is enforced **structurally in the
child**, not by tool schemas or file trust.

### V1 tool set — verified read-only only
- `start_review(pr, repo)` · `start_issue_answer(issue, repo)` (never
  auto-posts) · `start_issue_triage(repo)` (no `limit` knob — unplumbed;
  `issue.fetch` reads step params) · `get_result(run_id, offset?)` ·
  `get_status(run_id)` · `list_playbooks()`.
- **No `start_debug` in V1** — report-only `pr-debug` mutates (verified:
  `pr.checkout_branch` add-remote/fetch/`checkout -B`, ungated). Follow-up: a
  read-only `pr-debug-report` playbook (no `checkout`; CI groups rendered into
  the report).

### Non-goals (MVP)
No outward writes (no posting/pushing; no `report_only=False` surface); **stdio
only**; not a Claude Code subagent; **zero** change to existing CLI behavior.

### Two independent safety enforcers (defense in depth)
Rev 4 leaned on the MCP tool schema. That is not sufficient, because the run is
launched later from an on-disk `request.json` a same-user host process could
rewrite. So policy is enforced **twice**, and the child's check is authoritative:

1. **Boundary (server, at `reserve_run`)**: validate the tool call and write a
   restrictive-permission (`0600`) `request.json`.
2. **Child (authoritative, at execution)**: an `enforce_mcp_policy(spec)` gate
   runs after reading `request.json` and before anything else, **re-deriving**
   the safe task regardless of file contents:
   - kind ∈ {`pr_review`, `issue_assist`, `issue_filter`} only — any other kind
     (esp. write-capable: rebase/debug/push) → **refuse**;
   - force `post=False` (and `report_only` where the kind takes it);
   - reject unknown/extra params; strip anything not in the kind's schema;
   - revalidate `repo` against `mcp_repo_allowlist` and any target values.
   The same function guards the boundary, so tampering between reserve and
   execute cannot widen permissions — the guarantee is structural.

### Execution model — CLI in-process, MCP launches a subprocess
- **CLI unchanged & in-process.** The CLI's `run_task` keeps its **existing
  order**: resolve → print plan → gate/confirm → **then** `mkdir` → in-process
  `_execute`. A rejected plan or aborted confirm leaves **no** run directory
  (unchanged behavior — asserted by a test). `reserve_run` and the reserved-exec
  child are **new and MCP-only**; the CLI never spawns a subprocess.
- **MCP launches a subprocess per run** via `sys.executable -m
  omni_copilot.<reserved-exec-entry> --run-id <id>` (current interpreter/module,
  never a PATH `omni-copilot`). This keeps the copilot's stdout — plans/progress/
  metrics — in `<run_dir>/console.log`, leaving the server's stdout for JSON-RPC
  only; and makes the module-global `tracing._default` / `Copilot.last_run_dir`
  per-process. For the MCP path the dir exists **before** planning by design; a
  plan-review `blocked` or a failure is recorded as a **terminal** status (the
  poll record), intentionally persisted — not litter.
- **Worker**: one dedicated worker thread draining a `queue.Queue`; `Popen` +
  `.wait()`, one run at a time. No cross-loop `asyncio.Lock`.

### Run lifecycle — ownership-stamped, reconciled by confirmed death
Each server instance has a unique `server_id` (uuid, one per process start) and
registers a liveness token `run_root/servers/<server_id>` carrying its pid.

1. **`reserve_run(spec) -> run_id`** (server thread, no LLM): `enforce_mcp_policy`,
   allocate `run_id`, `mkdir` under `run_root`, write `request.json` (0600) +
   `run_status.json {state:"queued", owner_server_id, owner_server_pid,
   child_pid:null}`; return id in ms.
2. **Parent records `child_pid` immediately after `Popen`** (before the child's
   first status write) — else a server death in that window makes a live child
   look orphaned.
3. **Child** (`--run-id`, id-validated, dir derived+contained under `run_root`
   in-child — never a raw `--run-dir`): `enforce_mcp_policy`, then
   `queued → planning → running → {done|blocked|failed}`; atomic terminal write
   (tmp + `os.replace`) in a `finally`.
4. **Parent reconciles on exit.** After `.wait()`, if the run it owns is still
   non-terminal (child died before its `finally`), atomically mark it
   `interrupted`/`failed` immediately.
5. **Ownership-aware startup reconciliation** (multi-server safe). A starting
   server reconciles a run **only when its owner is confirmed dead**:
   `owner_server_id`'s liveness token is gone / its pid is not alive. A `queued`
   run (`child_pid:null`) owned by a **live** other server is left untouched
   (fixes the rev-4 bug where a second server would mark it `interrupted`). A
   `running` run is reconciled only if owner-server **and** `child_pid` are both
   dead. A live server never touches another live server's runs.

Durability = observability + ownership-aware reconciliation, not resurrection.
`finally` covers controlled completion + Python exceptions; child SIGKILL →
parent-on-exit; server death → another server reconciles only what the dead
owner held.

### MCP boundary validation
- `run_id`: strict pattern; resolved real path contained under `run_root`.
- `repo`: **`mcp_repo_allowlist` defaults to `[default_repo]`** (not every
  installed adapter); extra repos require explicit config; off-list → refused.
- `pr`/`issue`: positive integers.
- **`get_result` pagination contract**: returns ≤ `mcp_report_max_bytes`
  (default 64 KiB) of report text + `next_offset` (int|null) + `report_path`
  (archived full report); never an unbounded dump.
- **`get_status`** returns `run_status.json` (state/owner/pids/timestamps) +
  `progress.json` **when present** (queued/planning have none).

### Phases & deliverables
1. **CLI surface** (`cli/copilot.py`): `enforce_mcp_policy`, `reserve_run`, the
   reserved-exec module entry (id-validated, dir contained in-child, ownership
   stamps, planning-in-child). CLI `run_task` **unchanged**. All 227 tests hold.
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): `mcp` SDK (FastMCP)
   over stdio; `server_id` + liveness token; single-worker `queue.Queue`;
   `sys.executable -m` launcher; `child_pid`-on-Popen; parent-on-exit +
   ownership-aware startup reconciliation; V1 tools; allowlist/pagination
   settings. `omni-copilot-mcp` console-script behind an optional `[mcp]` extra.
3. **Claude Code plugin** (`plugin/`) — **verified layout**:
   - `.claude-plugin/plugin.json`: `{name, version, description, author?}`.
   - Plugin-root `.mcp.json`:
     `{"mcpServers":{"omni-copilot":{"type":"stdio","command":"…","args":[…],
     "env":{…}}}}`; `${CLAUDE_PLUGIN_ROOT}` / `${VAR:-default}` substitution is
     available.
   - **Package prerequisite (verified boundary):** installing the plugin does
     **not** pip/uv-install the Python package — the `.mcp.json` `command` must
     already resolve. So **prefer a preinstalled, pinned package**: document
     `uv tool install`/`pipx install 'omni-copilot==<pinned>'`, and set
     `command` to the installed `omni-copilot-mcp` (or a plugin `bin/` shim that
     execs it). A floating `uvx --from git+…@<ref>` is an explicit opt-in
     fallback only — it adds network latency + supply-chain drift + MCP
     startup-timeout risk. (One residual: whether any plugin hook can run an
     install step — treat as no; verify at implementation.)
   - Install: `claude plugin marketplace add github.com/tzhouam/<repo>` then
     `claude plugin install <name>@<marketplace>`, or direct
     `claude plugin install github.com/tzhouam/<repo>` (a root `marketplace.yaml`
     lists the plugin: name/version/description + `source:{type:github, repo,
     path?, ref?}`). The raw, host-agnostic path remains `claude mcp add`.
4. **Codex**: `docs/codex/config.toml` `[mcp_servers.omni_copilot]`
   (`command`/`args`/`env`, per Codex docs) + optional `AGENTS.md`. No plugin.
5. **Tests** (offline): `reserve_run` → id + `queued`, no LLM; `enforce_mcp_policy`
   refuses a tampered `request.json` (kind→rebase, `post=True`, off-list repo);
   `queued→planning→running→done`; child crash → parent-on-exit `failed`;
   **two servers**: server B's startup does **not** touch server A's live
   `queued` run, but **does** reconcile a run whose owner token is gone; CLI abort
   leaves **no** run dir; stdout hygiene; boundary (bad id/off-list repo/negative
   pr; capped report + `next_offset`); no post/push/debug tool in V1 schema. Plus
   a **live smoke**: `start_review` on a small merged PR → poll `done`.
6. **Docs**: `CODE_TOUR.md` §11 MCP entry; new `doc/MCP.md`.

### Acceptance
- CLI unchanged and in-process; aborted plans leave no run dir.
- The child enforces policy independently: a rewritten `request.json` cannot run
  a non-V1 kind, post, push, or an off-list repo.
- Multi-server safe: no server reconciles a run whose owner is alive.
- Every run reaches a terminal `run_status.json` (completion / exception /
  child-death via parent; server-death via owner-aware startup).
- `get_result` size-capped with `next_offset` + `report_path`; server stdout is
  protocol-only.

---

## Workstream 2 — contribute the copilot's net-new knowledge to `zuiho-kai/claude-workflow-starter` (fork → PR)

*Declared ready by the review; unchanged from rev 4. Summary:*

- **Knowledge-only PR** — net-new pages placed by *their* `layout.md`; no reorg.
- **Index linking mandatory** (verified: `page-rules.md` / `CONTRIBUTING.md` /
  `validation.md`): minimal additive link rows in the nearest `_index.md`
  (+ parent entry for a new subdir).
- **Content preserved**: a **navigation allowlist** exempts only those `_index.md`
  files (additive rows); a pre/post SHA-256 manifest hash-gates everything else.
- **Dedup + public provenance** (hard gates): never re-contribute
  `community:zuiho-kai/…`-sourced facts; cite **public** vllm-omni commit/PR/
  issue/source links (not internal `eval GT #n`).
- **Book form only** — no parallel machine tree.
- **Hygiene**: DCO `git commit -s` **mandatory** (verified); Chinese PR body; the
  PR body carries the hash **verify command + summary + compact allowlisted-index
  list** (full manifest + dedup matrix are local artifacts, **not** committed —
  a `MERGE-MATRIX.md` file would break their page/index rules).
- Phases: local prep (no mutations) → audit/dedup → author pages → minimal nav →
  hygiene → open PR → `zuiho-kai:master`.

---

## Sequencing & ownership
- WS1 and WS2 are independent.
- **WS1** is in-repo → proceeds on owner's go; PR to `tzhouam/vllm-omni-copilot`.
  Land in order: `enforce_mcp_policy` + `reserve_run` + reserved-exec child →
  ownership stamps + parent-on-exit + owner-aware startup reconciliation → MCP
  subprocess/queue → boundary/pagination → packaging. (Read-only
  `pr-debug-report` + `start_debug` is a fast-follow.)
- **WS2** external repo → **every mutation (fork/commit/push/PR) needs explicit
  owner approval before it happens**. Only local uncommitted prep runs unattended.

## What changed from rev 4 (per the review)
1. **Child-side policy enforcement** (`enforce_mcp_policy`) makes the "host cannot
   widen permissions" guarantee structural, immune to a tampered `request.json`
   (0600) — not reliant on tool schemas (blocker 1).
2. **Ownership-aware reconciliation**: persist `owner_server_id` /
   `owner_server_pid` / `child_pid`; reconcile only when the owner is confirmed
   dead — a second server no longer stomps another's live `queued` run
   (blocker 2).
3. **CLI `run_task` left unchanged** (gate-before-`mkdir`); reserve/child are
   MCP-only; a test asserts aborts leave no dir (IR1).
4. **`child_pid` recorded immediately after `Popen`** (IR2).
5. **`mcp_repo_allowlist` defaults to `[default_repo]`** (IR3).
6. **Prefer a preinstalled pinned package**; `uvx --from git+…` only as an opt-in
   fallback (IR4).
7. **Claude plugin/marketplace syntax verified** and written in — real form is
   `claude plugin install github.com/owner/repo`, `.claude-plugin/plugin.json`,
   plugin-root `.mcp.json` with `${CLAUDE_PLUGIN_ROOT}`, root `marketplace.yaml`;
   plugin install does not install the Python package (IR5).

## Open decisions
None blocking. One residual to confirm at implementation: whether any plugin
install hook can run a package install (assumed no). The remaining gate is owner
approval — go for WS1, per-mutation approval for WS2.
