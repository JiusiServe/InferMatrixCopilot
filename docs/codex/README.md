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

The installer also adds the `imreview` skill, so the short form is:

```text
/imreview https://github.com/vllm-project/vllm-omni/pull/5172
```

Codex calls `review`, receives the local `knowledge/AGENTS.md` path, and follows
that document's routing map itself. The MCP does not guess which owner applies
and does not inject complete rule pages.

The tool response is intentionally small:

```json
{
  "knowledge_entry": "C:\\...\\InferMatrixCopilot\\knowledge\\AGENTS.md"
}
```

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

- `review(target, repo?, mode="direct")`: Direct ignores `repo` and returns
  `knowledge/AGENTS.md`. Strict uses `repo` only when explicitly selected.
- `update_knowledge(repo?)`: keeps `repo` only for call compatibility and
  returns `knowledge/CONTRIBUTING.md`; the host model follows that document and
  edits the Markdown files itself.
- `submit_review_stage(run_id, stage, artifact)`: validates and advances one
  strict stage. Each response includes an `artifact_example`; scalar list fields
  are normalized automatically.
- `get_review_status(run_id)`: resumes a strict run.
- `doc_search(query, repo?)`: finds deeper model/component rules.
- `doc_read(path, repo?)`: reads a selected knowledge page.

Direct mode does not run another model, choose a knowledge owner, edit knowledge
inside the MCP, post comments, or push code.

## Optional autonomous BYOK workflow

The autonomous workflow has separate setup and documentation:
[`../autonomous-workflow.md`](../autonomous-workflow.md).
