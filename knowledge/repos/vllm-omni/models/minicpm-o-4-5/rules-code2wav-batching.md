---
title: "MiniCPM-o 4.5 Code2Wav 并发批处理规则"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #6021", vllm_omni/model_executor/models/minicpmo_4_5/batched_token2wav.py, vllm_omni/model_executor/models/minicpmo_4_5/minicpmo_4_5_code2wav.py, vllm_omni/platforms/npu/models/minicpmo_4_5_code2wav.py, tests/model_executor/models/minicpmo_4_5/test_code2wav_batching.py, tests/platforms/npu/test_graph_tools.py]
confidence: high
---

# MiniCPM-o 4.5 Code2Wav 并发批处理规则

## MCPMO-1j — Code2Wav 并发 duplex batch 必须按 request 保存 ragged state

- 触发：修改 `MiniCPMO45Code2Wav` bucket/initial-batch partition、`BatchedToken2Wav.decode_ragged_batch`、attention cache dtype 或 NPU Code2Wav patch。
- 强制：compatibility bucket 只由 prompt/cache history/epoch 决定；当前 token length 与 final flag 不同的短行可共享 masked ragged DiT pass，输出和 Flow/HiFT cache 必须按原 request row 回填。超出 RelPos-safe encode window 的行回退 `decode_batch` 的 sliced path。`code2wav_initial_batch_size` 为非零时必须不小于 min batch，partition 后每个 initial batch 都满足 min；未设置时不改变既有全 bucket 行为。BF16 attention cache 只改变存储表示，compute 保持 FP32。
- 禁止：用 batch index 复用另一 session 的 state；让 ragged path 跳过 long-input slicing、final-row mask 或 complete-row 检查；把 BF16 cache 当作 compute dtype 变化；用 generic generation scheduler 等待来凑 MiniCPM batch，或把外部 N=8 证据当作默认 two-session deploy/strict realtime claim。
- 现有边界：NPU patch 尚未在 `decode_ragged_batch` 外围安装与 exact path 相同的 flow execution context；其 BF16 guard 使用 Python `bool`，因此字符串 `"false"`/`"0"`/`"off"` 会被误判为启用；当 initial cap 为 0 且 min batch 大于 1 时 initial-marker bucket 仍可绕过 min check；steady-state batch 没有 execution-layer cap。CUDA-only BF16 opt-in 与 NPU/ragged 配置必须分别验证，不能把这些限制描述成已关闭。
- 验收：比较 mixed-length/final-flag batch 与逐 request exact decode 的 audio、Flow 和 HiFT state；覆盖 oversized row fallback、缺失中间 row fail-closed、initial min/max partition、BF16 storage/FP32 compute，以及上述 NPU/initial-marker/steady-state residual limits 的回归或显式拒绝。^[PR #6021]
