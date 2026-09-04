---
title: "vLLM-Omni TTS CI 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, ci]
sources: ["PR #6861", .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, .buildkite/amd/test-amd-merge.yml, tests/e2e/online_serving/test_qwen3_tts_base.py]
confidence: high
---

# TTS CI 规则

## OMNI-CI-1d — Qwen3-TTS Base 的 dummy-ready oracle 与 real-weight merge coverage 必须分离

- 触发：修改 Qwen3-TTS Base/CustomVoice 的 CUDA/AMD ready 或 merge step、marker、run level、source dependencies。
- 强制：Base online 保留 `advanced_model`，但移除 `core_model`；CUDA Ready 不收集 Base step。CUDA merge
  仍收集 Base offline+online real-weight pair，AMD merge 也保留相同 pair。新增 serving dependencies 只扩大
  CUDA merge 的 Base/CustomVoice 与 CUDA Ready 的 CustomVoice；不得外推为 AMD dependency 变更。
- 禁止：用 Ready dummy-weight 绿灯证明 Base real-weight/EOS 行为，或把 pending merge job 写成已证明通过。
- 验收：Ready `core_model` collect-only 对 Base 为空；CUDA/AMD merge marker matrix 仍含 Base offline+online；
  source-file mutation 分别验证上述 CUDA scope。^[PR #6861] ^[issue #6855]
