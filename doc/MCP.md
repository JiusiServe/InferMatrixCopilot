# MCP integration — Claude Code & Codex

The copilot ships an **MCP stdio server** (`infermatrix-copilot-mcp`, module
`src/infermatrix_copilot/mcp_server.py`) that exposes its **read-only** task kinds to
any MCP host. The standalone `infermatrix-copilot` CLI is unchanged; MCP is additive and
its dependency is gated behind the `[mcp]` extra.

## What it exposes (V1 — all read-only, start/poll)

A review can take 5–12 min, so each task is a **start + poll** pair: `start_*`
returns a `run_id` immediately; poll it with `get_result`.

| Tool | Kind | Notes |
|------|------|-------|
| `start_review(pr, repo?)` | `pr_review` | never posts |
| `start_issue_answer(issue, repo?)` | `issue_answer` | drafts only; never posts |
| `start_issue_triage(repo?)` | `issue_filter` | classifies recent open issues |
| `get_result(run_id, offset?)` | — | `{state, report?, next_offset?, report_path?}` |
| `get_status(run_id)` | — | `{status, progress?}` |
| `list_playbooks()` | — | the read-only kinds + backing playbooks |

There is **no** posting, pushing, rebase, or debug tool in V1. The surface is the
three `READ_ONLY_KINDS` (`pr_review`, `issue_answer`, `issue_filter`) and nothing
else — enforced in the child, so a rewritten `request.json` cannot widen it.
`repo` is restricted to `mcp_repo_allowlist` (default: `[default_repo]`).

## Install the package first (required by both hosts)

Installing a plugin / adding a Codex MCP entry does **not** install the Python
package — the `infermatrix-copilot-mcp` command must already resolve on PATH. Install a
pinned build:

```bash
uv tool install 'infermatrix-copilot[mcp]'      # or: pipx install 'infermatrix-copilot[mcp]'
# from a local checkout:  pip install -e '.[mcp]'
```

Provide credentials via the environment (or the repo `.env`): `ANTHROPIC_API_KEY`,
optionally `ANTHROPIC_BASE_URL`, `DEFAULT_REPO`, and repo paths.

## Claude Code

The repo is a plugin marketplace (`.claude-plugin/marketplace.json`) whose
`infermatrix-copilot` plugin (`plugin/.claude-plugin/plugin.json` + `plugin/.mcp.json`)
declares the stdio server. In Claude Code:

```
/plugin marketplace add JiusiServe/InferMatrixCopilot
/plugin install infermatrix-copilot@infermatrix-copilot-marketplace
```

Host-agnostic alternative (no plugin/marketplace) — register the server directly:

```
claude mcp add infermatrix-copilot -- infermatrix-copilot-mcp
```

> The exact marketplace-manifest schema and `/plugin` flow are per the current
> Claude Code docs (`discover-plugins.md`, `plugins.md`); re-check them at publish
> time if the CLI reports a manifest error.

## Codex

Add the block from `docs/codex/config.toml` to `~/.codex/config.toml`. Secrets are
forwarded **by name** via `env_vars` (read from your shell), not pasted as
literal values.

## Safety model (why the host cannot widen permissions)

- **Structural read-only.** `enforce_mcp_policy` runs at the boundary AND
  (authoritatively) in the child: only `READ_ONLY_KINDS`, `post` forced False,
  repo allowlisted, `pr`/`issue` positive, unknown params stripped — regardless
  of what a same-user process may have written into `request.json`.
- **Isolated execution.** Each run is a subprocess (`python -m infermatrix_copilot
  --execute-reserved <id>`); its stdout goes to `<run_dir>/console.log`, so the
  server's stdio channel carries only MCP protocol bytes.
- **Durable, single-writer status.** `run_status.json` (see `run_status.py`) is
  written by one process at a time under an advisory lock; a run always reaches a
  terminal state — via the child, the parent after `.wait()`, or ownership-aware
  reconciliation (lazy-at-read / startup) for runs orphaned by a server death.
- **Multi-server safe.** Claude Code and Codex may each launch a server; runs
  carry `owner_server_id`/`owner_server_pid`/`child_pid`, and a server reconciles
  only runs whose owner is confirmed dead — never another live server's queued
  run. (The queue serializes one server process; machine-wide serialization would
  need a filesystem lock — deferred.)
