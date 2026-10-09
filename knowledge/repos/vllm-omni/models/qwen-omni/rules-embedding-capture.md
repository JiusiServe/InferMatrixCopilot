---
title: "Qwen3-Omni layer-0 embedding capture 合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, models]
sources: ["PR #8532"]
confidence: high
---

# Qwen3-Omni layer-0 embedding capture 合同

## QOMNI-EMBED-1a — 编译 LM 修改输入前保存 layer-0 embedding

- 触发：修改 Qwen3-Omni return_hidden_states、compiled LM wrapper 或 PP captured hidden key。
- 强制：当请求捕获 layer 0 时在进入可能原地修改 inputs_embeds 的 compiled LM 前 clone 原始 embedding，inner capture 列表排除 0；返回 tuple hidden layers 和 IntermediateTensors 两条路径都补回该副本。修改过的 PP capture producer/consumer 使用同一 _get_capture_key。
- 禁止：把已被 compiled forward 原地改写的输入当作原始 layer 0；仅修 tuple 路径或在相关 PP 路径拼不一致 key。
- 验收：stub forward 原地修改输入，分别断言 tuple 与 IntermediateTensors 中 layer 0 仍是原值，其他 capture 输出与 key 保持一致；不把 CPU stub 当作 GPU compile 验证。 ^[PR #8532]
