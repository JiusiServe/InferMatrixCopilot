---
title: "平台后端合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #5886", "PR #6061", "PR #6096", vllm_omni/platforms/, "PR #5604"]
confidence: high
---

# 平台后端合同

`EXEC-10a`、`EXEC-12a`–`EXEC-13a`：NPU 平台 runner 的 runtime mode 与 dummy-run 接口、ROCm 分页注意力的 packed KV varlen 路径，以及 NPU 模型补丁的注册与回归。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-10a — NPU 平台 runner 必须保持 runtime mode 与 dummy-run 接口合同

- 触发：平台 runner 覆盖 `dummy_run` 或接收 `cudagraph_runtime_mode`，而共享 runner 新增运行时参数或需要校验复合 runtime mode。
- 强制：平台 override 必须保留共享签名中的 `randomize_inputs` 默认值并将其传给 `maybe_randomize_inputs`；runtime mode 必须调用 `is_valid_runtime_mode()` 判断当前实例是否有效。
- 禁止：通过实例调用返回集合的 `valid_runtime_modes()` 冒充实例有效性校验，或因共享签名新增可选参数而让平台 override 产生接口漂移。
- 验收：对 base NPU runner 与 generation override 分别覆盖 `randomize_inputs` 的默认和显式路径，并用包含 `FULL_DECODE_ONLY` 等复合模式的正负用例断言 `is_valid_runtime_mode()` 的校验结果和签名 parity。 ^[PR #6096]

## EXEC-12a — ROCm 分页注意力必须走 packed KV 的兼容 varlen 路径

- 触发：修改 `vllm_omni/experimental/ar_diffusion/kv_cache/paged_attention.py` 的 ROCm 分页注意力、AITER/`flash_attn` varlen kernel、`block_table` 映射或 KV block layout。
- 强制：ROCm 路径必须避开 CUDA 专用的 `vllm.vllm_flash_attn` 接口，优先解析 AITER、再回退到 `flash_attn`；依据每个请求的 `seq_lens` 构造 `cu_seqlens_k`，在 device 上按 `block_table` gather 可见 KV 为 packed tensors，并使用匹配的 query offsets、最大长度、`softmax_scale` 和 `causal` 参数调用 `flash_attn_varlen_func`。
- 禁止：复用 CUDA 专用的 `seqused_k`/`fa_version` 参数合同；直接把不兼容的 ROCm paged kernel 用于 AR-Diffusion 的 frame-aligned blocks；依赖 ROCm kernel 对 `block_table` 的隐式支持；丢失逐请求长度或把 KV gather 到 CPU 后再调用 kernel。
- 验收：在 ROCm GPU 上覆盖不同 history/action 长度、block table、请求长度和 `commit_current` 组合，与 dense reference 校验数值和输出 shape；分别验证 AITER 与 `flash_attn` fallback，确认 HIP 路径不导入 `vllm.vllm_flash_attn`，并确认 CUDA/CPU 路径行为不变。 ^[PR #5886]

## EXEC-13a — NPU 模型补丁必须由生产初始化路径注册并可回归

- 触发：在 NPU platform 初始化中加入模型专有 monkey patch、融合算子或其他必须全局启用的 model hook。
- 强制：把 hook 封装成幂等的 `apply_*_patch()`，在 `adapt_patch(is_global_patch=True)` 完成后由生产初始化路径显式调用；注册必须只指向目标模型 consumer，并保留非 NPU和其他模型路径。测试必须验证生产注册链，而不只直接调用 helper。
- 禁止：依赖 import side effect 或手工调用 helper 代替平台注册；只覆盖 patched function 的数值而不验证注册实际生效；把模型专有 patch 扩大到 MiniMax H3 DiT 或所有 NPU 模型。
- 验收：从 NPU 平台初始化/注册入口运行测试，断言目标 Qwen3-VL text encoder 的 consumer 已替换且重复初始化不重复 patch；随后用真实 consumer 覆盖至少一个 BNSD fast path、一个 BSND fallback 和 batched M-RoPE。^[PR #6061]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。

## EXEC-13b — NPU 精确形状图捕获必须隔离动态边界并失败即停

- 触发：修改 `vllm_omni/platforms/npu/graph_tools.py` 的 NPUGraph 捕获/重放、NPU 模型补丁的 tensor-only 子图，或 Token2Wav 图执行上下文。
- 强制：图缓存 key 必须同时包含 operation、缓存模式、所有输入的完整 shape、dtype 和 device；首次匹配调用先 eager 预热，再使用 vLLM global graph pool 捕获，后续重放前把当前值复制到静态输入，并在请求状态或 streaming cache 接管前 clone 持久化输出。Python metadata、CPU 频率张量、H2D、随机数和动态 state 必须留在 eager 边界；捕获失败后必须停止该 stage 进程。
- 禁止：捕获整个请求编排或包含动态 Python/RNG 状态的路径；使用无界 shape cache、绕过 global graph pool、在 nested capture 中重放、复用会被下一次重放覆盖的输出，或吞掉 capture、patch setup、SDPA context 的异常后继续运行。
- 验收：CPU/mock 测试覆盖 exact-signature dispatch、cached/uncached bucket、global graph pool、persistent-output ownership、capture failure fail-stop 和异常传播；A3 硬件测试分别比较 eager 与 uncached/cached NPUGraph 的输出、shape 和 cache，并核对图数量上限与 runtime preconditions。^[PR #5604]

