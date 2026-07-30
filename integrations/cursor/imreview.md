Use the InferMatrixCopilot MCP server to review the target supplied with this
command. If no target is supplied, review the current PR or working tree.

Call `review` with `mode="direct"`, read the returned `knowledge_entry`, follow
its routing instructions, inspect the live target, and return only
evidence-backed findings with file and line references.

Lead with a concise plain-language conclusion, user impact, and next action.
Put rule-ID coverage tables after that explanation; never return only a rule-ID
table.

Do not use Strict mode, post comments, or modify code unless explicitly asked.
