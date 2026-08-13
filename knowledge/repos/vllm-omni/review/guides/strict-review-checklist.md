---
title: "Strict 审查触发式检查单"
created: 2026-08-12
updated: 2026-08-12
type: guide
tags: [vllm-omni, review]
sources: []
---

# Strict 审查触发式检查单

Distilled from maintainer review patterns on merged PRs (train split of the
20-PR review campaign). Each line is a check to RUN when its trigger matches,
not background reading. The Strict reviewer injects the first 4,000 chars of
this page as its repo-specific checklist (`knowledge.review_checklist` in the
adapter manifest); keep the actionable core inside that budget.

## Streaming / TTS serving (serving_speech, stream sessions)

- `async_chunk` defaults to **False** (`OmniModelConfig`). Any gate or
  coercion keyed on it applies to EVERY async_chunk=false model (moss_tts,
  voxcpm2, higgs_audio, indextts2, qwen2_5_omni, ...), not just the model
  named in the PR title — demand scoping or cross-model evidence.
- Stream slots/sessions: acquisition must have a release on client
  **abort/disconnect**, not only on `finished=True`. Check the unscheduled/
  abort reap path releases too; leaked slots starve the pool silently.
- Cumulative vs delta chunk semantics: flipping re-emits the accumulated
  waveform (audible rewind). Removing a guard/warning around this without a
  replacement is itself a finding.
- Per-request seeding (`tts_local_seed` etc.): verify determinism survives
  CUDA-graph replay — replayed graphs discard per-request state; "seeded" in
  eager mode proves nothing about graph mode.

## Model executor / checkpoints

- Legacy vs v2 codec/tokenizer selection: legacy checkpoints can share
  `model_type` with v2 — selection must be gated by an explicit config
  marker, never try-instantiate-and-fallback (misload = wrong decode layout).
- Never mutate shared config objects (`hf_config`/`model_config` fields) at
  load/init: later readers (weight loading, cache sizing) see the mutated
  value. Copy, don't overwrite.
- Vendored model files carry a "Vendored from <upstream> @ <ref>" header
  (see `audio_tokenizer.py`); new vendored files without one are a finding.

## Platforms / kernels / global defaults

- Anything under `vllm_omni/platforms/` or in a `get_default_*` path is
  inherited by EVERY model on that platform. Validated-on-one-model changes
  need per-model scoping (registry override, e.g. `ir_op_priority_func`) or
  A/B evidence on the other affected families.
- Kernel-provider/priority switches: require before/after latency AND
  same-seed accuracy vs main, measured PER bundled change — a combined
  number cannot attribute the win.
- Hardware gates must match the claimed support matrix: `major >= 9` admits
  future arches the claim never covered; and check what CI actually runs —
  an L4 lane (sm_89) never executes an SM90-gated path, so its green is not
  coverage.

## Dependencies

- New kwarg/API into an optional third-party package (`kernels`, HF hub):
  read the declared range in `pyproject.toml` — does the OLDEST allowed
  version support it? A docs pin (`pkg==X`) is not a lower bound.
- When the commit timeline shows a described kwarg/API was later DROPPED,
  state the compatibility reason explicitly (old versions inside the
  declared range reject unknown kwargs, so every call would fail) — the
  description-vs-diff mismatch is the fix working, not an omission.

## CI / tests

- Tests are selected by pytest **markers** (`-m "core_model and cpu"` style
  expressions in `.buildkite/`), not by path: a new test file without
  `pytestmark` is silently deselected — CI green while never running it.
- A test that cannot fail is worse than none: try/except-and-continue around
  the assert, degenerate inputs (`k = q.clone()`), or asserting the value
  the fake injected. Flag these as test-integrity findings.
- L2 covers CPU/mock plumbing only; real weights, precision, and perf are
  L4. `0 missing / 0 unexpected` + shape smoke ≠ semantic correctness.

## Process norms maintainers enforce

- A PR fixing one of N problems reported in a linked issue: one comment must
  note what remains unfixed and ask for tracking or a split PR.
- An unexplained capacity/threshold/config retune riding along in a PR gets
  a benchmark-rationale ask — that is a review finding, not a process nit.
- Red CI on the PR head: name the failing check and ask for resolution.
