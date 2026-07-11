# vLLM-Omni review checklist (repo-specific extensions)

## Upstream verification (this is a fork)
- The aligned upstream checkout is at **`/rebase/vllm`**. Any claim about
  upstream vLLM behavior MUST be verified by reading it — cite file:line. Never
  cite an upstream PR number, version, or line you did not open this session;
  a PR description is a claim to check, not evidence.
- Rebase damage: dropped/duplicated hunks, references to symbols upstream
  renamed/moved. High-risk: `worker_runner`, `model_executor`, `scheduler`
  (`vllm_omni/core/`).

## Sweeps (mandatory when the diff adapts away from an API)
- Removed/renamed/re-signatured API: grep the WHOLE repo for remaining callers —
  incl. `vllm_omni/diffusion/`, vendored code, `gpu_*`/`npu_*` counterparts.
  Account for every hit (updated here / intentionally untouched — say why).
  Unexplained survivor = finding (#4810 shipped "missed by" follow-up #4891).
  Callers come from grep output, never memory; record command + hit count.
- **Checkout-drift discipline**: you review on current main, which may already
  contain post-PR fixes — a zero-survivor grep does NOT clear the PR-time state.
  Check `git log --oneline -- <file>` for commits after the PR. If the PR body
  names a file the diff doesn't touch, that is a candidate unswept caller —
  never explain it away as "an earlier iteration".
- Variant sweep: each confirmed defect is an exemplar — grep for structural
  siblings (same API, copy-pasted blocks, the paired AR/DiT or GPU/NPU file).

## Review like this repo's maintainers
- Surface the best design suggestion found during investigation, even on an
  approvable PR (suggestion/nit severity) — maintainers add single-source-of-
  truth asks to clean PRs (#4825: derive LoRA components from
  `_packed_modules_mapping` instead of another hardcoded tuple). "Duplication
  exists but extraction isn't justified in this PR" is a comment, not a
  discard — when a diff extends a hardcoded per-model list/tuple duplicating
  declared metadata (`_dit_modules`, registry tables), name the source to
  derive from.
- New guard/assert/NotImplementedError changes behavior for every caller — ask
  which existing tests/CI exercise the guarded path (#4834 broke merge CI →
  #4905/#4912).
- **Severity semantics**: a comment whose substance is "this fix is correct" is
  not a review comment — fold it into the summary. Severity minor+ ONLY when
  this PR must change; misfiled majors flip approvable PRs to REQUEST_CHANGES.
- Two-pass: ENUMERATE 5–10 one-line candidates without self-censoring, then
  prune to those inducing a concrete change. <3 candidates on a >200-line
  diff → one more enumeration pass.
- Comment contract: `file:line` + offending code + concrete consequence +
  specific requested change; <10-line fixes include replacement code. Drop
  comments that fit any PR. Grep every identifier you name — zero hits =
  fabricated: fix or drop. Re-open cited lines before emitting; state the
  trigger precondition or downgrade to a question.

## Modality correctness
- DiT: SSIM thresholds flake (HunyuanImage) — regression vs threshold-miss
  needs a reproduce + baseline compare.
- Shared code (inputs/outputs, sampling, scheduling) must be checked against
  BOTH the AR path and the DiT path.

## Evidence tiers
- Plumbing ≠ parity: 0-missing/0-unexpected weight load, shape smoke, no-NaN,
  mock weights prove plumbing only; new/ported models need semantic parity vs
  the HF reference (real checkpoint). CPU/mock CI tiers (L2) can't initialize
  real stages/devices; GPU semantics live in higher tiers.
- Perf claims need a scope label (strict apples-to-apples / workload-aligned /
  smoke-only) + locked config (commit, snapshot, steps/seed/guidance,
  eager-vs-graph, GPU). Anomalous numbers: audit config→runner→dataset→request→
  payload→server log before touching a baseline; loosening a baseline or
  threshold without justification is a finding.
