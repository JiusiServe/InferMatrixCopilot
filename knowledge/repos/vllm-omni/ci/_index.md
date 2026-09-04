---
title: "vLLM-Omni CI"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, ci]
sources: [.buildkite/cuda/pipeline.yml, docs/contributing/ci/test_system_overview.md, tests/diffusion/quantization/test_svdquant_config.py, tests/diffusion/quantization/test_svdquant_linear.py, tests/diffusion/quantization/test_svdquant_tp_loading.py, tests/diffusion/quantization/test_wan_autoround_mxfp4.py, tests/e2e/offline_inference/test_wan21_autoround_mxfp4.py, "PR #5544", "PR #6162", "PR #6170", "PR #6303", "PR #6390", "PR #6613", .buildkite/cuda/test-nightly.yml, tests/e2e/online_serving/run_minicpmo_realtime_duplex_server_vad.py, tests/e2e/online_serving/test_minicpmo_4_5_duplex_expansion.py, tests/e2e/online_serving/test_qwen_image_expansion.py, tests/dfx/perf/tests/test_qwen_image_vllm_omni.json, tests/platforms/npu/test_diffusion_attn_backend_selector.py, "PR #6054", .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, tests/e2e/online_serving/test_hunyuan_video_15_expansion.py, tests/dfx/perf/tests/test_hunyuanvideo15_t2v_vllm_omni.json, tests/dfx/perf/tests/test_hunyuanvideo15_i2v_vllm_omni.json, "PR #6349", .buildkite/amd/scripts/bootstrap-amd-omni.sh, .buildkite/amd/test-amd-merge.yml, .buildkite/amd/test-amd-ready.yml, tests/diffusion/distributed/test_tensor_parallel.py, tests/diffusion/offloader/test_diffusion_layerwise_offload.py, tests/helpers/clean.py, "PR #6704", tests/model_executor/models/minicpmo_4_5/test_pipeline.py, tests/model_executor/stage_input_processors/test_minicpmo_4_5_async_chunk.py, "PR #5464", "PR #6730", "PR #6745", "PR #6727", tests/diffusion/quantization/test_quantization_quality.py, "PR #5831", tests/dfx/perf/tests/test_qwen3_omni_async_chunk.json, tests/dfx/perf/tests/test_qwen3_omni_no_async_chunk.json, "PR #6743", tests/diffusion/models/minimax_h3/test_minimax_h3_quantization_quality.py, "PR #6742", "PR #6650", pyproject.toml, tests/helpers/mark.py, tests/helpers/tests/test_mark.py, tools/pre_commit/check_test_marks.py, "PR #6174", .buildkite/cuda/test-weekly.yml, tests/e2e/offline_inference/test_dots_tts_expansion.py]
---

# vLLM-Omni CI

## 什么时候查这里

- 处理 vLLM-Omni 的 L2/L4、模型测试配置或 CI 特有问题。
- 处理 `@hardware_test`/`hardware_marks`、SKU 与 `cards_N` 自动 marker 或按卡数切分时，先看
  [测试分级与 markers](guides/test-tiers.md)，再按 OMNI-CI-1a 审核 lane 的真实收集与执行。

## MiniCPM-o 4.5 full-payload regression coverage

- PR #6730 had reverted the two PR #5464 CPU assertions after CI failure. PR #6745 reports
  re-landing them after Buildkite build 14300 passed: with `async_chunk=False`, deployment merge
  selects Talker’s `tts2code2wav_full_payload`; and a terminal `pooling_output=None` full payload returns
  an empty terminal packet (`code_flat_numel=0`, `left_context_size=0`, `last_chunk=True`, and
  `finished=True`) rather than `None`, releasing the downstream consumer wait gate.
- This commit modifies only those two tests. It refreshes regression coverage for existing
  behavior; it does not itself change runtime, offline-inference, online-serving, or transport
  implementation. ^[PR #5464] ^[PR #6730] ^[PR #6745]

## dots.tts weekly L4 collection boundary

- Weekly TTS L4 selects `slow and L4 and tts` with `--run-level full_model`; the three dots.tts
  offline cases carry `slow`, `tts` and one-card L4 hardware markers, so collection returns three.
  The distinct nightly selector `full_model and L4 and tts` returns zero because these cases do not
  carry the `full_model` tier marker. PR #6174 reports collection only and explicitly did not run the
  tests on L4; this records OMNI-CI-1a/1c wiring, not a hardware pass or runtime/model validation.
  ^[PR #6174]

## LTX-2 FP8 quality-gate recipe boundary

- The H100 full-model `fp8_ltx2` gate compares Lightricks/LTX-2 online FP8 with BF16 using
  the supported eager default recipe: 512×384, 73 frames, ten steps, seed 42, recipe-default
  negative conditioning, and no request `sigmas` or `guidance_scale` override. Both arms keep
  `enforce_eager=True`, so the LPIPS ≤ 0.20 threshold isolates quantization rather than compile
  behavior. A CPU capturing test must assert that an absent negative prompt is omitted from the
  request and that the sampling overrides remain `None`; the skipped gate was restored because
  downstream RL training still relies on LTX-2.
- The PR reports one H100 run (LPIPS 0.0418, PSNR 33.0941 dB, MAE 0.017016) for that exact case.
  It supports this gate's threshold, not a quantization implementation change, graph-mode parity,
  other LTX variants, or a broader quality claim. ^[PR #5831]

## MiniMax-H3 two-GPU FP8 quality-test initialization boundary

- The full-model CUDA quality test shares one `common_kwargs` mapping between its fused BF16
  baseline and transformer-FP8 candidate: `enforce_eager=True`, `tensor_parallel_size=2`,
  `text_encoder_tp_size=2`, and VAE tiling. On the exact two-card H100-80GB scope, encoder TP
  is required for the fused BF16 baseline to initialize; without it, rank 0 retains the full
  colocated text encoder and can OOM before the FP8 comparison begins.
- This restores a CI test topology/resource setting only. The author reported one local two-B300
  run at the stated H100-marked selection, but no completed H100-80GB Buildkite result is
  recorded here; therefore it does not establish an H100 pass, a result on other hardware, a
  broader memory bound, or a runtime/quantization implementation change. ^[PR #6742 / issue #6735]

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
