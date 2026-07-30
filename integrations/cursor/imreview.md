Use the InferMatrixCopilot MCP server to review the target supplied with this
command. If no target is supplied, review the current PR or working tree.

Call `review` with `mode="direct"`, read the returned `knowledge_entry`, follow
its routing instructions, inspect the live target, and return only
evidence-backed findings with file and line references.

Format each actionable finding like a normal GitHub inline review comment:
identify the exact path and line/hunk, then explain the concrete triggering
input or call path, the observed behavior, why it matters, and the smallest
fix direction. Use the knowledge rules to discover and verify findings, but do
not expose rule IDs, coverage tables, matrices, or PASS/MISSING_EVIDENCE rows
unless the user explicitly asks for the full audit artifact. If there are no
findings, say so briefly and name any material validation gap.

Do not use Strict mode, post comments, or modify code unless explicitly asked.
