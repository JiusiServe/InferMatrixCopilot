---
name: imreview
description: Review a PR or local changes with InferMatrixCopilot Direct mode. Use when the user invokes imreview.
---

Call InferMatrixCopilot `review` with `mode="direct"` for the supplied target,
or the current PR/worktree when omitted. Read `knowledge_entry`, inspect the
live code, and return only evidence-backed findings with file/line references.
Format each actionable finding like a normal GitHub inline review comment:
identify the exact path and line/hunk, then explain the concrete triggering
input or call path, the observed behavior, why it matters, and the smallest
fix direction. Use the knowledge rules to discover and verify findings, but do
not expose rule IDs, coverage tables, matrices, or PASS/MISSING_EVIDENCE rows
unless the user explicitly asks for the full audit artifact. If there are no
findings, say so briefly and name any material validation gap. Do not post or
edit unless explicitly asked.
