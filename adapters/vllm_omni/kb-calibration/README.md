# vllm-omni judge calibration set

`infermatrix-copilot kb calibrate --repo vllm-omni` runs the pinned judge over
these cases exactly as the knowledge gate does. The repository may leave
shadow mode only when every `reject` case is caught and at most 20 % of the
`pass` cases are rejected; re-run it whenever the judge model or version
changes.

- `good-*`: the eight human-approved rules of InferMatrixCopilot #202, replayed
  against their pages before the merge. DIFF-2ag4 explicitly replaces its
  zero-binding predecessor DIFF-2ag2, retaining the old text as retired and
  preserving its guards in the stronger successor; the other cases add a rule.
- `bad-*`: mutations the gate must reject (reversed claim, optional enforcement,
  restated PR description, contradiction of BENCH-1a, unjustified retirement,
  an edit that changes meaning, an invented API) and the historical bot-written
  MMH3-4e that contradicted MMH3-4a (folded by a human in 03b0b62a2).

Evidence is the real upstream PR, pinned by merge commit: complete title/body
and per-file diff, plus exact source-line context where a rule depends on
unchanged behaviour (runner schema filtering, prefix-cache source planning,
speech exception handling). Positive and negative mutations of the same PR
receive identical evidence. The historical MMH3 case retains its original
evidence. None of the expected labels or scoring thresholds changed.

The 2026-10-09 source audit also corrects two assertions in the good fixtures
and canonical owner rules: SCHED-1c names `OmniPrefixCacheManager`, and SERV-9d
preserves engine-exception propagation instead of claiming all engine errors
are HTTP 400. Its `ValueError` 400 and generic internal-error 500 expectations
remain intact.

Recorded rerun reasons also correct BENCH-1h to the actual schema predicate
complement and scope its artifact example to NPU, DIST-1m to exact caller-key
cleanup without an invented pending-key ownership guard, and QOMNI-1i to the
real `async_chunk` symbol with honest existing-test coverage. Negative rule
mutations, labels, source evidence and scoring remain unchanged.
