# vllm-omni judge calibration set

`infermatrix-copilot kb calibrate --repo vllm-omni` runs the pinned judge over
these cases exactly as the knowledge gate does. The repository may leave
shadow mode only when every `reject` case is caught and at most 20 % of the
`pass` cases are rejected; re-run it whenever the judge model or version
changes.

- `good-*`: the eight human-approved rules of InferMatrixCopilot #202, each
  replayed as an `add` against its page as it was before the merge.
- `bad-*`: mutations the gate must reject (reversed claim, optional enforcement,
  restated PR description, contradiction of BENCH-1a, unjustified retirement,
  an edit that changes meaning, an invented API) and the historical bot-written
  MMH3-4e that contradicted MMH3-4a (folded by a human in 03b0b62a2).

Evidence is the real upstream PR (title, body, bounded diff excerpt).
