---
title: "运行时热路径合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #4765", "PR #5068", "PR #5174", "PR #5666", vllm_omni/worker/]
confidence: high
---

# 运行时热路径合同

`EXEC-8a`、`EXEC-9a`、`EXEC-11a`–`EXEC-11b`：采样循环的不变量提取、固定输入缓存与掩码/精度边界，以及连续 AR 音频侧路和 codec 帧账本。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-8a — DiT Euler 采样循环必须只计算一次不变条件

- 触发：修改 GLM-TTS flow-matching DiT 的 Euler 采样循环、文本 embedding、RoPE、block-causal mask、CFG batch，或新增预计算输入参数。
- 强制：在每次 `_do_sample` 调用中只计算一次不随 timestep 或采样状态变化的 text embedding、RoPE、attention mask 和 CFG 双 batch 张量，并传入 DiT；同时保持 `seq_len`、设备、dtype 与 `forward()` 的合同一致，缺省参数仍保留原有调用行为。
- 禁止：在每个 Euler step 重复构造上述固定输入；让预计算 embedding 或 RoPE 在长度不匹配时静默继续；改变原有 mask device、模型 dtype 或 block-causal 语义；把 eager streaming 路径的优化结论外推为 CUDA-graph 路径或其他模型的通用结论。
- 验收：覆盖 CFG/non-CFG 和 block-causal streaming 路径，验证预计算输入的长度、设备、dtype 与采样序列匹配，并以数值/字节一致性、输出 shape 及 profiling 证明循环内不再重复执行固定计算；确认非 streaming CUDA-graph 和未提供预计算参数的旧调用仍正常。 ^[PR #5068]

## EXEC-9a — OmniVoice 热路径的固定输入缓存与掩码/精度边界

- 触发：修改 OmniVoice 离散扩散生成循环中的 D2H 同步、attention mask、RoPE、文本/音频 embedding、CFG、CUDA graph/eager 路径或 TF32 配置。
- 强制：将循环不变的文本 embedding、`audio_mask_3d`、RoPE 和 additive attention mask 在循环外缓存；批量取得 `c_lens` 并只在实际消费的 logits slice 上转为 fp32；CUDA graph 与 eager 使用相同的 float mask 语义，bool mask 必须将 True 映射为 `0.0`、False 映射为 `-inf`，已有 float mask 必须原样保留；TF32 只能通过显式配置 opt-in，并在 graph capture 前启用。
- 禁止：每步重复计算固定输入或执行逐请求 D2H `.item()`；对 float mask 使用布尔反转或把 bool 直接隐式转换进 float buffer；让 graph capture 与 replay 使用不同 mask dtype；默认开启或宣称 TF32 路径 bit-identical；只更新 conditional 或 unconditional 一侧的迭代 token。
- 验收：覆盖 eager 与 CUDA graph、bool 与 additive float mask、CFG/non-CFG 及不同 batch/concurrency，断言 masked 位置仍为 `-inf`、float mask 数值保留、graph/eager 输出满足既定精度合同、每步无固定输入重算和逐请求同步；单独验证 `enable_tf32` 默认关闭且显式开启前后性能/非 bit-identical 语义有记录。 ^[PR #5174]

## EXEC-11a — 连续 AR 音频侧路必须保持 fp32、上下文与正常终止

- 触发：vLLM-native AR 模型在每个 token/patch 旁路执行 DiT 或 flow-matching 采样、连续声码器解码，并通过 Omni multimodal output 输出增量音频。
- 强制：Euler/ODE 累积状态保持 fp32，仅将 DiT matmul 输入置为模型 dtype；跨 patch 保留 causal decoder 的 streaming window，并在模型停止或容量边界通过正常 stop 信号前 flush lookahead；输出按 step 发 delta audio，并保留 `meta.sparse_audio` 等路由标记。
- 禁止：以 bf16 作为多步积分默认累积 dtype；每个 patch 独立零填充解码；容量耗尽时 raise 使 engine 失效；停止时丢弃 decoder 尾部，或让 scaffold hidden 通过默认 multimodal merge 混入音频。
- 验收：跨两次 engine restart 做 bit-identical/确定性探针，做跨 patch 首词与边界上下文验证；将容量缩小后确认请求正常截断且同一 engine 的下一次 generate 仍成功，并断言逐步 delta 合并后只有目标音频张量。^[PR #4765]

## EXEC-11b — codec 音频流必须由逐请求帧账本驱动

- 触发：native-AR 音频模型逐步产生多头 codec codes，按 chunk 解码并通过 sparse multimodal output 交付增量 waveform 时。
- 强制：按 request id 保存 frame history 与 `emitted_frames` 账本；仅提交有效音频 frame；每个 decode window 带 lookback 并在裁剪后用实际 decode 结果推导 samples-per-frame；以原 request id 排队增量 payload，在 STOP 或预算最后一步、request 仍在输出 batch 时完成最终 flush，并保留 `meta.sparse_audio`。
- 禁止：在裸 chunk 边界解码、假定标称帧率或固定 hop、每帧解码或每次发送完整历史；把尾部音频放进 finished cleanup；让已离开输出 batch 的 request 继续产生不可路由 payload，或以 pooler/hidden state 充当音频。
- 验收：CPU codec stand-in 覆盖跨 first/steady chunk 边界的完整帧拼接、lookback 和 partial final chunk；真实 runner 覆盖 mixed requests、sparse routing、预算尾部与 cleanup；GPU smoke 断言 waveform 样本数等于 committed frames 的实际 frame ledger。 ^[PR #5666]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。
