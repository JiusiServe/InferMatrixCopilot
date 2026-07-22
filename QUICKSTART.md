# Quickstart — vllm-omni-copilot

A playbook-driven repo-maintenance copilot for vLLM-Omni. One natural-language
interface reviews PRs, debugs CI, rebases branches, answers/triages issues, and
profiles repos — with a hard safety model: **everything is dry-run by default**,
and natural language can never widen permissions.

New to the code? Read [`doc/CODE_TOUR.md`](doc/CODE_TOUR.md) (data-flow
walkthrough) and [`doc/DESIGN.md`](doc/DESIGN.md) (the why). This page just gets
you running.

---

## 1. Install (one command)

```bash
bash install.sh
```

Creates/reuses a venv, installs the package editable, seeds `.env` from the
template (never overwrites), writes the repo-local `./omni-copilot` wrapper (no
PATH mutation), and runs `doctor`. `bash install.sh --uninstall` removes only
what it created (never touches `.env`).

> On this box it's already installed in `/rebase/.venv` — `./omni-copilot` works
> as-is. Skip to step 3 unless you changed `.env`.

## 2. Configure `.env` (git-ignored — NEVER commit it)

Minimum to be operational:

```bash
ANTHROPIC_API_KEY=sk-...            # or a DeepSeek /anthropic key
ANTHROPIC_BASE_URL=                 # set if using a compatible endpoint
AGENT_MODEL=claude-sonnet-5         # default reasoning model
REPO_PATHS={"vllm-omni": "/rebase/vllm-omni"}   # JSON map: repo name -> path
DEFAULT_REPO=vllm-omni
```

Leave the write guards **off** until you deliberately want outward writes:

```bash
ALLOW_PUSH=0     # 1 = allow git push (still --force-with-lease only, never to main)
ALLOW_POST=0     # 1 = allow posting PR comments / issue replies
```

Optional: `REVIEWER_MODEL`, `INTENT_MODEL`, `PERFORMANCE_MODEL` (dual-path),
`NOTIFY_EMAIL`+`RESEND_API_KEY`/SMTP (escalation email), `LLM_MIXTURE` (MoA).
See `.env.template` for all knobs.

## 3. Preflight

```bash
./omni-copilot doctor          # every ✗ prints the exact fix
```

Checks: package installed, `ANTHROPIC_API_KEY` set (name only, value never
printed), `gh` installed **and authenticated** (`gh auth login` once),
`REPO_PATHS` exist, `.env` parses, MoA config valid if set.

---

## 4. First commands

You never need to memorize task kinds or trigger phrases — plain English routes
itself; a full GitHub URL routes to the right repo/workflow.

```bash
# Review a PR (read-only; produces a review, does not post)
./omni-copilot -p "review pr 5134"
./omni-copilot -p "do a full-depth review of pr 5134"
./omni-copilot -p "review https://github.com/vllm-project/vllm-omni/pull/5134"

# Debug failing CI on a PR (report-only = read-only triage)
./omni-copilot -p "debug pr 5134, report only"

# Answer / triage issues
./omni-copilot -p "answer issue 4842, do not post"
./omni-copilot -p "triage recent open issues"

# Rebase a PR onto its base
./omni-copilot -p "rebase pr 5134"

# Compound request -> ordered queue, target carries over
./omni-copilot -p "rebase pr 5134, then review it"
```

Useful flags:

| Flag | Effect |
|---|---|
| `--yes` | skip the `[y/N]` confirmation (headless/scripting) |
| `--plan-only` | resolve and print the plan, execute nothing |
| `--performance` | use the high-capability model tier for this run (default: eco) |
| `--resume` | re-enter the last run at its first incomplete step |
| `--playbook <name>` | run a specific playbook (incl. candidates) |
| `--report-only` | with `--playbook`: read-only variant |
| `--task-param k=v` | with `--playbook`: pass a param (repeatable) |
| `--no-chat` | plain command REPL instead of chat |

In `-p --yes` mode an ambiguous request exits **nonzero** with a clarifying
question instead of guessing — safe for eval harnesses and CI.

## 5. Chat mode (default, no `-p`)

```bash
./omni-copilot
```

A Claude-Code-style conversation: ask about the repo or past runs, and run work
through tools — same TaskSpec, planner, and `[y/N]` gates as the flag CLI (chat
can never widen permissions). Built-ins: `/status`, `/logs [n]`, `/playbooks`,
`/resume`, `/quit`. Repo reads are jailed to configured repos; `.env*` refused.

---

## 6. Safety model (read this before you post or push)

Outward effects are **double-gated** — both must be true:

- **Post a PR comment / issue reply** → the request must carry explicit `post`
  intent (e.g. `"review pr 5134 and post it"`) **AND** `ALLOW_POST=1`.
- **git push** → an allowing push policy **AND** `ALLOW_PUSH=1`. Force is
  `--force-with-lease` only; **`main` is never pushed to**, policy or not.

Anything short of both is a **dry run** that shows exactly what it would do.
Adapter zero (`adapters/vllm_omni/manifest.yaml`) declares `push.allowed: false`
— vLLM-Omni changes ship via PR, never a direct push. Blocked runs write
`ESCALATION.md` and exit 3 (notify, never guess).

## 7. Where output goes

```
~/.omni-copilot/runs/run-<ts>-<uuid6>/
  RUN_REPORT.md      the deliverable (review / answer / debug summary)
  DIAGNOSTICS.md     per-step diagnostics
  run_trace.jsonl    append-only fact log
  progress.json      step checkpoints (what --resume reads)
  metrics.json       CATQ run metrics
  ESCALATION.md      only when blocked
~/.omni-copilot/worktrees/<repo>-pr<n>/   PR-time checkout for reviews
~/.omni-copilot/sessions/                  chat transcripts
```

## 8. Playbooks

```bash
./omni-copilot -p "…"                          # planner picks the vetted playbook
./omni-copilot --playbook pr-review --plan-only # run one by name
```

Registered: `pr-review`, `pr-debug`, `pr-rebase`, `issue-assist`,
`issue-triage`, `repo-rebase` (**locked** — delegates to the proven 5-phase
nightly orchestrator), `repo-rebase-native` (candidate), `repo-profile`,
`profile-consolidate` (candidate; Stage-4 maintenance). Candidates are invisible
to the planner — run them explicitly with `--playbook`.

## 9. Onboard a new repo (profile)

```bash
./omni-copilot -p "profile the repo" --yes     # fingerprint -> draft profile
./omni-copilot --playbook profile-consolidate --yes   # Stage-4 dedupe/refresh
```

Repo knowledge lives at the edge in `adapters/<repo>/` (human-gated
`manifest.yaml` + agent-established, evidence-gated `profile/`) — never in
`src/`. `PROFILE_BRIEFING_ENABLED=0` runs the {no-profile} eval ablation arm.

## 10. Advanced: MCP server (Claude Code / Codex)

```bash
pip install -e '.[mcp]'      # optional extra, kept out of the base install
```

Exposes read-only tools — `start_review` / `start_issue_answer` /
`start_issue_triage` (return a `run_id`), `get_status` / `get_result` (poll),
`list_playbooks`, `doc_read` / `doc_search`. Reviews take 5–12 min, so the API
is start-then-poll. Only the read-only kinds are reachable and `post` is
force-disabled at both the server boundary and the run subprocess. Setup:
[`doc/MCP.md`](doc/MCP.md).

---

## Troubleshooting

- **"capability gap … run repo_profile"** — the task needs repo knowledge the
  profile doesn't provide; profile the repo first (step 9).
- **Clarifying question in `-p --yes`** — the request was ambiguous; it exits
  nonzero by design. Add the PR/issue number or the `post`/`report only` intent.
- **Review/answer looks blocked but has content** — check `RUN_REPORT.md`; a
  substantive draft is salvaged and delivered even when a step escalates.
- **Anything red in `doctor`** — the message *is* the fix. `gh` auth is the most
  common one: `gh auth login`.

Deeper reading: [`doc/DESIGN.md`](doc/DESIGN.md) ·
[`doc/CODE_TOUR.md`](doc/CODE_TOUR.md) ·
[`doc/IMPLEMENTATION_STATUS.md`](doc/IMPLEMENTATION_STATUS.md) ·
[`doc/SPEC/`](doc/SPEC/README.md) · [`doc/MCP.md`](doc/MCP.md)
</content>
</invoke>
