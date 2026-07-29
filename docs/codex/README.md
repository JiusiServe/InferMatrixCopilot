# Use InferMatrixCopilot in Codex

The default MCP is a knowledge provider. Codex uses its currently selected
model to review code, so there is no API key or model configuration.

## Windows

```powershell
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot
.\install-codex.ps1
```

Restart Codex, then paste:

```text
Use InferMatrixCopilot to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

Codex first inspects the live PR, then calls `review` with the changed
files so the returned knowledge is specific to the affected modules.

For server-enforced sequencing, say:

```text
Use InferMatrixCopilot strict workflow mode to review
https://github.com/vllm-project/vllm-omni/pull/5172.
Do not return a review until the strict run is complete.
```

This uses a persistent `evidence → gates → review → verify → complete` state
machine. Codex performs the reasoning; the MCP refuses skipped or stale stages.
This guarantees the sequence for reports produced through the MCP, but an MCP
host can still bypass a tool entirely. Use the autonomous BYOK/managed executor
when the workflow itself must own every model call.

## macOS/Linux

```bash
git clone https://github.com/JiusiServe/InferMatrixCopilot.git
cd InferMatrixCopilot
python3.11 -m venv .venv
./.venv/bin/python -m pip install -e '.[mcp]'
codex mcp add infermatrix_copilot -- "$PWD/.venv/bin/infermatrix-copilot-mcp"
```

Restart Codex after installation. Use `/mcp` or `codex mcp list` if you want to
confirm that `infermatrix_copilot` is connected.

## What the default MCP exposes

- `review(target, changed_files?, mode="direct")`: the only starting point.
  Direct is the default; strict is selected only when the user explicitly asks.
- `submit_review_stage(run_id, stage, artifact)`: validates and advances one
  strict stage. Each response includes an `artifact_example`; scalar list fields
  are normalized automatically.
- `get_review_status(run_id)`: resumes a strict run.
- `doc_search(query, repo?)`: finds deeper model/component rules.
- `doc_read(path, repo?)`: reads a selected knowledge page.

It does not run another model, post comments, push code, or require a local
target-repository path.

## Optional autonomous BYOK workflow

The old start/poll workflow is still available as
`infermatrix-copilot-workflow-mcp`. It runs its own agents and therefore still
requires `.env` model and repository configuration. It is intentionally not
the default Codex experience.
