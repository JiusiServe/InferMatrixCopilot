---
title: "Async chunk（跨 stage 分块流式）"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, components, distributed]
sources: [docs/design/feature/async_chunk.md, vllm_omni/distributed/omni_connectors/transfer_adapter/chunk_transfer_adapter.py]
---

# Async chunk（跨 stage 分块流式）

官方 spec：`docs/design/feature/async_chunk.md`（`main @ 5c390096` 复核）；
传输适配层 `omni_connectors/transfer_adapter/chunk_transfer_adapter.py`，
调度侧等待状态机在 [Scheduler](../../scheduler/architecture.md) 的
`OmniSchedulingCoordinator`。

- 语义：多 stage pipeline（如 Qwen3-Omni Thinker→Talker→Code2Wav）不等上游 stage
  完整输出，按 chunk 就绪即处理即转发——降低延迟、跨 stage 重叠执行、支持流式
  音频输出；chunk IO（get/put）在后台线程与计算重叠，调度器不因等 chunk 阻塞。
- chunk 大小定义：prefill 段 `chunk_size = num_scheduled_tokens`（chunked
  prefill）；decode 段 `chunk_size = 1`（逐 token 流式）。qwen3-omni 实例：
  Thinker→Talker 逐 decode step（通常 1）；Talker→Code2Wav 积累到
  `codec_chunk_frames`（默认 25）再发——初始阶段按服务负载动态选初始 chunk（IC）
  以降 TTFP，可用逐请求 API 字段 `initial_codec_chunk_frames` 覆盖；Code2Wav 流式
  解码（支持批推理）。
- 配置：deploy 顶层 `async_chunk`（默认 true）；端到端跑完的 pipeline 应 pin
  `false`——单 stage diffusion 必须 `async_chunk: false` 的事故见
  [ci-gotchas](../../../ci/guides/ci-gotchas.md) 第 2 条。
- 性能：spec 附 E2E/TTFT/TPOT/TTFP/RTF/ITL 实测表（并发 1/4/10 × code2wav batch
  1/64 等组合）——引用数字前以当前版本原文为准。

## 相关

- 阈值变差对精度断言的影响（async_chunk 模式阈值 0.65 案例）见
  [accuracy-attribution](../../../ci/guides/accuracy-attribution.md)。
