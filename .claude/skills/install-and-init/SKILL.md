---
name: install-and-init
description: Install InferMatrixCopilot from a clone and initialize it to a verified working state — install.sh (venv + editable package + wrapper), .env configuration, doctor preflight, smoke verification, and target-repo onboarding (adapter/profile init). Use when setting up on a new machine or fresh clone, when doctor shows failures, when the ./infermatrix-copilot wrapper or venv is broken, or when adding a new target repo.
---

# Install and init InferMatrixCopilot

Goal state: `./infermatrix-copilot doctor` all green, a `--plan-only` run prints a
plan, and the target repo has an adapter (+ profile for non-seed repos).
Everything below is dry-run-safe: no step posts, pushes, or needs a GPU.

## 1. Install (one command, idempotent)

```bash
cd <clone of InferMatrixCopilot>
bash install.sh
```

What it does, in order: reuses an **active** virtualenv if one is exported,
else reuses `./.venv`, else creates `./.venv` with the newest of
`python3.12/3.11/3` (override with `OMNI_PYTHON=<interpreter>`); installs the
package editable (`pip install -e .`); seeds `.env` from `.env.template` only
if absent (never overwrites); writes the repo-local `./infermatrix-copilot`
wrapper (PATH is never modified); records what it created in
`.install-manifest`; finishes by running `doctor`.

- Failure "could not create a virtualenv" → the printed fix is exact
  (usually `sudo apt install python3.X-venv`, or set `OMNI_PYTHON`).
- `bash install.sh --uninstall` removes only manifest-recorded artifacts and
  deliberately never touches `.env`.
- Re-running `install.sh` is the supported repair for a broken wrapper or venv
  — do not hand-edit the wrapper.

## 2. Configure `.env` (git-ignored — NEVER commit it)

Minimum to be operational:

```bash
ANTHROPIC_API_KEY=sk-...            # Anthropic key, or a DeepSeek key with
ANTHROPIC_BASE_URL=                 # ...the /anthropic-compatible base URL set
AGENT_MODEL=claude-sonnet-5         # default agent reasoning model
REPO_PATHS={"vllm-omni": "/abs/path/to/vllm-omni"}   # JSON: repo name -> path
DEFAULT_REPO=vllm-omni
VLLM_OMNI_REPO=/abs/path/to/vllm-omni     # manifest ${VAR} fallbacks; keep in
VLLM_UPSTREAM_REPO=/abs/path/to/vllm      # sync with REPO_PATHS
```

Rules:
- Absolute machine paths belong here and only here — committed files must stay
  portable (`test_repo_neutral_core` enforces the src/ side).
- Leave `ALLOW_PUSH=0` and `ALLOW_POST=0` during setup. Every workflow is a
  useful dry run without them.
- Multi-line/JSON values (e.g. `LLM_MIXTURE`) must be single-quoted.
- Optional, skip at first init: `ECO_MODEL`/`PERFORMANCE_MODEL` (dual-path),
  `REVIEWER_MODEL`, `INTENT_MODEL`, escalation email (`NOTIFY_EMAIL` +
  Resend/SMTP), MoA (`LLM_MIXTURE`, `MOA_WHEN`, `MOA_MAX_USD`),
  `REBASE_ORCHESTRATOR_CMD` (only for the locked nightly-rebase delegation).

## 3. Preflight — doctor

```bash
./infermatrix-copilot doctor
```

Checks: package importable, `ANTHROPIC_API_KEY` set (name only — values are
never printed), `gh` installed **and authenticated**, `REPO_PATHS` entries
exist, `.env` parses, MoA config valid if set. Every ✗ line *is* the fix; the
most common one is `gh auth login` (needed once). Doctor reads the repo's own
`.env` regardless of the directory you invoke it from.

## 4. Smoke-verify (no cost, no writes)

```bash
./infermatrix-copilot --playbook pr-review --plan-only   # resolves + prints the plan, executes nothing
<venv>/bin/pytest                                        # offline suite: no GPU, no network, no API key
```

Then one real read-only run (needs the LLM key and `gh`):

```bash
./infermatrix-copilot -p "review pr <N>"
```

Expected: TaskSpec echo → `[y/N]` confirm → run directory under
`~/.infermatrix-copilot/runs/run-<ts>-<uuid6>/` with `RUN_REPORT.md`.
Note: `-p`/chat intent parsing is **LLM-only** — there is no offline
fast-path. With no key, only `--playbook ... --plan-only` and `doctor` work.
In `-p --yes` mode an ambiguous request exits nonzero with a clarifying
question by design; add the PR/issue number rather than retrying.

## 5. Init the target repo(s)

- **vllm-omni** (adapter zero) ships preconfigured in
  `adapters/vllm_omni/manifest.yaml` — modules, waves, `push.allowed: false`,
  protected `main`. Nothing to init beyond the `.env` paths.
- **A new repo**: add it to `REPO_PATHS`, then

  ```bash
  ./infermatrix-copilot -p "profile the repo" --yes
  ```

  Stage 0 fingerprints the repo and, for an unknown repo, writes a **draft**
  adapter + `BOOTSTRAP_REPORT.md` and stops for human review — high-risk
  manifest sections (`push`/`repo`/`upstream`) are human-only; review and flip
  the draft yourself before rerunning. Subsequent stages populate the
  evidence-gated profile under `adapters/<repo>/profile/`.
- Periodic maintenance (explicit-only candidate playbook):
  `./infermatrix-copilot --playbook profile-consolidate --yes`.

## 6. Optional extras

- MCP server for Claude Code/Codex: `pip install -e '.[mcp]'` (kept out of the
  base install), setup in `doc/MCP.md`; plugin/marketplace under
  `.claude-plugin/` + `plugin/`.
- Global command: `ln -s "$PWD/infermatrix-copilot" ~/.local/bin/infermatrix-copilot`.

## Verification checklist

1. `./infermatrix-copilot doctor` → all ✓.
2. `./infermatrix-copilot --playbook pr-review --plan-only` → plan printed, exit 0.
3. `pytest` → green (offline).
4. One `-p "review pr <N>"` run → `RUN_REPORT.md` produced, nothing posted.

## Anti-patterns

- Committing `.env`, echoing key values, or copying absolute paths into
  committed files.
- Setting `ALLOW_PUSH=1`/`ALLOW_POST=1` "to test the install" — outward writes
  are double-gated and never needed to verify setup.
- `pip install` into the system Python instead of the install.sh venv flow.
- Expecting `-p`/chat to work without a configured LLM (intent is LLM-only).
- Hand-repairing `./infermatrix-copilot` or deleting `.venv` piecemeal —
  rerun `bash install.sh` (or `--uninstall` first).
- Running `install.sh --uninstall` to reset config — it never removes `.env`.
