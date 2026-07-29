---
name: imreview
description: Review a PR or local changes with InferMatrixCopilot Direct mode. Use when the user invokes imreview.
---

Call InferMatrixCopilot `review` with `mode="direct"` for the supplied target,
or the current PR/worktree when omitted. Read `knowledge_entry`, inspect the
live code, and return only evidence-backed findings with file/line references.
Do not post or edit unless explicitly asked.
