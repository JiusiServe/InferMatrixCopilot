---
title: "Qwen3-TTS codec tokens 输出合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, models]
sources: ["PR #8619"]
confidence: high
---

# Qwen3-TTS codec tokens 输出合同

## Q3TTS-6a — codec tokens 按请求有效帧导出并沿注册 key 合并

- 触发：修改 Qwen3-TTS Code2Wav multimodal output 或 codec token 客户端消费。
- 强制：codec token key 在根 client output registry 声明 CONCAT_DIM0；零有效帧返回 long 类型 [0,q]，有效 codes 只取当前 request 的 valid rows 并转成 frames×q。async chunk 从当前块起始取，非 async 去掉已用 left context；顺序与对应音频块一致。
- 禁止：把 padding/其他请求的 code 行或重复 left context 导出；只改模型输出而漏 registry，或将 shape 合同扩大成已完成端到端 transcript/音频验收。
- 验收：覆盖 empty、valid-row selection、async/non-async context、分块累计顺序和不同请求隔离；客户端按注册 CONCAT_DIM0 合并后与完整 codes 对照。 ^[PR #8619]
