---
title: "CosyVoice3 F0 device 与 native vocoder 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models]
sources: ["PR #7518"]
---

# CosyVoice3 F0 device 与 native vocoder 规则

## COSY-F0-1a — F0 device 优化必须保留标准 FP32 路径与 TF32 恢复

- 触发：修改 causal HiFT F0 inference、COSYVOICE3_F0_ON_CPU、causal convolution cache 或 STFT window。
- 强制：标准loader的predictor保持FP32；CUDA且无CPUescape时在speech_feat设备执行，迁移时明确FP32，input.float后结果回输入dtype。临时禁matmul/cuDNN TF32，finally恢复两个旧flag；CPUescape/非CUDA用CPU float输入并返回原device/dtype。使用x.new_zeros/f0.new_zeros继承device/dtype，CausalConv1d默认cache=None；periodic FP32 torch.hann_window为nonpersistentbuffer，整数math.prod/cumulative scale保持原upsample/crop。
- 禁止：把标准FP32加载的正确性外推为任意.half/混合dtype模块都自动修复；保留默认CPUtensor再每块to(device)；使TF32异常后泄漏；用duration一致/高cosine声称waveformbitidentity或通用CUDAgraph可用。原有有界mel/phase合同保持COSYVOICE3-1c，后续packed load→move→fold合同保持COSY-PACKED-1b。
- 验收：stream/finalize voicedF0、CPUescape、默认GPU、predictorplacement、TF32开启/异常后恢复、causalcache与periodicwindow数值分别覆盖；用显式容差检查CPU/GPUwaveform与总samples，性能和graph证据独立归属实际revision。 ^[PR #7518]
