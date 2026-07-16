# Reviewer Lens Cases

Keep this file short. It explains why the reviewer-lens rules exist without making the main checklist unreadable.

## PR #3626 HunyuanImage3 explicit size

Plain `code check` missed four reviewer-facing problems:

- duplicated resolution algorithm instead of reusing owner code;
- output alignment lived in pipeline when image processor owned the behavior;
- ratio token ids were non-contiguous, so `start + idx` was wrong;
- help text exposed implementation details instead of a clean surface.

Later iterations also showed:

- module-owner review missed committer concerns around `/v1/images/generations`, `mm_processor_kwargs`, PR body freshness, and endpoint bad paths;
- fixing a finding once was not enough because the fix moved tests to the wrong behavior owner;
- rebase dropped mainline `resolve_stop_token_ids(..., image_size=...)` semantics and changed shared chat-completions img2img keys.

## PR #3734 prefix-cache CPU staging

Sub-agent found no P0/P1, but reviewer-lens caught:

- optional `hidden_states_cpu` contract lacked CPU / contiguous / length rules;
- generic helper names leaked one caller's hidden-state concept;
- data contract was reviewed, execution-context contract was not;
- adding required fields to shared `ExecuteModelState` missed older positional constructors.

Rebase then missed the tail-only model path when `requires_full_prefix_cached_hidden_states=False`. State-matrix review is required after conflict resolution.

## PR #3734 CI fix

A new tail-only test activated old dormant code. Treat activated old code as current PR surface. Mock wrappers must match real runner wrappers, including property vs method behavior such as `.cpu` vs `.cpu()`.

## PR #3723 image edit streaming

Happy-path tests and lint passed, but review caught:

- `EngineDeadError` swallowed by generic SSE error;
- structured 400 downgraded to 500;
- replacement text named as `delta`, which violated append semantics.

Streaming is public protocol, not helper plumbing.

## PR #4381 LTX-2.3 full diff miss

Known finding closure was mistaken for full diff clean. Misses included:

- helper output rejected by public `check_inputs()`;
- I2V tensor-valued `or` fallback;
- recipe/perf workload mismatch.

Full diff review needs diff census, semantic trace, garbage pass, and reviewer-lens audits.
