---
title: "Qwen3-Omni Realtime 音频 history 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models, qwen-omni]
sources: ["PR #7285"]
confidence: high
---

# Qwen3-Omni Realtime 音频 history 规则

## QOMNI-2a — Realtime truncate 的 Qwen token 前缀只能作为近似对齐

- 触发：修改 Qwen3-Omni audio history、token IDs 或 `audio_end_ms`→text prefix。
- 强制：当前约 383 ms/token 的换算仅用于 Qwen path；token count 四舍五入并限制在
  已生成 IDs 的区间，缺 token IDs 返回空前缀。只有音频长度与 content_index 合法时才
  改 history；共享会话存储、deferred event 与 terminal response 归 serving owner。
- 禁止：把固定 token/ms 当作逐 token 强制对齐或精确词级时间戳；将 Qwen ratio 放进
  generic session，使其他模型或 native duplex 继承；把播放确认扩展当作 OpenAI 标准必需输入。
- 验收：检查 0 ms、半 token rounding、超出 IDs 的 clamp、空 IDs 与合法 truncate；
  精确字幕/词级对齐需要独立真实音频证据，不能由这套近似推导。^[PR #7285]

完整 route、PCM 与 history 生命周期见 [OpenAI Realtime 规则](../../components/serving/rules-realtime-openai.md)；
Thinker/Talker 与 stage transfer 见 [Qwen-Omni 规则](rules.md)。
