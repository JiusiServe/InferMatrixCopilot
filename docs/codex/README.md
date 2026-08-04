# Use InferMatrixCopilot in Codex

The default MCP is a knowledge provider. Codex uses its currently selected
model to review code, so there is no API key or model configuration.

## Install

```text
# Windows
install.cmd

# macOS / Linux
./install-mcp.sh
```

The bootstrap detects Codex automatically. It uses the same MCP descriptor and
Agent Skill as Claude, Cursor, and other compatible hosts.

Restart Codex, then paste:

```text
Use InferMatrixCopilot to review
https://github.com/vllm-project/vllm-omni/pull/5172.
```

The plugin also adds the `imreview` skill, so the short form is:

```text
$imreview https://github.com/vllm-project/vllm-omni/pull/5172
```

Codex skills use `$name`, not `/name`; run `/skills` if the skill is not shown.

Codex calls `review`, receives the local `knowledge/AGENTS.md` path plus a
compact first-review checklist, and follows that document's routing map itself.
The MCP does not guess which owner applies and does not inject complete rule
pages. After pinning the snapshot, Codex immediately reports the pinned head SHA,
current CI, mergeability, and preliminary findings in the host conversation.
It does this before reading knowledge, searching source, or running tests and
does not wait for CI completion or resolved mergeability. Codex then calls
Direct once with the collected title, body, and changed files, uses the embedded
`quick_map` in each exact route without opening the full rule page, and runs
knowledge/source and validation tracks concurrently. It reuses one in-review
evidence packet and runs an import/version
compatibility preflight before pytest. Validation results are bound to the head
SHA and an environment fingerprint. The progress update is not an interim
GitHub comment. Before the only final review comment, Codex calls
`validate_direct_review`. A normal small fix uses `subtraction_signal="none"`
without a minimality proof. Only a diff that adds or expands a helper, class,
fallback, compatibility branch, or public behavior uses `"triggered"` and
requires subtraction evidence.

The tool response is intentionally small:

```json
{
  "mode": "direct",
  "knowledge_entry": "C:\\...\\knowledge\\repos\\vllm-omni\\components\\serving\\rules.md",
  "knowledge_routes": [
    {
      "owner": "serving",
      "path": "C:\\...\\knowledge\\repos\\vllm-omni\\components\\serving\\rules.md",
      "reason": "title/body: endpoint, request",
      "quick_map": "## Direct 代码快速入口\n...",
      "read_required": false
    }
  ],
  "navigation_policy": {
    "progress_before_knowledge": true,
    "use_embedded_quick_maps": true,
    "open_route_file_only_for_concrete_ambiguity": true,
    "max_routes": 3,
    "stop_after_routes": true
  },
  "execution_budget": {
    "profile": "code",
    "knowledge_file_reads": 0,
    "validation_commands": 4,
    "total_command_calls": 20,
    "hard_ceiling": true,
    "extension_command_calls": 4
  },
  "first_review_checklist": ["...", "Run subtraction only when the diff has a subtraction signal ..."],
  "progress_update": {
    "deadline_seconds": 60,
    "channel": "host_conversation",
    "required_fields": ["head_sha", "ci_status", "mergeability", "early_findings"],
    "early_findings_status": "preliminary",
    "continue_review": true,
    "github_comment": false
  },
  "completion_gate": {
    "tool": "validate_direct_review",
    "subtraction_signal": {
      "none": "no subtraction evidence required",
      "triggered": "require subtraction evidence"
    },
    "triggered_require_one_of": [
      "subtraction[{anchor, action, risk}]",
      "minimality_proof{scope_ledger, abstraction_census, why_no_safe_deletion}"
    ],
    "final_comment_count": 1,
    "if_missing": "partial_review"
  }
}
```

Strict uses the same installed MCP. The wheel already includes its playbooks,
adapters, and skills. Configure the local checkout during installation:

```text
install.cmd --repo-path D:\path\to\vllm-omni
```

Then set either `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in
`~/.infermatrix-copilot/.env`. Each provider also has an optional
`ANTHROPIC_BASE_URL` or `OPENAI_BASE_URL` for a proxy or compatible gateway.
With one key configured the provider is selected automatically; with both,
set `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=openai`. Restart Codex, and say:

```text
Use InferMatrixCopilot in Strict mode to review
https://github.com/vllm-project/vllm-omni/pull/5172.
Do not return a review until the strict run is complete.
```

Strict runs the packaged `pr-review` playbook with its configured model,
progress tracking, report generation, and publishing gates. Poll
`get_review_result` until the run is terminal.

Strict never posts implicitly. Posting still requires both an explicit
`post=true` tool argument and server-side `ALLOW_POST=1`.

Restart Codex after installation. Use `/mcp` or `codex mcp list` to confirm that
`infermatrix-copilot` is connected, and `/skills` to confirm that `imreview` and
`imupdate` are available.

## What the default MCP exposes

- `review(target, repo?, mode="direct", post=false, title="", body="",
  changed_files=[], review_depth="", repo_path="")`: after the host progress
  update, Direct uses title/body to
  return at most three exact owner/model routes with compact embedded
  `quick_map` excerpts. Changed files only validate scope. The host does not
  open full rule files unless a concrete ambiguity blocks source review and
  treats the returned docs/code `execution_budget` as a hard ceiling. A single
  bounded extension is reserved for one stated unresolved P1/high-risk
  contract.
  Strict starts the packaged workflow and accepts `review_depth` plus an
  optional local checkout override through `repo_path`.
- `validate_direct_review(subtraction_signal, subtraction?, minimality_proof?,
  final_comment_count=1)`: `none` completes an ordinary small fix without a
  minimality proof. `triggered` requires anchored subtraction actions or
  concrete evidence that the inspected scope is already minimal.
- `update_knowledge(repo?)`: keeps `repo` only for call compatibility and
  returns `knowledge/CONTRIBUTING.md`; the host model follows that document and
  edits the Markdown files itself.
- `get_review_result(run_id, offset?)`: polls and pages the Strict report.
- `get_review_status(run_id)`: returns the Strict run's durable progress.
- `doc_search(query, repo?)`: finds deeper model/component rules.
- `doc_read(path, repo?)`: reads a selected knowledge page.

Direct mode does not run another model, edit knowledge, post comments, or push
code. Its deterministic router selects bounded knowledge owners from the PR
description; Codex still owns scope validation and the truth of cited code
evidence. The completion validator checks review structure.

## Optional autonomous BYOK workflow

The autonomous workflow has separate setup and documentation:
[`../autonomous-workflow.md`](../autonomous-workflow.md).
