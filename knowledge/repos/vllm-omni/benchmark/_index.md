---
title: "vLLM-Omni 性能与 Profiling"
created: 2026-07-10
updated: 2026-09-05
type: index
tags: [vllm-omni, benchmark]
sources: [benchmarks/tts/bench_tts.py, benchmarks/tts/model_configs.yaml, "PR #6522", "PR #6634", "PR #6818", vllm_omni/benchmarks/data_modules/omniinteract_dataset.py, vllm_omni/benchmarks/omniinteract.py, vllm_omni/benchmarks/patch/patch.py, tests/benchmarks/patch/test_patch.py, vllm_omni/benchmarks/duplex/, vllm_omni/entrypoints/cli/benchmark/omni_duplex_eval.py, vllm_omni/experimental/fullduplex/client.py]
---

# vLLM-Omni 性能与 Profiling

## 什么时候查这里

- 跑 vLLM-Omni benchmark、profiling，或查询仓库内历史性能结果。

## 不放什么

- 跨仓库通用的性能测试方法。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 新增/审查 perf JSON、warmup 覆盖、realtime artifact 或 Hub dataset fallback | [benchmark rules](rules.md) |
| 查看旧 benchmark 总览 | [overview](overview.md) |
| 运行 AR graph、Hunyuan 或 MiniCPM-o Omni-DuplexEval benchmark | [benchmark guides](guides/_index.md) |
| 调查 profiling、模型加载和性能验证错误 | [benchmark incidents](incidents/_index.md) |
| 查询历史结果 | [results](results/_index.md) |
| 运行/审查 OmniInteract native-duplex serving benchmark（client ITL 优先，Stage-0 仅为无正 client ITL 的受限恢复） | [OmniInteract realtime guide](guides/omniinteract-realtime.md) |

`benchmarks/tts/model_configs.yaml` 是共享 TTS runner registry；新模型在这里声明 model、deploy、voice/
reference 与 workload，结果保留解析配置、seed、speed、并发和音频属性。IndexTTS 2.5 条目只证明
harness 可路由；没有 native 2.5 baseline 时不得声称性能等价。^[PR #5957]
