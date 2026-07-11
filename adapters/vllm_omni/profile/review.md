# vLLM-Omni review checklist (repo-specific extensions)

Apply these on top of the generic review checklist. vLLM-Omni is an omni-modality
(text/image/video/audio) fork of upstream vLLM; most changes either track an
upstream API or touch a modality-specific runtime path.

## Upstream alignment (this is a fork)
- If the change touches a path that mirrors upstream vLLM (worker, model_executor,
  scheduler/core, config, platforms), check it against the aligned upstream
  version — a hand-edit that diverges from upstream makes the next rebase harder.
- Rebase damage: dropped or duplicated hunks, references to symbols the aligned
  upstream renamed/moved. The high-risk modules are `worker_runner`,
  `model_executor`, `scheduler` (= `vllm_omni/core/`).

## Portability (never assume CUDA)
- `torch.cuda.*` is banned by ruff — flag any new `torch.cuda.*` call and ask for
  the `torch.accelerator.*` equivalent.
- A change in a runtime/platform path should be portable across CUDA/ROCm/NPU/XPU
  or explicitly guarded per backend; name the platforms the change was (not) tested on.

## Modality-specific correctness
- **Audio/TTS**: a similarity score just below the 0.9 gate is frequently a
  whisper-small ASR mishearing a short/quiet clip, not a model regression. Don't
  flag it as a defect unless it reproduces with whisper-large-v3.
- **Image/diffusion (DiT)**: SSIM-threshold comparisons are sensitive to
  nondeterminism (HunyuanImage has flaked). Distinguish a genuine quality
  regression from a threshold miss; ask for a reproduce + baseline compare.
- **AR vs non-AR**: vLLM-Omni runs both the autoregressive path and the
  Diffusion-Transformer path — a change to shared code (inputs/outputs, sampling,
  scheduling) must be checked against BOTH.

## CI & environment
- `docker/Dockerfile.ci` env pins are fragile: watch numpy (must stay `<2.5` for
  numba), `libnvJitLink.so.13`, and `transformers` API drift
  (`AutoProcessor.register`). A dependency bump in a rebase deserves a hard look.
- A "skipped" Buildkite run (docs-only / pytest skip-mark diff) is not a failing
  run. `pytest ... collected 0 items` (rc=4) is a stale test path, not OOM.

## Tests & verification
- A modality behavior change must name the specific test or benchmark that
  exercises the changed path and show it was run (on H200 for GPU paths).
- Behavior changed with no test change, or a loosened similarity/SSIM threshold
  with no stated justification, is a finding.
