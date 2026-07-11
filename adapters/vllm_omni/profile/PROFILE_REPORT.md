# Profile report

Per-fact provenance: how derived, evidence, confirmations.

## audio-similarity-trap [active]
- module: audio · kind: trap · channel: briefing · source: agent
- text: Audio/TTS similarity below the 0.9 gate is often a whisper-small ASR mishearing a short/quiet clip, not a model regression — re-check with whisper-large-v3 before flagging (large-v3 scored 200/200 where small failed).
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: verified rebase observation 2026-06 (Higgs-Audio-V3 'Shhh!' clip: whisper-large-v3 200/200 clean)

## benchmarks-wave2 [active]
- module: benchmarks · kind: note · channel: retrieved · source: agent
- text: benchmarks/ is rebase wave 2 (lower priority than the wave-1 runtime modules); its scripts validate throughput/latency, not output correctness.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: adapters/vllm_omni/manifest.yaml modules.benchmarks.wave=2

## build-and-lint [active]
- module: repo-wide · kind: command · channel: machine · source: agent
- text: Python 3.10–3.13; build via setuptools (dynamic version + platform deps); lint/format via ruff + pre-commit.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/pyproject.toml requires-python='>=3.10,<3.14', build-backend=setuptools
  - evidence: adapters/vllm_omni/manifest.yaml validation.precommit=true

## ci-entry [active]
- module: repo-wide · kind: command · channel: machine · source: agent
- text: CI image: `docker build --file docker/Dockerfile.ci -t vllm-omni-ci .`; pipeline entry `.buildkite/scripts/upload_pipeline.py` uploads the test-ready / test-merge / test-nightly / test-weekly child pipelines.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/.buildkite/pipeline.yml

## ci-signature-normalize [active]
- module: repo-wide · kind: trap · channel: retrieved · source: agent
- text: When grouping CI failures, normalize signatures — the same underlying failure recurs across runs with slightly different text; exact-string comparison misclassifies a known/flaky failure as new.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: rebase-agent debug lesson: CI baseline exact-string signature bug in monitor.py

## ci-skip-not-fail [active]
- module: repo-wide · kind: note · channel: briefing · source: agent
- text: CI is Buildkite (org vllm). A PR's tests can be legitimately skipped by the skip-ci resolver (docs-only or pytest skip-mark diffs) — a skipped run is NOT a failing run; image-build still runs for the nightly exception.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/.buildkite/pipeline.yml (upload_pipeline.py skip-ci resolution)

## collected-zero-is-path [active]
- module: repo-wide · kind: trap · channel: briefing · source: agent
- text: pytest 'collected 0 items' (rc=4) means a stale/renamed test path, not OOM — after a test-file rename, verify the CI test command still points at real files.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: rebase run: config.sh CI_TEST_CMD referenced pre-rename *_expansion.py/*_tts.py paths

## delivery-pr [active]
- module: repo-wide · kind: constraint · channel: briefing · source: agent
- text: Deliver every change as a PR to a working branch (e.g. dev/vllm-align); `main` is protected and must never be direct-pushed.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: adapters/vllm_omni/manifest.yaml push.allowed=false / protected_branches=[main]
  - evidence: owner policy: deliver via PR, not direct commit

## diffusion-nonar [active]
- module: diffusion · kind: note · channel: retrieved · source: agent
- text: vLLM-Omni adds a non-autoregressive path (Diffusion Transformers / DiT) alongside vLLM's autoregressive path; image/video generation and parts of the audio stack run through vllm_omni/diffusion/.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/README.md (non-autoregressive DiT architectures)
  - evidence: vllm-omni/vllm_omni/diffusion/

## dockerfile-ci-pins [active]
- module: platform · kind: trap · channel: briefing · source: agent
- text: docker/Dockerfile.ci env pins are fragile across rebases — recurring breakers: numpy must stay <2.5 (numba incompatibility), a missing libnvJitLink.so.13, and transformers AutoProcessor.register API drift.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: rebase CI build 2520 align-branch failures, 2026-07

## image-ssim-sensitive [active]
- module: image · kind: trap · channel: retrieved · source: agent
- text: Image-generation tests compare outputs with SSIM thresholds sensitive to nondeterminism — HunyuanImage SSIM has flaked; confirm a real regression (reproduce, compare against baseline) before flagging a threshold miss.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: rebase CI build 2520 align-branch failures, 2026-07

## model_executor-convention-checkpoint-layout [active]
- module: model_executor · kind: convention · channel: retrieved · source: agent
- text: Before a model id is written into docs/recipes/examples/perf configs, verify the checkpoint layout the pipeline loader needs (model_index.json, transformer/vae/scheduler/tokenizer subfolder configs, single-file safetensors support) — official and community-Diffusers repos differ; docs may only list checkpoints the CURRENT loader loads directly.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: github:vllm-omni issue#4827 (Base vs Instruct checkpoint layout crash)
  - evidence: community:zuiho-kai/claude-workflow-starter review/guides/model-adaptation-guardrails.md

## model_executor-trap-omni-phase-metadata [active]
- module: model_executor · kind: trap · channel: briefing · source: agent
- text: Worker runner _preprocess emits per-request _omni_prompt_len/_omni_num_computed_tokens/_omni_is_prefill consumed by model talkers — review producer and consumers together.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: vllm_omni/worker/gpu_model_runner.py (producer)
  - evidence: vllm_omni/model_executor/models/qwen3_tts/qwen3_tts_talker.py (consumer)
  - evidence: community:zuiho-kai/claude-workflow-starter repos/vllm-omni/rules.md (verified in-repo 2026-07-12)

## multi-platform [active]
- module: repo-wide · kind: constraint · channel: briefing · source: agent
- text: Don't assume CUDA: the repo targets CUDA/ROCm/NPU/XPU. Platform code is per-backend and dependencies are platform-specific (requirements/), not installed via a [cuda] extra.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/pyproject.toml (dynamic platform deps, no [cuda] extra)
  - evidence: vllm-omni/docker/Dockerfile.{cuda,rocm,npu,xpu}

## omni-fork [active]
- module: repo-wide · kind: note · channel: briefing · source: agent
- text: vLLM-Omni is a fork of upstream vLLM extending it to omni-modality (text/image/video/audio) serving; releases align to an upstream vLLM version and rebasing onto upstream is the core maintenance activity.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/README.md 'About' + release notes (0.16 rebased onto vLLM 0.16, 0.22 aligned to vLLM 0.22)
  - evidence: adapters/vllm_omni/manifest.yaml upstream.kind=fork_tracking

## online_serving-trap-run-level-dummy-weights [active]
- module: online_serving · kind: trap · channel: briefing · source: agent
- text: --run-level defaults to core_model = DUMMY weights even in online serving; garbage output on a manual server is run-level misconfig — use --run-level=full_model for behavior tests.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: github:vllm-omni issue#4842 (closed INVALID: core_model default -> dummy weights; PR#4354 extended run-level to online serving)

## rebase-hotspots [active]
- module: repo-wide · kind: trap · channel: briefing · source: agent
- text: Highest rebase-damage risk is worker_runner, model_executor and scheduler (vllm_omni/core/) — they track upstream vLLM internals closely; after a rebase check for dropped/duplicated hunks and references to moved/renamed symbols.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: adapters/vllm_omni/manifest.yaml modules with risk: high

## repo-wide-constraint-upstream-checkout [active]
- module: repo-wide · kind: constraint · channel: briefing · source: agent
- text: Aligned upstream vLLM checkout: /rebase/vllm — read it to verify any upstream claim (cite file:line); never cite an unread PR/version/line.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: eval judgments/val 2026-07: baseline wins on pr4810/pr4893 rest on /rebase/vllm reads; copilot fabricated PR #43167/vllm#46022 cites
  - evidence: CLAUDE.md: /rebase/vllm is the upstream checkout used as rebase target

## repo-wide-convention-design-suggestions [active]
- module: repo-wide · kind: convention · channel: briefing · source: agent
- text: Surface the best design suggestion found during review even on approvable PRs (single-source-of-truth asks) — never silently drop it; empty review of a nontrivial diff = missed value.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: github:vllm-omni#4825 inline (dsocek: derive LoRA components from _packed_modules_mapping)
  - evidence: eval train GT 2026-07: #4810->issue#4891, #4870->#4910 follow-ups

## repo-wide-convention-plumbing-vs-parity [active]
- module: repo-wide · kind: convention · channel: briefing · source: agent
- text: Weight-load 0-missing/0-unexpected, shape smoke, no-NaN and CPU/mock CI prove plumbing only — model claims need HF semantic parity with a real checkpoint; perf claims need a locked config + scope label.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: .buildkite/ leveled pipelines (L2 CPU/mock vs higher GPU tiers; cf issue#5014 'L3 CI failure')
  - evidence: community:zuiho-kai/claude-workflow-starter repos/vllm-omni/rules.md (verified in-repo 2026-07-12)

## scheduler-is-core [active]
- module: scheduler · kind: note · channel: retrieved · source: agent
- text: The 'scheduler' module maps to vllm_omni/core/ (per the manifest module map) — not a top-level scheduler/ directory.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: adapters/vllm_omni/manifest.yaml modules.scheduler.local_paths=[vllm_omni/core/]

## torch-accelerator [active]
- module: repo-wide · kind: convention · channel: briefing · source: agent
- text: Never call `torch.cuda.*` — ruff bans it; use the `torch.accelerator.*` equivalents (device_count, current_device_index, empty_cache, synchronize, max_memory_allocated, reset_peak_memory_stats).
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: vllm-omni/pyproject.toml [tool.ruff] banned-api rules for torch.cuda.*

## transformers-drift [active]
- module: model_executor · kind: trap · channel: retrieved · source: agent
- text: transformers version drift breaks model loading across rebases (e.g. AutoProcessor.register signature changes) — pin and verify transformers when a rebase bumps it.
- confirmations: 1 (first 2026-07-11, last 2026-07-11)
  - evidence: rebase CI build 2520 (transformers AutoProcessor.register regression), 2026-07

## worker-trap-removed-api-sweep [active]
- module: worker_runner · kind: trap · channel: briefing · source: agent
- text: A PR adapting callers of a removed/renamed upstream API needs a repo-wide grep proving no caller remains (diffusion/, vendored, gpu_/npu_ included).
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: github:vllm-omni#4810 'missed by' -> issue#4891 (HunyuanImage3 diffusion loader)

## worker-trap-stage-capacity [active]
- module: worker_runner · kind: trap · channel: retrieved · source: agent
- text: Stage topology bugs: validate per-stage parallel world size (TP*PP*DP) against the stage's resolved visible devices BEFORE worker creation; config merges CLI -> per-stage override -> deploy YAML -> platform overlay (vllm_omni/engine/stage_init_utils.py setup_stage_devices). deploy YAML devices:'0' with --tensor-parallel-size 4 crashes with 'DP adjusted local rank out of bounds'.
- confirmations: 1 (first 2026-07-12, last 2026-07-12)
  - evidence: vllm_omni/engine/stage_init_utils.py + stage_engine_startup.py (verified 2026-07-12)
  - evidence: github:vllm-omni issue#5003
  - evidence: community:zuiho-kai/claude-workflow-starter components/model-executor/rules.md (verified in-repo)
