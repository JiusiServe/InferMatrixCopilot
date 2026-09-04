---
title: "OmniVoice 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, model-executor, attention-runtime, ffn-runtime]
sources: ["PR #6317", vllm_omni/model_executor/models/omnivoice/omnivoice_generator.py, vllm_omni/model_executor/models/omnivoice/fused_qkv_rope.py, tests/model_executor/models/omnivoice/test_cuda_graph_generator.py, tests/model_executor/models/omnivoice/test_fused_projection_load.py, tests/model_executor/models/omnivoice/test_fused_qkv_rope.py, tests/model_executor/models/omnivoice/test_mask_dtype.py, tests/model_executor/models/omnivoice/test_triton_kernels.py]
confidence: high
---

# OmniVoice 规则

只有 `OMNIVOICE-数字字母` 是可审计规则 ID。双注册、pipeline 与部署结构见
[_index](./_index.md)；共享固定输入、mask 与 TF32 约束见
[EXEC-9a](../../components/model-executor/rules-runtime-hot-paths.md#exec-9a-omnivoice-热路径的固定输入缓存与掩码精度边界)。

## Direct 代码快速入口

| 正在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| OmniVoice generator 的 fused projection、checkpoint loading、attention prologue、SwiGLU、residual、mask dtype、CUDA graph 或 Triton fallback | `core`：`OMNIVOICE-1a` | `vllm_omni/model_executor/models/omnivoice/omnivoice_generator.py::{OmniVoiceGenerator._load_fused_projections,OmniVoiceAttention.forward,OmniVoiceMLP.forward,OmniVoiceTransformerBlock.forward,_OmniVoiceCUDAGraphForward}` → `vllm_omni/model_executor/models/omnivoice/fused_qkv_rope.py::{fused_qkv_norm_rope,fused_cuda_supported,_eager_qkv_norm_rope}` |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次命中 OmniVoice generator 热路径或其 checkpoint/attention 测试 | `OMNIVOICE-1a` |

## OMNIVOICE-1a — OmniVoice 生成器热路径必须保持 pack、加载、注意力与回退合同

- 触发：修改 OmniVoice 的 Q/K/V 或 gate/up projection、checkpoint loader、Q/K RMSNorm/RoPE、GQA、SwiGLU、residual threading、attention mask、CUDA graph，或 `fused_qkv_rope.py` Triton/eager 路径。
- 强制：checkpoint pack 顺序固定为 `qkv=[q,k,v]`、`gate_up=[gate,up]`；一旦某层开始 pack，缺少或仅出现部分 source shards 必须拒绝，不能让 fused parameter 保持随机初始化；未进入任何 fused-source group 的 shard 保持 generic loader 处理。attention prologue 只以 fp32 进行 Q/K RMSNorm、Q/K 权重计算与 Q/K RoPE，V 保持原 projection 值；随后按 GQA repeat K/V，并产出 contiguous `[batch, heads, sequence, head_dim]`（BHSD）。Triton 仅在 Triton 可用、CUDA tensor、QKV contiguous、head dim 为正的 2 的幂、Q 与 KV head 数都可被 8 整除且 GQA 可整除时启用；其他情况走 eager reference。residual 的加法/归一化代数不变，SwiGLU 保持 `silu(gate) * up` 的顺序。
- 禁止：改变 source shard packing 次序、接受 partial/missing pack group，或把没有 fused source 的整组 shards 误判为 partial；对 V 应用 Q/K norm 或 RoPE；重排 GQA 的 K/V 映射、返回非 contiguous BHSD；把 Triton 的存在或 CUDA 单项条件当作充分资格，或删除 eager fallback；为方便而给 generator mask 重新引入 fp32 默认。不得把本 PR 的 A800、CPU 或 CUDA 测试/性能证据外推为其他硬件、shape、后端或普遍 serving support。
- 验收：CPU 覆盖 pack order、全缺 source group 不触发 pack、任一 partial/missing 或错误 shape 拒绝，以及 eager 输出；CUDA+Triton 仅在上述 geometry 下对 eager reference 覆盖 fp32/fp16/bf16、Q/K norm+RoPE、未经变换的 V、正确 GQA index 与 contiguous BHSD；无 Triton、CPU、non-contiguous 或不合资格 geometry 必须回退。mask 测试覆盖 `model_dtype` 的 bool True→`0.0`、False→`-inf`、float 原样保留和 graph replay；graph/eager 及 residual/SwiGLU 回归保持既有精度合同。A800 上的 float16/float32 性能和 CPU/CUDA 单测只构成该 PR 的有界证据，不构成广泛性能或支持承诺。 ^[PR #6317]
