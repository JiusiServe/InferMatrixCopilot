# AFD local rebase

`repo-rebase-v3` in `local_rebase` mode synchronizes the official AFD main into
the result branch, adapts it to the fixed vLLM target through Codex, runs local
validation, and publishes the result branch. It does not run remote CI or merge
into main.

This guide is for running the standalone Copilot program. You can also ask
Codex App to adapt AFD, run checks, and push a work branch directly; that does
not require this CLI/MCP integration. The standalone program starts a separate
Codex session using the CLI login, rather than continuing the App conversation.

## Setup

Install Copilot with its MCP extra in a control environment with Python 3.11 or
newer. The AFD target environment is separate and must support the configured
vLLM wheel, pytest, and pre-commit.

```bash
uv pip install --python /path/to/copilot-venv/bin/python -e '.[mcp,dev]'
codex login status
```

Use a dedicated AFD checkout. Its `upstream` remote must point to the official
AFD repository. Configure `fork` to the writable repository listed in the AFD
adapter's `push.remote_url`; the current adapter publishes only
`codex/vllm-0.28-sync` to `jiaran-king/afd-plugin`.

```bash
export AFD_PLUGIN_REPO=/path/to/afd-checkout
export AFD_PLUGIN_VENV=/path/to/afd-target-venv
export VLLM_UPSTREAM_REPO=/path/to/vllm-checkout
export VLLM_WHEEL_VARIANT=cu130
export VLLM_WHEEL_ARCH=x86_64
export STRICT_BACKEND=codex
```

If the `codex` launcher on PATH cannot start, set `STRICT_BACKEND_CLI` to an
existing working Codex executable. Verify that executable with `--version` and
`login status`, and ensure its version supports your configured model; this
setting does not require changing the system installation.

The wheel variant and architecture must match the target environment. Codex
uses the current CLI login; no Anthropic API key is required. Set
`STRICT_BACKEND_MODEL` only to override the CLI's configured model.

For the non-interactive session, Copilot approves only its injected
`infermatrix-tools` MCP server. The bridge still enforces tool scope and plan
review before changes. This is a per-invocation override; it does not change
your global approval settings or approvals for other MCP servers.

## Run

Supply the full SHA of the previously adapted vLLM baseline. The adapter fixes
the target to `v0.28.0`; it does not follow vLLM main.

```bash
ALLOW_PUSH=true /path/to/copilot-venv/bin/infermatrix-copilot \
  --repo afd-plugin --playbook repo-rebase-v3 --yes \
  --task-param rebase_mode=local_rebase \
  --task-param last_rebase_commit=<previous-vllm-sha>
```

`--plan-only` prints the selected workflow without executing it. Assignment can
also be inspected using `--task-param rebase_mode=report_only` with the same
baseline; it analyzes the configured target ref without moving the source
checkout.

Each run fixes its AFD main and result branch inputs. Existing result history
is preserved, including when only the remote branch exists in a fresh checkout.
Text conflicts and semantic compatibility changes are handled separately.
Repositories without an explicit `repo.source_remote` keep the existing sync
behavior; this AFD integration does not add main merging to other adapters.

## Validation and publication

The AFD adapter runs two jobs: CPU unit tests and required target-runtime class
and signature tests. JUnit evidence records actual passed, failed, errored and
skipped test cases. Required runtime tests must execute against the configured
version and selected source commit. GPU/NPU/E2E tests are outside this local
acceptance set and are not reported as passed.

In local_rebase, a red baseline never exempts a failing target job. Changes made
by debug or pre-commit invalidate earlier results and trigger a bounded
verification pass. Publication requires completed checks, passing pre-commit,
and a consistent dependency pin and uv lock.

The publisher binds its commit to the tested content. It rejects changes made
after validation or by commit hooks. Pushes remain fast-forward-only on both
the first attempt and resume; a diverged remote is not overwritten. Protected
branches such as main are rejected.

Without `ALLOW_PUSH=true`, a validated local commit is retained and the run
stops before remote publication. A failed push likewise remains incomplete so
resume can retry without repeating adaptation.

```bash
ALLOW_PUSH=true /path/to/copilot-venv/bin/infermatrix-copilot --resume --yes
```

Resume uses the most recent saved run and its original inputs. Use a new run to
take a newer AFD main or a different vLLM target. Failed local rebase runs retain
their upstream scratch and editable-runtime artifacts for recovery. Successful
runs clean the scratch; the dedicated target environment is run infrastructure,
not a deployed serving environment.

Inspect `RUN_REPORT.md`, `FINAL_SUMMARY.md`, `substate.json`, the module plans,
test logs/JUnit reports and push WAL in the run directory. These distinguish
adaptation, validation and publication outcomes. A successful local run is not
evidence of GPU/NPU/E2E acceptance or a merge to main.
