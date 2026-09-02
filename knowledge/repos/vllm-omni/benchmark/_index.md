---
title: "vLLM-Omni 性能与 Profiling"
created: 2026-07-10
updated: 2026-07-10
type: index
tags: [vllm-omni, benchmark]
sources: [benchmarks/tts/bench_tts.py, benchmarks/tts/model_configs.yaml]
---

# vLLM-Omni 性能与 Profiling

## 什么时候查这里

- 跑 vLLM-Omni benchmark、profiling，或查询仓库内历史性能结果。

## 不放什么

- 跨仓库通用的性能测试方法。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 查看旧 benchmark 总览 | [overview](overview.md) |
| 运行 AR graph 或 Hunyuan benchmark | [benchmark guides](guides/_index.md) |
| 调查 profiling、模型加载和性能验证错误 | [benchmark incidents](incidents/_index.md) |
| 查询历史结果 | [results](results/_index.md) |

`benchmarks/tts/model_configs.yaml` 是共享 TTS runner registry；新模型在这里声明 model、deploy、voice/
reference 与 workload，结果保留解析配置、seed、speed、并发和音频属性。IndexTTS 2.5 条目只证明
harness 可路由；没有 native 2.5 baseline 时不得声称性能等价。^[PR #5957]
