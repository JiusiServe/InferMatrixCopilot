# Code Taste · Review Flow

Use this for new execution paths, push-time diff review, and human inline review handling.

## New execution paths

Trigger when adding step-wise, graph, cache, batching, serving, offline, benchmark, or any second path for existing behavior.

Hard rules:

- Normal path and new path must not duplicate parsing / normalization / validation.
- Request parsing belongs in the data owner helper; both paths call it.
- Helper return values are named by consumer, not by vague normalized value.
- If a consumer needs a special default, name it specifically, such as `model_bot_task` vs `system_prompt_bot_task`.
- New path only diverges at explicitly unsupported capability boundaries, and those boundaries fail fast or no-op visibly.
- Tests cover one default and one non-default field. Default-only tests do not prove parsing parity.

Self-check:

- Is this field one chain from ingress to every consumer?
- Did the new path copy ten lines from normal path?
- Is one normalized value feeding two different semantic consumers?
- Is the default a user default or a consumer internal default?

## Diff smell pass

Before commit / push, resolve the real target base and collect the current tracked and untracked surface with the canonical [full diff review](reviewer-lens-gates.md#full-diff-review). Do not hardcode a remote or default branch, and do not inspect only `HEAD` when the implementation is still in the working tree.

Check:

- file list matches PR topic;
- new helper is not a copy;
- variable names need no oral explanation;
- test file and test class names match behavior owner;
- comments explain strategy source;
- public surface did not expand accidentally;
- new parameter docstring and contract are updated;
- rank/stage/mode guards live in the right owner;
- shared schema constructors / unpack sites / consumers were grep-checked;
- no "compatibility" or "fallback" silent patch hides an error.

If the diff requires a review comment explaining "actually this is because...", first improve code, naming, or comments.

## Human reviewer simulation

Each new logic block must answer:

- Why here?
- Why this name?
- Why not reuse existing implementation?
- Why this test and this file?
- Why this default?
- Which edge case owns this branch?
- Which upstream / official behavior matches it?
- Will adding a second model / backend copy this a third time?
- If a future caller passes the optional parameter wrong, where does it fail?
- Is this a shared state ABI change, and were all constructors/unpack sites checked?

If not, redesign before coding.

## Inline review action mapping

Reviewer anchor lines are source of truth. Before editing an inline review comment:

```text
Comment: <reviewer 原文>
Anchor: <file:line + 锚点代码实际行为>
Pronoun target: <this / it / here / strategy 指向锚点里的哪个实体>
Reviewer asks: <按锚点语义拆成 1-3 个具体要求>
Code action: <要改哪个 owner/module，什么逻辑从哪里移到哪里>
Done check: <回到锚点附近看 diff，reviewer 是否会认为正面解决>
```

Bad signs:

- comment anchors output alignment, but the fix edits condition-image crop;
- reviewer says "add it to image processor" but `it` was never resolved;
- adjacent concept changed, anchor behavior unchanged;
- only a comment was added while logic remains in the questioned owner.

Full reviewer-lens gates are in [reviewer_lens_gates](reviewer-lens-gates.md). The spawn prompt is in [reviewer_lens_prompt](reviewer-lens-prompt.md).
