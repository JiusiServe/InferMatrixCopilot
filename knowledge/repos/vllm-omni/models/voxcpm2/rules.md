---
title: "VoxCPM2 请求噪声规则"
created: 2026-09-22
updated: 2026-09-22
type: rule
tags: [vllm-omni, models]
sources: ["PR #7866"]
---

# VoxCPM2 请求噪声规则

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批 live 源码 |
|---|---|---|
| request seed、CFM noise、batched prefill/decode、graph replay | `request-noise`：`VOXCPM2-2a` | `worker/gpu_ar_model_runner.py` request seed → `model_executor/models/voxcpm2/` request generator 与各 noise fill 站点 |

## VOXCPM2-2a — 请求 seed 必须驱动模型内 CFM/噪声流，且与 batch 位置无关

- 触发：TTS/talker 在 `forward()` 内绘制 CFM、flow-matching 或同类噪声，且公开协议声称 `seed` 可复现；修改 `_omni_seed`、`SamplingParams.seed`、per-request `torch.Generator` 或 `deterministic_cfm_noise`。
- 强制：`SamplingParams.seed` 到达 vLLM sampler 不等于到达模型内噪声点。有 seed 的请求必须在首次 prefill 从 runner 的 `_omni_seed` 构造请求私有 `Generator`，并在每个噪声 fill 站点（eager、cuda-graph、batched prefill/decode、unified replay）对 shape `(1, …)` 的行切片使用该 generator。同 text+seed 的噪声流必须与 batch 组成、request id 无关；无 seed 保持全局 RNG；`deterministic_cfm_noise` 的 request-id 哈希只服务 replay，且请求 seed 优先。
- 禁止：仅依赖 `SamplingParams.seed` 或全局 `normal_()` 宣称 speech seed 合同；用 request-id 哈希冒充用户 seed；让 seeded 行的噪声依赖同 batch 其他请求。
- 验收：跨 request 同 seed 字节一致、异 seed 敏感、batch 位次无关、seed 优先于 replay 哈希；覆盖所有噪声站点。^[PR #7866]
