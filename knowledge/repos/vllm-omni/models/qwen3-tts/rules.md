---
title: "Qwen3-TTS 规则"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [vllm-omni, models, serving, qwen-omni]
sources: ["PR #5157"]
confidence: high
---

# Qwen3-TTS 规则

只有 `Q3TTS-数字字母` 是可审计规则 ID。

## Q3TTS-1a — ref-audio readiness 按 mode/capability 隔离

- 触发：同一 `ref_audio` 在 x-vector-only 与 ICL 请求之间复用 artifact。
- 强制：x-vector-only artifact 只证明存在 speaker embedding，不能满足需要 `ref_code`
  的 ICL；ICL 请求遇到这种 artifact 时必须保留原始 audio 并重新计算。
- 禁止：仅按 `artifact_key` 标 ready 后剥离 `ref_audio`；worker 此时既没有 `ref_code`
  也没有输入可补算，会把请求错误升级为 engine failure。
- 验收：同一 audio 的 x-vector → ICL 顺序重新计算且 server 存活；x-vector → x-vector
  与 ICL → ICL 仍命中 artifact-only reuse。 ^[PR #5157]

## Q3TTS-1b — ICL 是能力超集，是否反向复用必须显式取舍

- 触发：用 `(artifact_key, x_vector_only)` 等 exact-mode key 简化 readiness。
- 强制：记录 ICL artifact 同时含 `ref_code` 与 speaker embedding，因此理论上可满足
  x-vector 请求；若选择 exact-mode 隔离，应把首次 ICL → x-vector 的一次重算视为已知
  非阻塞性能代价。
- 禁止：把该重算描述为正确性要求，或在未 profiling 前增加复杂 capability 状态机。
- 验收：顺序测试证明 ICL → x-vector 只多一次重算、输出正确且后续同模式复用恢复；
  若优化为 capability predicate，保留 x-vector artifact 不能服务 ICL 的单向边界。 ^[PR #5157]

共享 readiness/错误隔离规则见 [Serving rules](../../components/serving/rules.md)；
Qwen 家族入口见 [Qwen-Omni](../qwen-omni/_index.md)。
