---
title: "vLLM-Omni CI"
created: 2026-07-10
updated: 2026-09-04
type: index
tags: [vllm-omni, ci]
sources: [.buildkite/cuda/pipeline.yml, docs/contributing/ci/test_system_overview.md, tests/diffusion/quantization/test_wan_autoround_mxfp4.py, tests/e2e/offline_inference/test_wan21_autoround_mxfp4.py, "PR #5544", "PR #6613", tests/e2e/online_serving/test_qwen_image_expansion.py, tests/dfx/perf/tests/test_qwen_image_vllm_omni.json]
---

# vLLM-Omni CI

## 什么时候查这里

- 处理 vLLM-Omni 的 L2/L4、模型测试配置或 CI 特有问题。

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

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 审查硬件 lane、回归 fence、CI 工具供应链或 xdist/shared fixture | [CI rules](rules.md) |
| 查看仓库特有 CI 陷阱 | [CI guides](guides/_index.md) |
| 调查历史 CI 失败 | [CI incidents](incidents/_index.md) |
