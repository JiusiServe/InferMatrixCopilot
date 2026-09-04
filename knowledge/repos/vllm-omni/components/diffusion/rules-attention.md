---
title: "Diffusion attention 规则"
created: 2026-09-02
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, diffusion]
sources: ["PR #5543", "PR #5866", "PR #5887", "PR #5891", "PR #5897", "PR #5997", "PR #6000", "PR #6037", "PR #6518", "PR #6563", "PR #6724", "PR #6909", docs/design/feature/skip_softmax.md, docs/user_guide/diffusion/attention_backends.md, docs/user_guide/diffusion/attention_backends/trtllm.md, docs/user_guide/diffusion/attention_backends/fastvideo_vsa.md, docs/user_guide/diffusion/attention_backends/rainfusion.md, vllm_omni/config/omni_config.py, vllm_omni/config/stage_config.py, vllm_omni/diffusion/attention/backends/abstract.py, vllm_omni/diffusion/attention/backends/fastvideo_vsa.py, vllm_omni/diffusion/attention/backends/flash_attn.py, vllm_omni/diffusion/attention/backends/rainfusion_attn.py, vllm_omni/diffusion/attention/parallel/ulysses.py, vllm_omni/diffusion/diffusion_kv/paged_attention_adapter.py, vllm_omni/diffusion/models/minimax_h3/denoise_loop.py, vllm_omni/diffusion/models/minimax_h3/packed_sequence.py, vllm_omni/diffusion/data.py, vllm_omni/engine/arg_utils.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/cli/serve.py, vllm_omni/platforms/cuda/platform.py, vllm_omni/platforms/npu/platform.py, tests/config/test_omni_config.py, tests/diffusion/attention/test_fastvideo_vsa.py, tests/diffusion/attention/test_flash_attn.py, tests/diffusion/attention/test_attention_config.py, tests/diffusion/attention/test_piecewise_attn.py, tests/diffusion/attention/test_rainfusion_plan.py, tests/diffusion/attention/test_ulysses_uaa.py, tests/diffusion/diffusion_kv/test_paged_attention_adapter.py, tests/diffusion/models/minimax_h3/test_minimax_h3_packing.py, tests/diffusion/cache/test_teacache_extractors.py, "PR #5500", "vllm_omni/diffusion/models/ltx2/ltx2_transformer.py", "PR #6070", "vllm_omni/diffusion/attention/backends/cudnn_attn.py", "PR #5614", "PR #5194", "vllm_omni/diffusion/models/hidream_o1_image/hidream_o1_image_transformer.py", "vllm_omni/diffusion/models/hidream_o1_image/pipeline_hidream_o1_image.py", "PR #6181", "vllm_omni/diffusion/cache/teacache/extractors.py", "vllm_omni/diffusion/models/longcat_image/pipeline_longcat_image.py", "vllm_omni/diffusion/models/longcat_image/pipeline_longcat_image_edit.py"]
confidence: high
---

# Diffusion attention 规则

## DIFF-1ad — CUDA backend 选择必须区分显式承诺与自动回退

- 触发：修改 CUDA platform selector、`FLASH_ATTN`/`FLASHINFER_ATTN`/`CUDNN_ATTN`/TRTLLM、SP
  auto-pad 或 paged dispatch。
- 强制：显式 backend 必须运行或以可操作错误失败，auto 才可回退。Blackwell 的 `FLASH_ATTN` 仅可用
  `flash_attn.cute` FA4；显式缺 FA4 报错，auto 继续选择。cuDNN、FlashInfer、Sage、TRTLLM 都须按
  实际 head-size/所需 symbol 验证（SM10x TRTLLM probe 真正 API），不得以 import 代替能力。
- 强制：mask/SP pad 按已解析的 per-role `AttentionSpec` 能力判断，FlashInfer CuTe 不接受 custom
  mask；未知 `head_size=-1` 的 capability query 不得触发大小校验。formal paged 走 native backend，
  profiling 才可 dense/SDPA fallback。
- 禁止：显式 backend 在不兼容时静默替换为 MATH/SDPA/native；从相等维度猜 BHS/BSH layout，或把
  import 成功、CPU contract test、早期 B300 smoke 外推为跨硬件功能、质量或性能支持。
- 验收：覆盖 Blackwell FA4 缺失与可用、显式失败/auto fallback、CuTe mask、per-role SP pad、未知
  head sentinel、真实 wrapper/TRTLLM symbol 及无 FA4 的 paged path。^[PR #5543]

## DIFF-1ac — FastH3 VSA 必须保留 H3 packed document、tile 和 SP 合同

- 触发：修改 `FASTVIDEO_VSA` 的 MiniMax-H3 route、`vsa_h3_prefix_segments`/`VideoTokenLayout`、
  FastVideo 64-token kernel、compression gate，或 Ulysses attention all-to-all。
- 强制：H3 metadata 表示一个 packed `[text | condition | audio | video]` document；prefix segment
  RLE 的 sum 必须等于 target-video start，video grid 必须完整覆盖 query rows。prefix 以不跨 modality
  边界的 64-token tiles 切分，target video 以 `(4,4,4)` tiles 切分；prefix query dense，video query
  保留所有 prefix tiles 加 top-k video tiles。tile partition、non-pad index 与 untile 必须恢复原 row
  顺序；native SM100a path 只为 even block-partner requirement 增加 transport-only partner，并在返回前移除。
- 强制：compression gate 跟随 Q/K/V 的 Ulysses sequence-to-head all-to-all，使 local head shard 拥有
  完整 document；仅 local 或 pure Ulysses 可进入 H3 VSA，Ring 与 AllGather SP 必须在 admission 拒绝。
  H3 route 有意不走 generic `min_seq_len` 或 `disable_when_sp_active` fallback gates；不能把这些 knobs
  当作 H3 sparse admission 的实际保护。
- 禁止：让 prefix tile 跨 `[text|condition|audio]` boundary、把 video top-k 施加到 prefix keys、把
  odd partner 留给输出 untile，或把 Ring/AllGather partial document 交给 block-sparse kernel。不得将
  H3 route 的 CUDA error 之后的 dense fallback 描述为 sparse execution。
- 验收：测试覆盖 segment-pure prefix、3-D video tiling、prefix-dense/top-k map、odd partner、gate
  blending、packed-padding zero restore 和 pure-Ulysses gate resharing；真实 VSA 还须固定 checkpoint、
  kernel build、GPU、topology、request shape 与 top-k。PR #6909 的 B300 Triton 与独立 B200 native
  SM100a observations 仅限所报 8×GPU、USP8/Ring1、four-step、1344×768/24 FPS、top-k 64 workload，
  不构成广泛性能或 support claim；两条路均依赖外部 `fastvideo-kernel`。
- 证据缺口：multi-request layout error 会被 `fallback_on_error` 吞掉并运行 dense SDPA；尚无
  continuous-batching proof。^[PR #6909]

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

## DIFF-1m — TRTLLM packed-padding、Skip-Softmax 与 SAGE 必须保留 producer、SP 和 schedule 合同

- 触发：修改 `PackedPaddingMetadata`、TRTLLM packed `cu_seqlens`、`supports_packed_mask_free`、
  padded-output restore、SAGE/Skip-Softmax gate、calibration 或 multi-document varlen capability。
- 强制：`PackedPaddingMetadata` 只表示 single physical batch producer-owned `[real,pad]`：Q/KV host
  lengths 是 Python int、在 flattened bounds 内并与 max lengths/可选 `valid_kv_length` 相等；canonical
  two-element `int32` cu_seqlens 与 Q/K 同 device。该 path trim Q/K/V、zero-restore output，且不读
  `attn_mask`；generic complete cu_seqlens 仍是 genuine multi-document ragged varlen，paired trailing
  empty document 删除，二者不可混用。
- 强制：TRTLLM 仅在无 SP 或 pure Ulysses 运行；Ring+`skip_softmax` 报错、Ring 的 `quant` 不使用，
  AllGather-KV 拒绝。SAGE 和 Skip-Softmax 都须显式 opt-in。`threshold` 与 `target_sparsity` 互斥：
  kernel `lambda = threshold_scale_factor / max_kv_len`；direct path 的 factor 是
  `threshold * max_kv_len`，故 `lambda = threshold`；calibrated path 是
  `threshold_scale_factor = a * exp(b * target_sparsity)`，故
  `lambda = a * exp(b * target_sparsity) / max_kv_len`。请求 `target_sparsity` 而无 calibration
  metadata 必须失败，不得静默变 dense。
- 强制：Skip-Softmax 的 tile 只有当 tile 内每个 query row 都满足
  `exp(tile_max[i] - running_max[i]) < lambda` 时才跳过 Softmax/PV；`QK^T` 仍执行。正的
  `disabled_until_timestep` 以已归一化、递减的 `t` gate：`t > cutoff` dense、`t <= cutoff` 才可 skip；
  `0` 关闭 gate，缺 `t` 时保持 dense。MiniMax-H3 默认 flow shift `s=12` 的
  `t = s*u / (1 + (s - 1)*u)`，50 sigma points/49 denoiser forwards 下 cutoff `.99`/`.97`/`.95`
  分别留下 6/14/19 个 dense forwards；这些 counts 只属于该 schedule。
- 禁止：接受 nonempty TRTLLM `attn_mask`、把 shortcut 用作 arbitrary mask/multi-request layout，或把
  tail document 短于 `k_block_size` 的 dense fallback 当作 real-document SAGE gate 完成。不得将本
  docs-only PR #6724 外推为 runtime、数值、质量或性能证明。
- 验收：覆盖 malformed metadata、trim/zero restore、unequal Q/KV ragged、trailing empty、complete
  metadata+mask rejection、real-document SAGE minimum；再覆盖 SP admission、mutually-exclusive
  controls、missing calibration fail、tile-wide predicate、timestep gate/missing `t` 和 H3 flow-shift
  cutoff counts。^[PR #6542] ^[PR #6724]

## DIFF-1h — RainFusion irregular tail 由 MindIE-SD 保护，不能 padding 伪对齐

- 触发：修改 `RAINFUSION_ATTN`、`rf_v2`、`VideoTokenLayout`、block size、MindIE-SD
  依赖或 packed video shape。
- 强制：legacy resolver 传入真实 `prefix_len`、`latent_shape=[t,h,w]` 和
  `used_len=prefix_len+t*h*w`；Ref2VA multi-span resolver 改传 `used_len` 与按 physical start 排序的
  `video_spans=[{start, latent_shape}]`，将 interleaved text/image/audio 与 padding 保留 dense。只裁掉
  document-0 后的物理 padding，kernel 输出再补零回 query shape。video rows 不再要求 128 整除；新 MindIE-SD 在空间重排后把不规则的
  真实 video suffix 提升到 always-kept segment，使余下 video 按 128-row block 稀疏。
  不能用人工 padding 替代，因为 `rf_v2` 不消费 padding mask，pad key 会污染 softmax。
- 边界：`sparsity<=0`、未到 `start_step`、skip layer、无/未声明 BSND layout、无
  video layout/无 `max_seqlen_q`、`prefix+t*h*w` 不闭合 document 0，或 video 少于
  32×128 rows 均保持 FlashAttention dense fallback；显式错 layout、causal 或 Ring>1
  仍 fail closed。非 8×8 空间网格的 residual 被 always-kept，因而 realized sparsity 低于
  nominal；潜空间 h/w 为 8 的倍数（输入高宽为 256 的倍数）仍是性能首选。
- 边界：`end_step>0` 时，forward context 必须同时提供当前 `step_idx` 与 `total_denoise_steps`，
  并在 `step_idx >= total_denoise_steps-end_step` 的最后窗口回到 dense；默认 `end_step=0`。
  `precision` 只允许 `bf16|fp8|mix` 且默认 `bf16`；non-BF16 请求必须确认已安装 MindIE-SD 的
  `sparse_attention` 显式声明 `precision` 参数，否则 fail fast，不能让 `**kwargs` 静默吞掉配置。
- 禁止：只因 `mindiesd` 可 import 就断言 irregular-tail 或 multi-span 合同可用；availability 必须在
  模型构造前检查 `sparse_attention` 明确接受 `video_spans`，否则以可操作的 upgrade/FLASH_ATTN error
  fail closed，不能成功启动后在 T2VA/FL2VA/Ref2VA dispatch 才 TypeError，也不能静默尝试 legacy
  signature。该 feature check 不是版本 pin，仍不能据此推断任意 MindIE-SD build 的 kernel quality。
- 验收：CPU plan 同时接受 128-aligned 与 irregular grid，并保持所有其他 fallback/
  rejection；真实 Ascend + updated MindIE-SD 用 irregular grid 对 dense reference。目标 NPU test
  仅以 `sparsity=0` 证明 protected-tail 几何下全 block 等价，不证明稀疏选择的质量、
  realized sparsity 或加速。CPU tests 还应覆盖 multi-span 的 used length、geometry/role/overlap/bounds、
  total threshold 与 clip-boundary dense-context fallback；它们只证明 plan payload。PR #6518 review 的
  MindIE-SD `2661f83` field-name/layout check 与 4×B300 FLASH_ATTN regression 都不执行 RainFusion；
  真实 Ref2VA same-seed sparse quality 仍未覆盖。另覆盖 `end_step` 边界、zero-tail、precision enum
  normalization 与旧 MindIE-SD fail-fast；serial/homogeneous producer 必须发布并清理 progress trio。
  heterogeneous batch 的空 progress trio 在该目标没有独立 dense guard，不能据此声称安全 fallback。
  ^[PR #6000] ^[PR #6518] ^[PR #6037]

## DIFF-1k — 非等长 SP attention 必须保留 K/V mask 并走 mask-safe backend

- 触发：模型在 strict Ulysses/SP 中为 self-attention 或 cross-attention 增加 K/V padding mask，且 Q 与 K 的序列长度可能不同。
- 强制：保留完整逻辑 K/V mask，并以 `[B, 1, 1, K]` 语义传递；masked LTX attention 必须走支持该 mask 的 SDPA fallback，unmasked 请求才保留 native backend，不能修改通用 Ulysses 的 mask 语义来适配单一模型。
- 禁止：因为 cross-attention 的 Q/K 长度不同就丢弃 mask；把只匹配 query 长度的二维 mask 交给 Flash varlen；把 backend 的 `supports_attention_mask` 能力等同于支持任意 mask layout。
- 验收：CPU/mock 覆盖 masked self-attention、masked unequal-length cross-attention 与 unmasked path，分别断言 SDPA/native dispatch 和 mask shape；真实 SP 再以带 padding 的 LTX 输出对照未分片参考。^[PR #5500]

## DIFF-4v — FLASH_ATTN masked varlen packing 必须由 attention role 选择

- 触发：修改 diffusion `FLASH_ATTN` 的 masked-varlen unpad/pad 路径、`Attention` role 传递，或给 cross-attention 增加二维 key-padding mask。
- 强制：只有 self-attention 才可用同一 2D mask unpad Q/K/V；构造参数精确为 `role="cross"`
  时 mask 只 unpad K/V，Q 保持 dense，并按每个 batch 的完整 query length 构造
  `cu_seqlens_q`，输出直接 reshape 回 `[B, Q, ...]`。该提交没有扩展 namespaced
  `role_category="cross"` caller；LTX strict-SP 的 SDPA fallback 仍由 [DIFF-1k](#diff-1k-非等长-sp-attention-必须保留-kv-mask-并走-mask-safe-backend) 约束。
- 禁止：以 `Q == K` 推断 self-attention，或把 key-mask indices 用于 query gather/scatter；这会丢弃 query rows，且在 batch 大于一时可能令 query 对齐到另一样本的 K/V。
- 验收：CPU/mock 覆盖 self 与 `role="cross"` 的 masked varlen routing（包括 Q/K 等长），精确断言 cross 的 dense Q offsets 与 K/V offsets；GPU 将不同 batch valid-K lengths 的 cross output 与 SDPA 对照。^[PR #5866]

## DIFF-1n — cuDNN 单 token 仅限 auto MATH workaround

- 触发：修改 cuDNN dispatch 或动态 Q/K 长度。auto 的 Q/K=1 可在 cuDNN 前走 `SDPBackend.MATH`；
  显式 `CUDNN_ATTN` 必须拒绝该形状，不能静默换 backend。覆盖 `(1,1)`、`(8,1)`、`(1,8)`、`(8,8)`
  的 explicit/auto dispatch、compile 和 mask。^[PR #6070] ^[PR #5543]

## DIFF-1z — 混合 causal/full attention 必须经过共享 Attention 能力路径

- 触发：diffusion 模型包含文本 causal 行与 image/timestep full-attention 行的混合序列，或修改 `full_attn_spans`、attention mask 与高分辨率长序列 dispatch。
- 强制：通过 `vllm_omni.diffusion.attention.layer.Attention` 传递 `AttentionMetadata`；piecewise backend 消费连续的 `full_attn_spans`，不支持时才使用按请求构造并复用的 dense mask，且 mask 形状必须覆盖完整 text+image 序列。strict Ulysses paged path 必须保存/恢复 SP padding 并要求 `query_lens`、`image_mask`、`position_ids`；Ring、AllGather 和 non-strict Ulysses 必须 fail-closed，不能借 paged marker 落入其他 path。^[PR #6563]
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
