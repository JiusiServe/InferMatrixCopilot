# vLLM-Omni constraints (adapter Tier-2 knowledge)

Repo-wide review / merge / safety norms. The machine-enforced ones (protected
branches, push policy) are authoritative in `../manifest.yaml`; this file is the
human-readable expansion the review and push guards can cite.

## Delivery & branches
- `main` is protected — **never direct-push**. Deliver every change as a PR to a
  working branch (rebase work uses `dev/vllm-align`).
  *(manifest: `push.allowed=false`, `protected_branches=[main]`)*
- The repo tracks upstream vLLM (fork). Prefer changes that stay diff-able
  against upstream; a divergent hand-edit to an upstream-mirrored path (worker,
  model_executor, core/scheduler, config, platforms) raises the cost of the next
  rebase.

## Commit & PR requirements
- **DCO sign-off is required** — every commit must carry `Signed-off-by:`
  (enforced by the local `signoff-commit` pre-commit hook).
  *(.pre-commit-config.yaml)*
- pre-commit must pass before merge: `ruff-check`, `ruff-format`, `typos`,
  `actionlint`, `check-yaml`, end-of-file / whitespace fixers,
  `check-pickle-imports`. *(GitHub: `.github/workflows/pre-commit.yml`)*

## Required checks (CI)
- Buildkite runs L2 tests on the PR `ready` label (diff-aware); the
  merge / nightly / weekly pipelines gate `main`. A change to a runtime module
  should show that module's tests ran (H200 for GPU paths). *(see `ci.yaml`)*

## License & security
- **Apache-2.0** licensed. New source files follow the repo's existing header
  convention.
- **pickle is restricted** (`check-pickle-imports` hook) — do not introduce new
  `pickle` / untrusted-`torch.load` usage without justification.
- **`librosa` is banned** — use `vllm.multimodal` helpers. *(ruff banned-api)*

## Never-reformat / keep-upstream paths
Vendored upstream model code keeps upstream conventions so it stays diff-able —
do **not** reformat, "clean up", or lint-fix these:
- `vllm_omni/model_executor/models/minicpmo_4_5/` — star imports, long lines,
  math-symbol argument names. *(pyproject per-file-ignores comment)*

## Portability
- **Don't assume CUDA.** Runtime / platform changes must be portable across
  CUDA / ROCm / NPU / XPU, or explicitly guarded per backend.
  *(docker/Dockerfile.{cuda,rocm,npu,xpu})*

---
*Evidence: vllm-omni `LICENSE` (Apache-2.0), `.pre-commit-config.yaml`,
`pyproject.toml`, `.github/workflows/pre-commit.yml`, `adapters/vllm_omni/manifest.yaml`.*
