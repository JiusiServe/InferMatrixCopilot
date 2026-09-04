---
title: "vLLM-Omni CI"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, ci]
sources: [.buildkite/cuda/pipeline.yml, docs/contributing/ci/test_system_overview.md, tests/diffusion/quantization/test_svdquant_config.py, tests/diffusion/quantization/test_svdquant_linear.py, tests/diffusion/quantization/test_svdquant_tp_loading.py, tests/diffusion/quantization/test_wan_autoround_mxfp4.py, tests/e2e/offline_inference/test_wan21_autoround_mxfp4.py, "PR #5544", "PR #6162", "PR #6170", "PR #6303", "PR #6390", "PR #6613", .buildkite/cuda/test-nightly.yml, tests/e2e/online_serving/run_minicpmo_realtime_duplex_server_vad.py, tests/e2e/online_serving/test_minicpmo_4_5_duplex_expansion.py, tests/e2e/online_serving/test_qwen_image_expansion.py, tests/dfx/perf/tests/test_qwen_image_vllm_omni.json, tests/platforms/npu/test_diffusion_attn_backend_selector.py, "PR #6054", .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, tests/e2e/online_serving/test_hunyuan_video_15_expansion.py, tests/dfx/perf/tests/test_hunyuanvideo15_t2v_vllm_omni.json, tests/dfx/perf/tests/test_hunyuanvideo15_i2v_vllm_omni.json, "PR #6349", .buildkite/amd/scripts/bootstrap-amd-omni.sh, .buildkite/amd/test-amd-merge.yml, .buildkite/amd/test-amd-ready.yml, tests/diffusion/distributed/test_tensor_parallel.py, tests/diffusion/offloader/test_diffusion_layerwise_offload.py, tests/helpers/clean.py, "PR #6704", "PR #5464", "PR #6730", "PR #6727"]
---

# vLLM-Omni CI

## 什么时候查这里

- 处理 vLLM-Omni 的 L2/L4、模型测试配置或 CI 特有问题。

## Historical MiniCPM-o 4.5 unit-test revert

- PR #6730 reverted the two PR #5464 CPU assertions after CI failure. They are not current
  coverage and do not evidence a runtime, offline-inference, online-serving, or transport
  implementation change. Reintroduce comparable coverage only with a passing CI-backed change.
  ^[PR #5464] ^[PR #6730]

## MiniCPM native-duplex server-VAD coverage

- Ready/merge 的 MiniCPM duplex source dependencies 纳入 server-VAD runner；其 L4 full-model
  acceptance 验证 one hard-cancel terminal、无旧 epoch delta、speech edges、interrupt PCM/pre-roll
  与 follow-up response。它是 protocol/lifecycle coverage，不能单凭 runner 或历史 H200 结果声称
  常规 listen-only 性能提升。 ^[PR #6170]

## MiniCPM Realtime video-frame unit coverage

- PR #6404 adds CPU/unit coverage for closing-append frame placement, held last/still frames, two-frame stacking, Stage 0 marker/embedding ordering, rejected early video appends, dtype conversion, and external WAV video demos. It is protocol and input-assembly coverage; its unchecked full-model video E2E and manual demo do not establish an end-to-end checkpoint pass or video quality result. ^[PR #6404]

## FLUX.2 configurable encoder-layer test boundary

- `tests/model_tests/diffusion/diff_model_builders.py::tiny_flux2_builder` makes the fixture
  economical by reducing the text encoder to three layers and selecting `[0, 1, 2]`; its
  transformer `joint_attention_dim=96` matches the concatenated selected hidden outputs.
  The focused offline `Flux2Pipeline` run covers text-to-image, determinism, and multi-output.
  It does not execute a full-size legacy checkpoint without `text_encoder_out_layers`, so it is
  not evidence that the `(10, 20, 30)` fallback completed a full-model validation. ^[PR #6390]

## 不放什么

- 跨仓库通用的测试方法。

## Invalid-request error expectation

- 对 Qwen3-Omni 的 incomplete `response_format={"type": "json_schema"}`，DFX
  invalid-request test 应断言 400 公共 API error envelope 中的
  `BadRequestError`、`param="response_format"` 和 `json_schema` 缺失提示；不要把
  vLLM 内部 validator 的 Pydantic `value_error` token 当成该接口合同。该断言曾因
  上游错误映射改为 `BadRequestError` 而导致 weekly CI 失败。^[PR #6290 / issue #6248]

## AutoRound MXFP4 coverage boundary

- Wan AutoRound MXFP4 has a CPU-marked configuration/layer-mapping test and a full-model
  diffusion E2E test gated to XPU B60. The latter uses an environment-overridable model ID,
  runs a minimal 256×256 five-frame, one-step request, and checks response success, frame
  shape, and nonzero variance. It is an offline inference smoke, not online-serving, FLUX,
  CUDA, or general backend coverage. ^[PR #5544]

## SVDQuant W4A4 coverage boundary

- The SVDQuant suite is CPU-marked and uses mocked NVFP4 kernels to check configuration,
  tensor conversion, the BF16 correction calculation, and Column/Row/QKV TP loading. It does
  not run a compatible real kernel, load a released checkpoint, or establish SM103 execution,
  output quality, latency, or VRAM results. Any GPU support or performance claim requires a
  separately recorded exact-device E2E run. ^[PR #6162]

## Diffusion GGUF nightly plugin compatibility

- The L4 full-model diffusion-quantization nightly lane installs
  `vllm-gguf-plugin==0.0.4`, rather than the floating `>=0.0.3`: the later resolved
  0.0.5 imports `huggingface_hub.ResolvedRevision`, which the lane's existing
  `huggingface_hub` does not export, so plugin loading and `gguf` registration fail
  before the tests run. This is a temporary CI-environment reproducibility pin, not a
  runtime support or package-dependency claim. Remove it only after a plugin release
  is compatible with that environment or declares the required minimum hub version.
- The scoped command is `pytest -sv tests/diffusion/quantization -m 'full_model and
  cuda and L4' --run-level full_model`; its two GGUF cases cover Z-Image-Turbo and
  FLUX.2-klein. PR evidence reports local loading/registration recovery, while the
  L4 full-model run was deferred to Buildkite, so do not record a full test pass from
  this change alone. ^[PR #6303 / issue #6022]

## NPU diffusion-attention selector regression boundary

- `tests/platforms/npu/test_diffusion_attn_backend_selector.py` is CPU-marked and loads the
  NPU platform module with fake vLLM/vLLM-Ascend dependencies. It isolates eager `mindiesd`
  import selection for FLASH, hub FLASH fallbacks, RAINFUSION, and SDPA plus missing-package
  fallback behavior. It is selector regression coverage only: it neither requires an NPU or
  MindIE-SD install nor establishes CANN registration or real Ascend-kernel execution. ^[PR #6054]

## Qwen-Image nightly coverage and step-execution perf sharing

- The Qwen-Image online-serving expansion keeps nine feature pytest IDs, but assigns one
  checkpoint to each case: Qwen-Image covers CPU offload, TeaCache, Ulysses degree 2,
  CFG parallel size 2, and HSDP shard size 2; Qwen-Image-2512 covers step execution,
  layerwise offload, Ring degree 2, and VAE patch parallel size 2. Single-card versus
  two-card H100 marks remain attached to those cases. This is a nightly coverage matrix,
  not evidence that either checkpoint is interchangeable for runtime behavior or numeric
  output.
- The Qwen-Image step-execution perf config uses one H100 server with profiler,
  `step-execution`, and `max-num-seqs: 8` for sequential 512x512/20-step and
  1536x1536/35-step cases plus the 512x512/20-step concurrency 1/2/4/8 sweep. Keep the
  three `benchmark_params` under that shared server and retain their existing H100 baseline
  artifacts; the JSON change itself does not establish a performance result or an active
  regression threshold. ^[PR #6613]

## HunyuanVideo-1.5 ready/merge and nightly coverage

- The basic one-H100 CPU-offload T2V online-serving row is marked `core_model` and
  `advanced_model`, and the ready and merge Buildkite jobs select it with the matching
  run level. The CacheDiT + layerwise CPU-offload one-card row and CacheDiT + TP=2 +
  VAE patch-parallel=2 (with VAE tiling) two-card row are `full_model` only, so their
  function coverage remains in the nightly H100×2 lane. This is deliberately a
  scope split, not evidence that the richer combinations run in ready/merge. ^[PR #6349]
- The dedicated nightly DFX job runs separate T2V and I2V JSON configs: random data,
  ten prompts at concurrency one, seed 42, negative prompt, and 832×480 / 33-frame /
  four-step / 24-fps requests. Each has a one-H100 baseline and a two-H100
  CacheDiT/TP2/VAE-patch-parallel=2/tiling case. It uploads result JSON and logs but
  configures no threshold, so it is benchmark-report/artifact collection rather than
  a performance regression gate. ^[PR #6349]

## XPU base-image resolution and support-table boundary

- The Intel Buildkite XPU lane targets vLLM `v0.28.0`. Its Omni image layers on
  `vllm/vllm-openai-xpu:${VLLM_VERSION}` and clears that image's serving entrypoint so the
  result remains a shell/test container. The base carries the matching XPU runtime and vLLM;
  Omni installs only its own layers. Keep the Dockerfile default and lane environment version
  aligned.
- Before building, CI pulls the published upstream base freshly. If that pull fails it may use
  an existing local copy; only if neither exists does it build the same vLLM tag from upstream
  `docker/Dockerfile.xpu`, optionally under `VLLM_BASE`. Thus a fallback is provenance-aligned,
  but it is not evidence that an arbitrary pre-existing fallback image matches the published
  tag. The in-container scope remains the B60-marked core/advanced/omni pytest selections plus
  `test_mxfp8_config.py`; it is not a whole-suite or model-matrix validation. The PR author
  reported CI passing but supplied no command output or completed test plan, and review had no
  surviving findings, so retain those evidence limits. ^[PR #6727]

## AMD CI stabilization boundary

- AMD merge lanes may combine READY and MERGE definitions only through the bootstrap's
  explicit `DEBUG_TEST_YAML=merge,ready` override; the merged YAML shares one build step
  and preserves each suite as a named group. This is a maintainer debugging control, not
  a change to the normal branch-based READY-versus-MERGE selection.
- Long MI300 diffusion shards carry explicit Buildkite timeouts, while a known long-running
  Qwen3-TTS CustomVoice `async_chunk` Whisper-validation case is an 80-minute,
  `NonBlocking` quarantined step. It must return to the blocking sharded lane only after
  the AMD failure is resolved; a passing neighboring shard does not establish that result.
- ROCm memory assertions sample steady-state inference and report peak usage relative to
  each run's initial device use, after cache cleanup. They therefore do not count retained
  compiler/workspace allocations from a preceding topology as model memory, and the ROCm
  layerwise-offload floor remains a conservative 512 MiB signal rather than a portability
  or performance claim. Cleanup diagnostics use bounded `rocm-smi` calls because an
  optional `amd-smi` CPER ioctl can remain uninterruptibly blocked. ^[PR #6704]

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 审查硬件 lane（含 MiniMax-H3 DLO DP2 ready smoke 的证据边界）、回归 fence、CI 工具供应链或 xdist/shared fixture | [CI rules](rules.md) |
| 查看仓库特有 CI 陷阱 | [CI guides](guides/_index.md) |
| 调查历史 CI 失败 | [CI incidents](incidents/_index.md) |
