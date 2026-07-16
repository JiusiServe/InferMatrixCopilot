# PR Body Model Evidence

Use this for new model, pipeline, backend, or checkpoint adapter PRs.

## Split evidence tiers

`0 missing / 0 unexpected`, stub smoke, shape checks, and no-NaN checks prove plumbing only. They do not prove upstream semantic parity, real checkpoint correctness, quality, or e2e serving behavior.

Write the PR body in three separate sections when applicable:

```markdown
### Source parity
- Scheduler / denoising: <upstream file:line or "source inference">
- Embedding order: <upstream file:line>
- Activation: <upstream file:line>
- Token order: <upstream file:line>
- Attention mask / pad-eos: <upstream file:line or explicit deviation>

### Stub plumbing smoke
- Command:
- Inputs:
- Allowed conclusion: model wiring / tensor shapes only

### Real checkpoint validation
- Checkpoint:
- Tokenizer / processor status:
- Strict load:
- Command:
- Allowed conclusion:
```

## Hard rules

- Stub smoke cannot support real checkpoint, quality, or e2e conclusions.
- Clean `load_state_dict` belongs under plumbing evidence, not correctness.
- Missing tokenizer / processor / config must be a fail-fast blocker or explicitly pending; do not silently fall back.
- If source parity is inferred rather than directly traced to upstream source, label it `source inference`.
- After editing the PR body, read it back with `gh pr view` and verify fences, tables, and allowed conclusions are not misaligned.

## What caused this

PR #3474 GO-1-Air showed that shape-clean evidence can still hide scheduler, embedding order, activation, token order, and attention-mask semantic drift. Reviewer-facing PR bodies must not imply model correctness from plumbing-only evidence.
