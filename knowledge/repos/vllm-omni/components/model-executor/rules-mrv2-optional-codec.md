---
title: "MRv2 optional codec 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #8484"]
confidence: high
---

# MRv2 optional codec 规则

## EXEC-MRV2-CODEC-1a — shared eager-MTP preprocess 不得假定 model 自带 stream decoder

- 触发：修改 OmniModelState.run_preprocess、eager-MTP replay 或 optional codec access。
- 强制：先以 getattr(model, stream_decoder, None) 验证 codec 存在，只有具有 codec 的
  Talker 才走相应 replay；无 attribute 与显式 None 均保持正常 preprocess/sample rows。
- 禁止：把 Qwen3-TTS 的 in-Talker codec 属性强加给 Qwen3-Omni 等 model；MagicMock
  自动生成 attribute 或测试 helper 总设 None 掩盖真实缺失情况。
- 验收：parameterize attribute 存在/None/删除三条路径，断言样本保留行为与 replay
  eligibility；真实目标 MRv2 deploy 另做 warmup/serving，作者单一硬件吞吐不外推。^[PR #8484]

attention metadata 见 [MRv2 capture](rules-attention-capture.md)；
model-specific Talker/codec 拓扑见 [Qwen-Omni](../../models/qwen-omni/_index.md)。
