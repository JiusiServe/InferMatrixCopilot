---
title: "Diffusion attention 规则"
created: 2026-09-02
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5887", "PR #5891", "PR #5897", "PR #5997", "PR #6000", docs/user_guide/diffusion/attention_backends.md, vllm_omni/config/omni_config.py, vllm_omni/config/stage_config.py, vllm_omni/diffusion/attention/backends/abstract.py, vllm_omni/diffusion/attention/backends/flash_attn.py, vllm_omni/diffusion/attention/backends/rainfusion_attn.py, vllm_omni/diffusion/data.py, vllm_omni/engine/arg_utils.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/cli/serve.py, vllm_omni/platforms/npu/platform.py, tests/config/test_omni_config.py, tests/diffusion/attention/test_flash_attn.py, tests/diffusion/attention/test_rainfusion_plan.py, tests/diffusion/cache/test_teacache_extractors.py, "PR #5500", "vllm_omni/diffusion/models/ltx2/ltx2_transformer.py", "PR #6070", "vllm_omni/diffusion/attention/backends/cudnn_attn.py", "PR #5614", "PR #5194", "vllm_omni/diffusion/models/hidream_o1_image/hidream_o1_image_transformer.py", "vllm_omni/diffusion/models/hidream_o1_image/pipeline_hidream_o1_image.py", "PR #6181", "vllm_omni/diffusion/cache/teacache/extractors.py", "vllm_omni/diffusion/models/longcat_image/pipeline_longcat_image.py", "vllm_omni/diffusion/models/longcat_image/pipeline_longcat_image_edit.py"]
confidence: high
---

# Diffusion attention 规则

## DIFF-1f — deterministic flag 只对构造时选定的 local dense FA 生效

- 触发：修改 `--fa-deterministic`、diffusion config projection 或 local `FLASH_ATTN` dispatch。
- 强制：direct CLI 经 engine args/AsyncOmniEngine 传播到 `OmniDiffusionConfig`，attention impl 在构造
  时捕获；true 只在 dense unmasked `flash_attn_func` 传 `deterministic=True`，false 必须省略 kwarg
  保留 library default。structured deploy 必须由 `_DiffusionConfigProjection` 显式拥有字段。
- 禁止：把该 flag 描述成全 FlashAttention、跨平台或运行时动态 toggle。piecewise、packed-varlen、
  masked-varlen、dense-varlen fallback 以及 XPU/NPU path 不消费 kwarg，启用时只能 warning once。
- 验收：direct CLI 与 structured/deploy config 分别做 true/false 端到端传播；dense true/false 精确断言
  kwarg，每条 non-dense path 断言不传且只警告一次，构造后改 config 不得被误认为立即生效。目标 pin
  已将 `fa_deterministic` 加入 `_DiffusionConfigProjection`，因此 `from_kwargs` 不再过滤且派生
  config/stage-engine field set 会分类该字段；PR 引用/运行的既有 classification test 只断言字段分类
  集合与 projection dataclass 一致，没有以 non-default true 证明 structured/deploy→
  `OmniDiffusionConfig`→backend 的值传播，也没有重跑 Qwen accuracy。^[PR #5887] ^[PR #5897]

## DIFF-1g — NPU packed mask-free 是 model opt-in + backend fallback 双合同

- 触发：修改 `supports_packed_mask_free`、NPU `FLASH_ATTN`、packed cu/max metadata、
  `npu_attn_varlen`、`laser_input_scale` 或 MindIE-SD backend selection。
- 强制：base backend capability 默认 false；`FlashAttentionBackend` 只在 CUDA/NPU 报 true，XPU
  仍读 mask。NPU 新分支还必须由每次 forward 的 `extra["npu_attn_varlen"]` 显式 opt in；未设置的
  Wan/Cosmos 等 caller 保持原 masked `attention_forward`。quantized KV 在 `forward_npu` 更早转入
  `forward_fa_quant_npu`，不消费这套 mask-free metadata。显式选择 NPU `FLASH_ATTN` 且 MindIE-SD
  存在时，platform 必须在首次 custom-op registry snapshot 前 eager import 它。^[PR #5891]
- 强制：默认 opt-in 路径用 MindIE-SD TND varlen，host list 传累计 end offsets；只有 env 精确等于
  `ascend_laser_attention` 才改走 prefix K/V slice。resolver 只接受 non-causal、batch=1、四个 packed
  key 齐全、Q/K cu shape 相同且至多两 documents、Python-int max length 在 bounds 内，以及
  `[real,pad]` 中 real 不短于 pad；无 padding 的单 document 也接受。Q/K/V 从 BSND squeeze batch
  不复制；Laser 保留 full Q、只裁 K/V，padding-row output 必须由下游忽略。
- 强制：packed branch 拒绝 metadata 时，如果 caller 因 capability 没构造 mask，backend 必须用合法
  `valid_kv_length` 重建 prefix mask；缺失、非 int 或越界立即报错，不能对 padding 做 unmasked
  attention。重建路径仍会扩展 quadratic `full_qk`，所以是 correctness fallback，不是 memory
  fast path。Laser 可消费数值型 `input_scale>1`：Q/K/V 同除、softmax scale 乘平方、output 再乘回；
  absent/invalid scale 不缩放。模型只应给有硬件数值证据的 exact power-of-two factor。
- 禁止：把任意 `MINDIE_SD_FA_TYPE` 当作 honored selection；target 对除 exact Laser string 外的合法值、
  typo 和垃圾值都静默走 TND varlen。不得从 capability=true 推断任意 packed layout安全：resolver
  只检查 cu tensor shape、不读其 offset values，真实 producer 必须另证 `[0,used,total]` 内容。
- 验收：CPU/mock 覆盖 resolver 接受/拒绝矩阵、env dispatch、default caller masked path、fallback
  mask/fail-closed、host lists、Laser layout/slice/scaling；真实 NPU 再与 masked FP32/BF16 reference
  对照。target tests 覆盖前者但 mock kernel 不证明 MindIE 数值；NPU SDPA 的同类 `full_qk` churn
  未改。capability 是 classmethod，所有非 `AttentionBackend` duck-typed doubles/plugins 也须兼容；
  repo 内 TeaCache `FakeBackend` 已镜像 abstract default，显式返回 false 并恢复 masked-path
  extractor coverage。该修复只改 test double，没有给 production consumer 加 default-safe access，也
  没有证明 third-party registry override 或未继承 base class 的 backend 完成了 capability
  census；这些实现仍须继承合同或显式实现 method。^[PR #5891] ^[PR #5997]

## DIFF-1m — TRTLLM packed-padding 快路径必须隔离 producer contract、ragged documents 与 SAGE gate

- 触发：修改 `PackedPaddingMetadata`、TRTLLM packed `cu_seqlens`、`supports_packed_mask_free`、
  padded-output restore、SAGE quantization gate 或 multi-document varlen capability。
- 强制：TRTLLM 只把 `PackedPaddingMetadata` 当作 single physical batch 的 producer-owned
  `[real,pad]` shortcut：Q/KV host lengths 必须是 Python int，在 flattened tensors bounds 内并与
  `max_seqlen_q/k` 及可选 `valid_kv_length` 相等；canonical two-element `int32` cu_seqlens 必须和
  Q/K device 一致。该 path 裁 Q/K/V 后把 output 补零回物理 shape，且从不读取或 materialize
  `attn_mask`。generic complete cu_seqlens 仍支持 genuine multi-document ragged varlen，并删除
  paired trailing empty document；两条合同不能互相降级或混用。
- 禁止：接受任何 nonempty TRTLLM `attn_mask`、用 producer shortcut 表示 arbitrary mask 或
  multi-request block-diagonal layout，或让未验证的 CUDA scalar read 回到 single-request fast path。
  不得把 tail document 短于 `k_block_size` 造成的 dense fallback 描述为 SAGE 的真实-document
  检查已经完成。
- 验收：backend tests 分别覆盖 malformed host/device/dtype/shape/max-length metadata、trim/zero
  restore、generic unequal Q/KV ragged batch、trailing empty pair、complete packed metadata 加
  nonempty mask 的 rejection，以及 real multi-document output 对逐 document reference。SAGE 还要覆盖
  alignment tail 不参与 real-document minimum；该 fix 在 PR #6542 尚未提交，现存行为可整 batch
  fallback dense。性能只可引用该 PR 的 exact 4×B300 Nsight all-to-all→FMHA interval，不能以 CPU mock、
  kernel gap 或 frame hash 声称 E2E latency/quality。^[PR #6542]

## DIFF-1h — RainFusion irregular tail 由 MindIE-SD 保护，不能 padding 伪对齐

- 触发：修改 `RAINFUSION_ATTN`、`rf_v2`、`VideoTokenLayout`、block size、MindIE-SD
  依赖或 packed video shape。
- 强制：resolver 传入真实 `prefix_len`、`latent_shape=[t,h,w]` 和
  `used_len=prefix_len+t*h*w`；只裁掉 document-0 后的物理 padding，kernel 输出再补零回
  query shape。video rows 不再要求 128 整除；新 MindIE-SD 在空间重排后把不规则的
  真实 video suffix 提升到 always-kept segment，使余下 video 按 128-row block 稀疏。
  不能用人工 padding 替代，因为 `rf_v2` 不消费 padding mask，pad key 会污染 softmax。
- 边界：`sparsity<=0`、未到 `start_step`、skip layer、无/未声明 BSND layout、无
  video layout/无 `max_seqlen_q`、`prefix+t*h*w` 不闭合 document 0，或 video 少于
  32×128 rows 均保持 FlashAttention dense fallback；显式错 layout、causal 或 Ring>1
  仍 fail closed。非 8×8 空间网格的 residual 被 always-kept，因而 realized sparsity 低于
  nominal；潜空间 h/w 为 8 的倍数（输入高宽为 256 的倍数）仍是性能首选。
- 禁止：只因 `mindiesd` 可 import 就断言 irregular-tail 合同可用；当前 availability
  只检查 module 存在，没有 version/feature gate，旧 `rf_v2` 与新 planner 组合仍有风险。
- 验收：CPU plan 同时接受 128-aligned 与 irregular grid，并保持所有其他 fallback/
  rejection；真实 Ascend + updated MindIE-SD 用 irregular grid 对 dense reference。目标 NPU test
  仅以 `sparsity=0` 证明 protected-tail 几何下全 block 等价，不证明稀疏选择的质量、
  realized sparsity 或加速。^[PR #6000]

## DIFF-1k — 非等长 SP attention 必须保留 K/V mask 并走 mask-safe backend

- 触发：模型在 strict Ulysses/SP 中为 self-attention 或 cross-attention 增加 K/V padding mask，且 Q 与 K 的序列长度可能不同。
- 强制：保留完整逻辑 K/V mask，并以 `[B, 1, 1, K]` 语义传递；masked LTX attention 必须走支持该 mask 的 SDPA fallback，unmasked 请求才保留 native backend，不能修改通用 Ulysses 的 mask 语义来适配单一模型。
- 禁止：因为 cross-attention 的 Q/K 长度不同就丢弃 mask；把只匹配 query 长度的二维 mask 交给 Flash varlen；把 backend 的 `supports_attention_mask` 能力等同于支持任意 mask layout。
- 验收：CPU/mock 覆盖 masked self-attention、masked unequal-length cross-attention 与 unmasked path，分别断言 SDPA/native dispatch 和 mask shape；真实 SP 再以带 padding 的 LTX 输出对照未分片参考。^[PR #5500]

## DIFF-1n — cuDNN attention 的单 token 形状必须提前走 MATH

- 触发：修改 cuDNN diffusion attention dispatch，或引入可能出现单 token 的动态 Q/K 序列长度。
- 强制：当 query 或 key 的序列长度为 1 时，在进入 cuDNN-only context 前显式使用 `sdpa_kernel([SDPBackend.MATH])`；其他形状才使用显式 cuDNN，并保留符号 shape 被 cuDNN 拒绝时的运行时 fallback。
- 禁止：把单 token 形状交给 cuDNN 后等待 eager exception；用包含 FLASH/MATH 的 priority list 掩盖 backend 选择；因 Q/K 长度不同而丢弃已有 attention mask。
- 验收：CPU/mock 参数化覆盖 `(1,1)`、`(8,1)`、`(1,8)` 与 `(8,8)`，精确断言选择的 SDP backend；另覆盖 compile、masked unequal-length 与 unmasked native path，并说明真实 GPU 数值仍需独立验证。^[PR #6070]

## DIFF-1z — 混合 causal/full attention 必须经过共享 Attention 能力路径

- 触发：diffusion 模型包含文本 causal 行与 image/timestep full-attention 行的混合序列，或修改 `full_attn_spans`、attention mask 与高分辨率长序列 dispatch。
- 强制：通过 `vllm_omni.diffusion.attention.layer.Attention` 传递 `AttentionMetadata`；piecewise backend 消费连续的 `full_attn_spans`，不支持时才使用按请求构造并复用的 dense mask，且 mask 形状必须覆盖完整 text+image 序列。
- 禁止：在模型内直接调用 raw `scaled_dot_product_attention`，绕过 diffusion attention backend/configuration；把所有 full rows 当作任意离散 spans；在每个 denoise step 重建只依赖 `token_types` 的 SxS mask，或因 fallback 方便而关闭 backend 能力检查。
- 验收：CPU/mock 覆盖 contiguous full-span、piecewise path、dense fallback、batch mask shape 与 piecewise/dense 输出一致性；高分辨率请求另验证实际 backend 选择、显存边界和 attention mask 不被重复构造。^[PR #5194]

## DIFF-7a — 多控制 transfer attention 必须按控制独立计算并显式承担 Ulysses 复制成本

- 触发：修改 Cosmos3 transformer 的多控制 transfer attention、控制 token packing、控制权重传递或其 Ulysses/sequence-parallel 路径。
- 强制：多控制 attention 必须为每个 control 独立构造 `[text, control_i, target]` 的 K/V 序列；保留该 control 自己的输出，target 输出按已归一化的 control weights 加权后再拼回控制区与 target 区。control token size 与 weight 数量必须一一对应，所有 control range 必须为正且完整覆盖 packed control 区。该路径使用 `skip_sequence_parallel=True` 的专用 attention，multi-control 时不得执行 `gen_sp_prepare`/`gen_sp_gather`，以完整的 `[control_i | target]` 序列在每个 Ulysses rank 复制执行，并显式告警其不降低每-rank memory 或 latency；未提供权重时使用均匀相对权重。
- 禁止：把多个 control 直接拼成一个共享 attention 序列后让一个 control 污染其他 control 的输出；按 control token 数对拼接序列做 Ulysses 切分；只验证 output shape 就宣称 sequence parallel 为多控制 transfer 提供 per-rank 节省，或把一个控制的局部测试外推为多控制数值/性能 parity。
- 验收：CPU/mock 测试用至少两个 control 的不同 value 和非均匀权重断言 target 是加权结果、control 输出来自各自 pass，并覆盖 token-size/weight 长度及非法权重；带 Ulysses 的测试断言专用 attention、复制执行和 warning，真实多卡再与单卡 dense reference 对照并分别测量显存、延迟和输出质量。^[PR #5614]

## DIFF-8a — CFG 双分支与 TeaCache extractor 必须保持参数合同一致

- 触发：修改 diffusion transformer 的 `forward` 参数、TeaCache `extract_*_context` hook、CFG 正/负分支 kwargs 或 `guidance_scale > 1` 的执行路径。
- 强制：以被 hook 的实际 `forward` 签名作为参数合同；extractor 必须兼容真实调用的可选字段，CFG 正负分支必须传递全部 required conditioning kwargs，尤其是 `guidance`，并保持对应 tensor 的语义与形状一致。
- 禁止：只让正分支携带 extractor 所需参数；假设 negative branch 可以省略 `guidance`；用宽泛 `**kwargs` 或不启用 CFG 的测试掩盖 hook 与 model `forward` 的签名漂移。
- 验收：TeaCache 启用且 `guidance_scale > 1` 时分别覆盖 LongCat T2I 与 Edit 的正/负分支，断言 extractor 两次均收到 `guidance` 且不抛 `TypeError`；再以固定输入、seed 和 checkpoint 对照无缓存输出。^[PR #6181]
