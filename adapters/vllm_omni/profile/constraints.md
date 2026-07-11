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

## Multi-stage engine & deployment (Tier-2 detail; 2026-07-12)
Sources: vllm-omni code (paths verified live) + community workflow spec
`zuiho-kai/claude-workflow-starter` `repos/vllm-omni/` (each claim re-verified
in-repo before inclusion) + eval train/val ground truth.

- **Stage config merge chain**: effective per-stage config = global CLI args →
  per-stage overrides → deploy YAML (`vllm_omni/deploy/*.yaml`: `pipeline:`,
  per-stage `devices`, parallelism, `engine_extras`) → platform overlay.
  Reviewing any of these means expanding the FINAL merged config, then checking
  per-stage `TP·PP·DP ≤ resolved visible devices` **before worker creation**
  (`vllm_omni/engine/stage_init_utils.py::setup_stage_devices`,
  `stage_engine_startup.py`). Truncating device lists or continuing on
  capacity mismatch is a defect (issue #5003: YAML `devices: "0"` +
  `--tensor-parallel-size 4` → "DP adjusted local rank 1 out of bounds").
- **Runner→model preprocess contract**: `vllm_omni/worker/gpu_model_runner.py::
  _preprocess` produces per-request `_omni_prompt_len`,
  `_omni_num_computed_tokens`, `_omni_is_prefill`; consumers include
  qwen3_omni / qwen3_tts talker / voxtral_tts. Phase decisions must derive from
  real scheduling state (prompt progress), never current-span length.
  Regression home: `tests/worker/` calling the production `_preprocess` with a
  mixed batch (one request that should and one that should not enter the
  route). Testing only model helpers with hand-fed metadata proves nothing
  about the runner contract.
- **Checkpoint layout gate** (before docs/recipes/examples list a model id):
  the pipeline loader's required layout must exist — `model_index.json`,
  subfolder configs (`transformer/`, `vae/`, `scheduler/`, `tokenizer/`,
  `text_encoder/`), single-file-safetensors support. Official vs
  community-Diffusers repos differ (issue #4827 = Base-vs-Instruct layout
  crash). Docs may only list checkpoints the CURRENT loader loads directly.
- **Run levels**: `--run-level` defaults to `core_model` → dummy weights, even
  for online serving (PR #4354 extended it); `full_model` is required for
  behavior/output tests (issue #4842, closed INVALID over exactly this).
- **CI tiers**: leveled Buildkite pipelines — CPU/mock tiers (L2-style) must
  not initialize real stages/devices; real weights/precision/perf sit in
  higher tiers (L3/L4-style; cf. issue #5014 "L3 CI failure"). A PR whose only
  evidence is a CPU/mock tier cannot claim GPU semantics.
- **What a model-adaptation PR should declare** (mini-spec, community-derived):
  goal; checkpoint layout (runnable id, raw id, required files); public
  entrypoints per modality (offline/serving); request fields (ingress, default
  semantics, owner, consumers, failure policy); path parity (normal vs variant
  paths, shared helper or intentional split); validation tier per claim
  (unit / public smoke / formal perf); PR evidence freshness (latest-head vs
  historical); non-goals.
