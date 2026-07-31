# Use InferMatrixCopilot in Codex

The default MCP is a knowledge provider. Codex uses its currently selected
model to review code, so there is no API key or model configuration.

## Install

```powershell
codex plugin marketplace add JiusiServe/InferMatrixCopilot
```

Then open `/plugins` and install `infermatrix-copilot`. The plugin uses the
same MCP descriptor and Agent Skill as Claude, Cursor, and other compatible
hosts; there is no Codex-specific installer.

Restart Codex, then paste:

```text
Use InferMatrixCopilot to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

The plugin also adds the `imreview` skill, so the short form is:

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

Strict is the new public name for the previous Eco mode. It runs the same
configured model, `pr-review` playbook, progress tracking, report generation,
and publishing gates as Eco. Poll `get_review_result` until the run is
terminal.

Strict never posts implicitly. Posting still requires both an explicit
`post=true` tool argument and server-side `ALLOW_POST=1`.

Restart Codex after installation. Use `/mcp` or `codex mcp list` if you want to
confirm that `infermatrix-copilot` is connected.

## What the default MCP exposes

- `review(target, repo?, mode="direct", post=false)`: Direct ignores `repo`
  and returns `knowledge/AGENTS.md`. Strict maps to the previous Eco workflow.
- `update_knowledge(repo?)`: keeps `repo` only for call compatibility and
  returns `knowledge/CONTRIBUTING.md`; the host model follows that document and
  edits the Markdown files itself.
- `get_review_result(run_id, offset?)`: polls and pages the Strict report.
- `get_review_status(run_id)`: returns the old workflow's durable progress.
- `doc_search(query, repo?)`: finds deeper model/component rules.
- `doc_read(path, repo?)`: reads a selected knowledge page.

Direct mode does not run another model, choose a knowledge owner, edit knowledge
inside the MCP, post comments, or push code.

## Optional autonomous BYOK workflow

The autonomous workflow has separate setup and documentation:
[`../autonomous-workflow.md`](../autonomous-workflow.md).
