---
title: "dots.tts 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, ci]
sources: ["PR #6174", tests/e2e/offline_inference/test_dots_tts_expansion.py]
confidence: high
---

# dots.tts 规则

## DOTS-1a — weekly E2E scaffold 必须保留 prompt、队列与 request-noise oracle

- 触发：修改 dots.tts offline E2E、prompt helper、`compute_logits` result queue 或 flow-matching noise test。
- 强制：以显式 remote-code tokenizer 调 `build_dots_tts_prompt`，构造
  `[文本]<text>[文本对应语音]<|audio_gen_start|>` 的真实 Qwen2 token IDs。mixed case 的五个请求
  （一长四短）必须按位置维护 `_results_queue -> logits[i]`：每个 step 的 prefill row 也各贡献一个
  entry，不能压缩后错配。测试引用的既有 flow-matching noise 由
  `blake2b(seed:request_key:noise_step)` 派生 request-local generator；音频 oracle 只检查 finite、
  non-silent 和宽松时长。
- 禁止：用 bare prompt string 代替真实 prefill scaffold；跳过 prefill queue slot；用本 PR 声称新增
  runtime queue/RNG 修复；把 selector collection、non-silence 或相邻两次一致写成可懂度、speaker
  similarity、并发确定性、bitwise parity、性能或真实 L4 成功证据。
- 验收：zero-shot 输出为 48 kHz、finite/non-silent 且时长 `(0.5,30)` 秒，mixed 五项各在
  `(0.1,30)`；sequential singleton 同 prompt 运行两次，shape 相同且
  `torch.allclose(atol=1e-4)`（默认 nonzero `rtol` 仍生效）。三例都带 `slow`、`tts` 和一张 L4
  hardware marker；weekly `-m "slow and L4 and tts"` 收集 3，nightly
  `-m "full_model and L4 and tts"` 收集 0。PR 未在 L4 实跑，真实 weekly run 才能证明硬件结果。
  ^[PR #6174]
