# Plan — (1) Copilot as an MCP plugin for Claude Code + Codex, and (2) community-repo adapter contribution

Status: PROPOSED, revision 6 (planning only — nothing here is executed yet).
Rev 6 folds in a fifth external review (GPT). All three blockers were real; two
were verified against the source / official docs:
- The V1 kind is **`issue_answer`**, not `issue_assist` (that's the playbook
  name) — `task_spec.py:18` already defines the exact V1 set as
  `READ_ONLY_KINDS = {pr_review, issue_answer, issue_filter}`.
- The Claude Code marketplace flow is **`.claude-plugin/marketplace.json` +
  `/plugin marketplace add` + `/plugin install <plugin>@<marketplace>`** (a
  marketplace is always required; rev-5's root `marketplace.yaml` / bare-GitHub
  install were wrong — re-fetched from `discover-plugins.md`).
Changes from rev 5 are listed at the end. WS2 is unchanged (ready).

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

### V1 tool set — the three `READ_ONLY_KINDS`
- `start_review(pr, repo)` → kind `pr_review`
- `start_issue_answer(issue, repo)` → kind `issue_answer` (never auto-posts)
- `start_issue_triage(repo)` → kind `issue_filter` (no `limit` knob — unplumbed)
- `get_result(run_id, offset?)` · `get_status(run_id)` · `list_playbooks()`
The kinds match `READ_ONLY_KINDS` in `task_spec.py` verbatim; the policy gate
references that frozenset, not a hardcoded list, so it can't drift from the code.
**No `start_debug` in V1** (report-only `pr-debug` mutates via
`pr.checkout_branch`); read-only `pr-debug-report` playbook is the follow-up.

### Non-goals (MVP)
No outward writes; **stdio only**; not a subagent; **zero** change to CLI.

### Two independent safety enforcers (defense in depth)
The run is launched later from an on-disk `request.json` a same-user host process
could rewrite, so policy is enforced **twice**, child-authoritative:
1. **Boundary (server, `reserve_run`)**: validate the call; write `request.json`
   with `0600` perms.
2. **Child (authoritative, at execution)**: `enforce_mcp_policy(spec)` runs after
   reading `request.json`, re-deriving the safe task **regardless of file
   contents**:
   - `kind ∈ READ_ONLY_KINDS` (`{pr_review, issue_answer, issue_filter}`) — any
     other kind (rebase/debug/push/profile) → **refuse**;
   - force `post=False`;
   - reject unknown/extra params; strip anything outside the kind's schema;
   - revalidate `repo` against `mcp_repo_allowlist`.
   The same gate guards the boundary, so tampering between reserve and execute
   cannot widen permissions — the guarantee is structural.

### Execution model — CLI in-process, MCP launches a subprocess
- **CLI unchanged & in-process**: `run_task` keeps its existing order (resolve →
  plan → gate/confirm → **then** `mkdir` → in-process `_execute`); aborts leave
  **no** run dir (asserted by a test). `reserve_run`/reserved-exec child are new
  and **MCP-only**.
- **MCP launches a subprocess** via `sys.executable -m
  omni_copilot.<reserved-exec-entry> --run-id <id>` — keeps copilot stdout in
  `<run_dir>/console.log` (server stdout = JSON-RPC only) and makes
  `tracing._default` / `last_run_dir` per-process. Dir exists **before** planning
  by design; a plan-review `blocked` / failure is a **terminal** poll record, not
  litter.
- **Worker**: one dedicated worker thread + `queue.Queue`; `Popen` + `.wait()`,
  one run at a time; no cross-loop `asyncio.Lock`.

### Run-status: single-writer protocol + ownership
`run_status.json` fields: `state`, `owner_server_id`, `owner_server_pid`,
`child_pid`, timestamps. Each server has a uuid `server_id` (per process start)
and a liveness token `run_root/servers/<server_id>` carrying its pid.

- **Single writer at all times** (fixes the parent/child write race):
  - `reserve_run` (server) writes the initial `queued` record — before the child
    exists, so no contention.
  - Once launched, the **child is the sole writer**: it writes its **own** pid
    (`os.getpid()`) as its first action, then drives
    `queued → planning → running → {done|blocked|failed}`; the parent does **not**
    write during the run (it holds `Popen.pid` in memory for its own use).
  - **Reconcilers** (parent-on-exit, or a lazy/sweeper check from any server)
    write a terminal state **only after confirming the writer is dead**, under an
    advisory `flock` on the status file, and **preserve the ownership fields** on
    every transition.
  So exactly one process ever writes at a given time; atomic `os.replace` + the
  flock make it safe.

### Reconciliation — lazy + on-exit + startup (no indefinite non-terminal)
Startup-only reconciliation misses a run orphaned *after* the last server
started (owner server died, then the child was SIGKILLed, and nothing restarts).
So reconcile at three points, all **ownership-aware** (act only when the run's
owner-server, and for a `running` run its `child_pid`, are **confirmed dead**):
1. **Parent-on-exit**: after `.wait()`, if the owned run is still non-terminal,
   mark it `interrupted`/`failed` immediately (child is dead — no concurrent
   writer).
2. **Lazy at read**: every `get_status`/`get_result` reconciles the run it reads
   if its owner/child are dead — so a post-startup orphan resolves on the next
   poll.
3. **Startup + optional periodic sweeper**: backstop for runs never polled again.
A `queued` run (`child_pid:null`) owned by a **live** other server is never
touched (the rev-4/5 multi-server bug).

### MCP boundary validation
- `run_id`: strict pattern; resolved real path contained under `run_root`.
- `repo`: **`mcp_repo_allowlist` defaults to `[default_repo]`**; extra repos need
  explicit config; off-list → refused.
- `pr`/`issue`: positive integers.
- **`get_result`**: ≤ `mcp_report_max_bytes` (default 64 KiB) + `next_offset`
  (int|null) + `report_path`; never an unbounded dump.
- **`get_status`**: `run_status.json` + `progress.json` when present (queued/
  planning have none).

### Phases & deliverables
1. **CLI surface** (`cli/copilot.py`): `enforce_mcp_policy` (over
   `READ_ONLY_KINDS`), `reserve_run`, reserved-exec module entry (id-validated,
   dir contained in-child, child writes own pid, single-writer transitions).
   CLI `run_task` **unchanged**; all 227 tests hold.
2. **MCP server** (`src/omni_copilot/mcp_server.py`, new): `mcp` SDK (FastMCP)
   over stdio; `server_id` + liveness token; single-worker `queue.Queue`;
   `sys.executable -m` launcher; parent-on-exit + lazy-at-read + startup/periodic
   ownership-aware reconciliation under `flock`; V1 tools; allowlist/pagination
   settings. `omni-copilot-mcp` console-script behind an optional `[mcp]` extra.
3. **Claude Code plugin** — **verified layout & flow** (`discover-plugins.md`,
   `plugins.md`):
   - Plugin: `.claude-plugin/plugin.json` `{name, version, description, author?}`;
     plugin-root `.mcp.json`
     `{"mcpServers":{"omni-copilot":{"type":"stdio","command":"…","args":[…],
     "env":{…}}}}` with `${CLAUDE_PLUGIN_ROOT}` / `${VAR:-default}` substitution.
   - Marketplace: a repo-level **`.claude-plugin/marketplace.json`** naming the
     marketplace and listing the `omni-copilot` plugin + its `source`.
   - Install flow (a marketplace is **always** required — no bare-GitHub install):
     `/plugin marketplace add tzhouam/<repo>` then
     `/plugin install omni-copilot@<marketplace>` (or the non-interactive CLI
     `claude plugin install omni-copilot@<marketplace> [--scope …]`).
   - **Package prerequisite (verified):** installing the plugin does **not**
     pip/uv-install the Python package — the `.mcp.json` `command` must already
     resolve. **Prefer a preinstalled, pinned package** (`uv tool
     install`/`pipx install 'omni-copilot==<pinned>'`, command =
     `omni-copilot-mcp` or a plugin `bin/` shim). A floating `uvx --from
     git+…@<ref>` is an explicit opt-in fallback only (network latency +
     supply-chain drift + startup-timeout risk).
   - Host-agnostic escape hatch remains `claude mcp add`.
4. **Codex**: `docs/codex/config.toml` `[mcp_servers.omni_copilot]`
   (`command`/`args`); **forward secrets via Codex `env_vars`**, not literal
   `env` values; optional `AGENTS.md`. No plugin.
5. **Tests** (offline): `reserve_run` → id + `queued`, no LLM;
   `enforce_mcp_policy` refuses a tampered `request.json` (kind→rebase,
   `post=True`, off-list repo); child-writes-own-pid then `queued→…→done`; child
   crash → parent-on-exit `failed`; **lazy** reconcile: a `running` run with a
   dead owner+child resolves on the next `get_status` (no restart); **two
   servers**: B leaves A's live `queued` run alone but reconciles a dead-owner
   run; single-writer (no lost `child_pid`/ownership under a simulated
   parent+child race); CLI abort leaves no dir; stdout hygiene; boundary (bad
   id/off-list repo/negative pr; capped report + `next_offset`); no
   post/push/debug tool in V1 schema. Plus a **live smoke** `start_review`.
6. **Docs**: `CODE_TOUR.md` §11 MCP entry; new `doc/MCP.md`.

### Acceptance
- CLI unchanged/in-process; aborts leave no run dir.
- A rewritten `request.json` cannot run a non-`READ_ONLY_KINDS` kind, post, push,
  or an off-list repo.
- No lost updates to `run_status.json` (single writer + flock); ownership fields
  survive every transition.
- No run stays non-terminal: completion/exception (child), child-death
  (parent-on-exit), post-startup orphan (lazy/sweeper) — all ownership-gated;
  no server touches a live owner's run.
- `get_result` size-capped with `next_offset`+`report_path`; server stdout is
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
  list** (full manifest + dedup matrix are local artifacts, not committed).
- Phases: local prep (no mutations) → audit/dedup → author pages → minimal nav →
  hygiene → open PR → `zuiho-kai:master`.

---

## Sequencing & ownership
- WS1 and WS2 are independent.
- **WS1** is in-repo → proceeds on owner's go; PR to `tzhouam/vllm-omni-copilot`.
  Order: `enforce_mcp_policy` + `reserve_run` + reserved-exec child (single-
  writer) → ownership stamps + parent-on-exit + lazy/startup reconciliation →
  MCP subprocess/queue → boundary/pagination → packaging. (`pr-debug-report` +
  `start_debug` is a fast-follow.)
- **WS2** external repo → **every mutation (fork/commit/push/PR) needs explicit
  owner approval before it happens**; only local uncommitted prep runs unattended.

## What changed from rev 5 (per the review)
1. **Kind name fixed**: V1 uses `issue_answer` (not `issue_assist`); the gate now
   references `READ_ONLY_KINDS` from `task_spec.py` so it can't drift (blocker 1).
2. **Marketplace flow corrected** to the verified `.claude-plugin/marketplace.json`
   + `/plugin marketplace add` + `/plugin install <plugin>@<marketplace>`;
   marketplace always required (blocker 2).
3. **Reconciliation is lazy-at-read + parent-on-exit + startup/periodic**, not
   startup-only — closes the post-startup-orphan liveness gap (blocker 3).
4. **Single-writer protocol**: the child writes its own pid first; the parent
   never writes during the run; reconcilers write only after confirming the
   writer dead, under `flock`, preserving ownership fields — removes the
   parent/child write race (implementation race).
5. **Codex secrets via `env_vars`**, not literal `env` values.

## Open decisions
None blocking. One residual to confirm at implementation: whether any plugin
install hook can run a package install (assumed no). The remaining gate is owner
approval — go for WS1, per-mutation approval for WS2.
