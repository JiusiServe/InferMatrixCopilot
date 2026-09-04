---
title: "MiniMax H3 缓存与任务生命周期规则"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5703", "PR #5720", "PR #5810", "PR #5837", "PR #5840", "PR #5853", "PR #5991", "PR #6476", "PR #6550", "PR #6666", "PR #6714", "PR #6909", vllm_omni/diffusion/models/minimax_h3/batched_packing.py, vllm_omni/diffusion/models/minimax_h3/fasth3.py, vllm_omni/diffusion/models/minimax_h3/lora.py, vllm_omni/diffusion/models/minimax_h3/minimax_h3_transformer.py, vllm_omni/diffusion/models/minimax_h3/npu/lora.py, vllm_omni/diffusion/models/minimax_h3/pipeline_minimax_h3.py, vllm_omni/diffusion/models/minimax_h3/quality_policy.py, vllm_omni/diffusion/models/minimax_h3/vae.py, vllm_omni/diffusion/cache/cachedit/runtime.py, vllm_omni/diffusion/sched/sigma_schedule.py, vllm_omni/diffusion/worker/diffusion_worker.py, vllm_omni/entrypoints/openai/video_api_utils.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/diffusion/models/minimax_h3/test_minimax_h3_fasth3.py, tests/diffusion/models/minimax_h3/test_minimax_h3_lora.py, tests/diffusion/models/minimax_h3/test_minimax_h3_native_lora.py, tests/diffusion/models/minimax_h3/test_minimax_h3_parallel.py, tests/diffusion/models/minimax_h3/test_minimax_h3_step_execution.py, tests/entrypoints/openai_api/test_video_api_utils.py]
confidence: high
---

# MiniMax H3 缓存与任务生命周期规则

`MMH3-2c`–`MMH3-2k`：conditioned VAE 的确定性、modular task 选择，以及 request 级
Cache-DiT、TeaCache、distilled sigma schedule 与 Turbo LoRA 的生命周期。触发信号见
[MiniMax H3 规则](rules.md) 的 Direct 代码快速入口；加载合同见
[加载规则](rules-loading.md)，媒体输入见 [媒体规则](rules-media.md)。

## MMH3-2c — conditioned VAE 的固定种子必须按实际设备隔离并恢复

- 触发：修改 H3 image/video reference 的 VAE encode、固定 keyframe seed、`fork_rng`、设备
  generator 或 accelerator backend 支持。
- 强制：`encode_image()`/`encode_video()` 在采样前暂时把 VAE 转成 FP32，在
  `torch.random.fork_rng` 同时传 `devices=...` 与 `device_type=parameter.device.type`，并在
  context 内播种 CPU default generator 与 active-device generator；退出时恢复 RNG state，
  在 `finally` 恢复原 dtype，image path 还必须恢复 `parallel_tiling`。这个 seed 是
  conditioned VAE 的固定内部 seed，不能描述成 request seed。
- 强制：`devices` 只决定保存/恢复哪些 device index，不能代替 `device_type` 选择 RNG module；
  目标 torch 版本省略后者会默认进入 CUDA。NPU 依赖 `torch_npu` 先注册 `torch.npu`，encode
  内的 `self.device_module` 则在同一 active device 上执行 `device(...)` 与 `manual_seed(...)`。
- 禁止：把 PR 文本中的 CUDA+MUSA allowlist 当成目标实现。目标代码实际以
  `parameter.device.type != "cpu"` 接纳已注册的 accelerator device module，并把真实 type
  交给 `fork_rng`；CPU 的
  `devices=[]` 仍保存/恢复 CPU RNG。实机证据覆盖 CUDA/MUSA，以及 PR #5837 报告的 Ascend
  NPU direct fork smoke 与一次双参考图 FL2VA serving 成功，不能外推 XPU 或 ROCm。也不能因
  `fork_rng` 最终恢复 state 就宣称并发安全：context 内仍会暂时改写 process-global CPU/device
  generator，重叠调用需要序列化或独立并发证明。
- 验收：同 seed 的 image/video condition latent 可重复，正常和 encode 异常后 CPU、目标设备
  RNG state、dtype 及 image tiling state 都恢复；CPU 与每个声称支持的 accelerator 分支分别
  覆盖，并加入重叠调用 fence。PR 中拟议的专用 VAE 单测按 review 被删除，目标 commit 没有
  新增测试；PR #5837 也只改两处参数，未提交 CPU/NPU 回归测试，其 NPU smoke、serving 结果
  与 CUDA 不变性说明只能作为外部证据，不能冒充持续回归覆盖。^[PR #5703] ^[PR #5837]

## MMH3-2d — modular H3 的 task selector 必须同步权重、能力与所有 DiT lifecycle

- 触发：修改 `modular_model_index.json`、`MiniMaxH3ModularPipeline`、`--task-type`、combined
  FL2VA/Ref2VA 服务、`_dit_modules` 或 shared text/VAE components。
- 强制：模型发现同时识别 `model_index.json` 与 `modular_model_index.json`，registry alias 与
  postprocess 都映射到同一 H3 pipeline。`auto/combined` 从 root 加载 FL2VA `transformer` 与
  Ref2VA `transformers_ref`，但共享 text encoder、video/audio VAE；单 task 只加载所需 DiT。
  request task 必须属于启动时 `supported_tasks`；combined 省略 task 时按无媒体→t2va、image-only
  →fl2va、video/audio→ref2va 推断，因此 image-only Ref2VA 必须显式给 task；Ref2VA-only
  省略 task 时保留 implicit ref2va。
- 强制：modular alias 复制 9-image/mixed-reference admission capability；所有基于
  `_dit_modules` 的 consumer（loader strictness、Cache-DiT enable/refresh/summary、LoRA/offload）
  遍历实际 DiT，不硬编码 `transformer`/`transformer_2`。共享 `--task-type` 放宽后，非 H3
  owner 仍 model-aware 校验；Qwen3-TTS 只接受既有三值。
- 缺口：目标 pin 的 modular metadata 虽修复 admission 字段，仍遗漏 canonical H3 的
  `attention_mask_free=True`。HF root 的两个 index 都解析成 modular alias，因此默认
  combined 服务在 Blackwell 不会自动选 TRTLLM，与 recipe 声明冲突；alias 必须校验全部能力
  字段 parity，不能只复制 review 点名的字段。
- 禁止：从 combined 注册推断双 DiT 性能已验证；recipe 最终只描述配置，没有 combined
  warm latency/throughput/output-parity qualification。也不能用单 DiT Cache-DiT 测试证明
  `transformers_ref` lifecycle。
- 验收：覆盖 local/Hub index discovery、snapshot allow-pattern、combined/单分区初始化、缺
  partition、task default/membership、modular admission、两 DiT cache lifecycle 与非法 TTS
  selector。PR body 的顺序 T2VA→Ref2VA 视频使用 `duration=2.0`，低于目标 pin 已生效的 4 秒
  下限，因此不能证明 final merge 的 combined 路径；148.27/158.67 GiB combined 与 86.27 GiB
  single-load 等数字来自缺硬件/协议/重复次数的 issue comment，不能作为容量保证。^[PR #5720]

## MMH3-2e — quality 映射只决定 request 的 Cache-DiT 目标

- 触发：修改公共 `quality` 值、H3 quality policy、startup cache adoption 或 denoise 前 prepare。
- 强制：公共层只接受 `None`、`lossless`、`high`，并保留 omitted 与 explicit lossless 的区别。
  对 request-scoped Cache-DiT，`lossless` 产生空 target；`high` 总是选择 model-owned conservative
  profile，即使启动时没有 cache backend；omitted 仅在启动配置为 Cache-DiT 时恢复 server generic
  profile，否则不安装 Cache-DiT。
  pipeline 必须在参数/任务/step 解析完成后、真实 denoise 紧邻之前 apply plan。
- 禁止：沿用 PR 早期描述，把无 startup cache 的 `high` 拒绝；让 unsupported quality 静默落入
  lossless；在 request 未显式提供 quality 时由 sync/streaming serving 覆盖 model default。recipe
  把同一组 quality 数字标为 4×H200，而 PR evidence 把它归于 4×L20X SP4；hardware provenance
  未统一前不得引用该表作为任一硬件的可靠 benchmark，更不能外推通用 speedup/quality。
- 验收：offline、chat、sync video、streaming video 都覆盖 omitted/lossless/high/非法值及显式字段
  传播；startup cache on/off × 三种 intent 验证 exact installation key，并断言 prepare 先于 diffuse。
  当前测试广泛覆盖 validation/routing/policy 和 mock 顺序，但真实 Cache-DiT transition 的并发、取消、
  failure rollback 仍缺证据；独立 reviewer 的单卡 B300 观察也显示 `high` 的质量/延迟与四卡表明显
  不同，只能支持 topology-dependent 边界。共享状态机与 batch 合同见
  [DIFF-2i–2j](../../components/diffusion/rules-component-lifecycle.md)。^[PR #5853]

## MMH3-2f — force-refresh hint 属于 active profile identity

- 触发：H3 request `extra_args` 使用 `force_refresh_step_hint` 或 `force_refresh_step_policy`。
- 强制：hint 是 1-based positive integer 且不超过 `num_inference_steps`，policy 只接受 once/repeat，
  省略 policy 默认 once；没有 active cache target 时两者都拒绝。用 dataclass replace 生成 request-local
  config，不修改 startup generic config；installation key 必须包含 hint+policy，因为 Cache-DiT 的
  incremental refresh 把 `None` 解释为保留旧 hint，变更或移除 hint 必须 reinstall hooks。
- 禁止：接受 bool 作为整数；只给 policy；跨 request 原地修改共享 config；same-key repeated request
  忘记重置 once hint，导致它只在首个 request 生效。
- 验收：边界 1/steps、0/越界/bool/非法 policy、无 target、hint add/change/remove、once/repeat 和
  repeated same-key request；断言每次 refresh 重建 hint context、generic config 不变，key 变化发生
  disable→enable。当前覆盖为 mock/config 合同，未证明不同 topology 下 hint 对质量/命中率的效果。
  ^[PR #5853]

## MMH3-2g — H3 TeaCache 只绑定 FL2VA 校准与 request state

- 触发：H3 选择 `tea_cache`、修改 extractor、polynomial coefficients、threshold 或 partition。
- 强制：只允许 `fl2va`/`combined`，Ref2VA-only fail fast；combined 只 hook FL2VA `transformer` 并
  告警 Ref2VA 不缓存。extractor 必须复刻 `_embed`、packed/SP block kwargs、final row selection 与
  video/audio update masks；缺/多 kwargs、空 blocks、shape/length 不闭合立即失败。runner 在每次
  generation 前 reset module-resident hook state；first step 强制计算，后续按累积距离计算或复用
  residual，目标 hook 没有 last-step 强制计算分支。
- 强制：H3 coefficients 只由 70 prompts、seed 42–111、256×448、107 frames、50 steps 的 3360
  adjacent pairs 校准；`TeaCacheConfig` 收到 `None` 时模型默认 0.17，自定义 coefficients/正 threshold
  可覆盖。但 public `AsyncOmniEngine._normalize_cache_config` 在省略 cache config 时仍先注入 0.2，
  因此 CLI/public omitted 路径没有获得 0.17；recipe 显式 0.17 不受影响。
- 禁止：把 FL2VA coefficients 用于 Ref2VA，或宣称 selector 已在 request 层强制互斥。目标 pin 中
  TeaCache 由 runner 持有；`quality=lossless` 只清除 Cache-DiT target、不会卸载 TeaCache，
  `quality=high` 还会尝试在同一 transformer 安装 Cache-DiT。修复或拒绝该组合前，TeaCache server
  不得用 request `quality` 承诺 lossless 或双 backend 安全。0.2 单 H100 A/B 虽约 1.20×，LPIPS
  0.3162 是显著视觉差异；0.17 在同 prompt 仅约 3% wall reduction、LPIPS 0.0134，均非通用保证。
  ^[PR #5840]
- 验收：CPU extractor tests 覆盖 native parity、packed kwargs、mask/SP 与错误路径；backend tests
  覆盖 partition/default/override。模型 E2E 仅两 steps 并检查输出 shape，未断言真实 cache hit；
  还必须从 public omitted config 断言最终 H3 threshold，不能只直接构造 backend；覆盖 TeaCache ×
  omitted/lossless/high，断言只存在一个 hook/backend 或明确拒绝。module state 若可交错还需并发隔离
  证明。单 H100 online/offline、
  Cache-DiT default/conservative 数据无多 prompt/repeats，不能升级为 gate。

## MMH3-2h — distilled sigma schedule 按 partition 所有且以区间计步

- 触发：H3 partition `model_index.json` 的 `_minimax_h3.base_schedule`、显式
  `num_inference_steps`、video/audio flow shift 或 combined FL2VA+Ref2VA。
- 强制：缺少 metadata key 或显式 null 都表示未蒸馏，保持旧
  `num_inference_steps or 50` 的 uniform-point 构造（默认 50 个点实际是 49 个 solver
  intervals）；explicit empty list 必须拒绝。调度至少两个有限点，严格
  从有限 `(0,1]` 首点递减到 0.0，并逐对验证相邻位置；FastH3 的首点是 `0.999`，不能被
  旧的 exact-1.0 假设拒绝。
- 强制：5 个 sigma boundaries 只有 4 个 denoise intervals；`num_inference_steps`、
  Cache-DiT quality policy 和请求验证均使用 `len(base_schedule)-1`，solver 仍接收
  完整 boundary list。用户省略 step 时自动采用 checkpoint 步数；显式值只有
  精确相等才接受，否则 `OmniClientError`。同一 continuous base positions 分别
  应用 video/audio shift（默认 12/3），不得改用单模态 integer timesteps。
- 强制：schedule 从各 partition metadata 分别读取；`t2va`/`fl2va` 选 FL2VA，
  `ref2va` 选 Ref2VA。distilled FL2VA 不得拖普通 Ref2VA 进 4-step。类级空 map
  是 partially constructed pipeline 的 legacy fallback，避免 `object.__new__`/dummy fixture
  读未初始化属性。
- 边界：共享 `DMD2SigmaSchedule` 在 `diffusion/sched` 定义，但此 pin 只有
  H3 消费；现有 `DMD2PipelineMixin` 仍是 scheduler-backed，用
  `DMD2EulerScheduler`/integer `denoising_timesteps`，本次未接入新 utility。不得由
  `[NPU]` title 推导 NPU 实机已验：无 platform/deploy/recipe 改动，PR hardware
  与 branch-head 也留空；附件视频只是 smoke，无数值 teacher/student quality gate。
- 共享 boundary/interval、metadata null/empty 与 shift 有限性合同见
  [DIFF-4j](../../components/diffusion/sigma-schedules.md#diff-4j-continuous-sigma-boundaries-不得与-scheduler-integer-timesteps-混同)。
- 验收：shared class 覆盖长度/端点/单调/非有限/shift≤0、缺 key 与空 key；
  H3 覆盖双 shift 精确值、combined partition 隔离、4-step 传入 solver/quality、
  matching/mismatched explicit step 和 legacy/partially-constructed fallback。仍缺真实 distilled
  checkpoint 的 CUDA/NPU E2E 与 teacher/student 质量阈值。^[PR #5991]

## MMH3-2n — FastH3 只接受精确 artifact，并将 VSA gate 在启动时一次性融合

- 触发：FastH3 `lora_path`、load-time fusion、four-step request 或 serving gate。
- 强制：只 claim `fastvideo-lora-v2`、`finetuned_model` 位于 `fastvideo/` 且 identity 含 `fasth3`
  的 exact FastH3 artifact；`base_model` 可缺省，声明时必须精确为 `MiniMaxAI/MiniMax-H3`。bundle
  root 与 claimed variant 都必须唯一，否则 fail closed；普通 FastVideo/PEFT/多 shard 交还 legacy
  dynamic LoRA，不可误认。
- 强制：声明的 low-rank/diff/`set_weight` tensor count 必须 numeric 且与实物一致；任何 unmapped、
  duplicate/unpaired factor、shape mismatch、extra/incomplete block 或 fused QKV/FC1 不支持的 full-rank
  delta 都失败。fusion 在 sharding 前完成：Diffusers Q/K/V 重排为 grouped native QKV，FC1 value-first
  重排为 gate-first，再加入 low-rank `B@A` 与 full-rank `diff`/`diff_b`。成功后只保留永久 fused sentinel；
  不能 request-switch，dynamic manager 的 list/add/remove/pin 安全返回空/false。
- 强制：FastH3 `vsa-datafree` artifact 的 `.set_weight` 必须精确映射到 main `transformer.` DiT 的
  `blocks.{0..49}.attn.to_gate_compress.weight`：pipeline 在 streaming weights 之前只为这 50 个 main-DiT
  attention 创建 zero-initialized gate projection；token refiner 保持 dense，base checkpoint 没有同名 parameter
  collision。`set_weight` 是 assign 不是 base-delta；加载后以实际 `transformer_loaded` 集合调用
  `validate_fully_applied`，保证每个 injected gate 唯一且确实被 transformer 消费。
- 强制：VSA artifact 的 main-DiT self attention resolved backend 必须为 `FASTVIDEO_VSA`（含 `self`
  per-role override）；dense substitute 不可运行该 sparse student。serving 只允许 `t2va`、无 per-request
  `lora`、exact `num_inference_steps=4`（五 boundaries/四 forwards）以及默认 video/audio shift `12/3`；
  拒绝 CPU/layerwise/DLO offload 与 Ref2VA。
- 禁止：不得混同 Turbo/native dynamic adapters，支持 VSA multi-adapter、Ref2VA/offload，或声称 quality
  parity、平台 portability 与通用性能收益；recipe/body 的旧 steps=5 不能覆盖 source 的 4。
- 验收：synthetic artifact 覆盖 identity/base/root/variant、metadata counts、mapping/pairs、QKV/FC1 reorder、
  full/low-rank delta、50 个 gate 的 mapping/unique/consumption、block/shape 与 unapplied patch failures；
  request matrix 覆盖 backend、task、steps、shifts、request LoRA 和各 offload gate。CPU tests 不替代真实
  artifact/hardware 质量或性能验证。^[PR #6714] ^[PR #6909]

## MMH3-2j — Turbo LoRA 只接受精确发布 artifact，并与 H3 task、sampling 和 offload lifecycle 共同门禁

- 触发：MiniMax-H3 LightX2V Turbo 的 dynamic LoRA loader、artifact conversion、request task/steps/flow shift，或与 CPU、standard layerwise、distributed layerwise offload (DLO) 的组合。
- 强制：仅识别声明文件名的 LightX2V Turbo v1.0 safetensors，且 metadata 必须为 `key_format=minimax-h3-diffusers`、rank/alpha `128/128`；任何未知 tensor、重复/不完整 A/B pair、unsupported target 或不精确的 global A/B shape 都在 binding 前失败。转换必须把 Diffusers token-refiner/main-block names 映射为 native H3 names，恢复 FC1 `[gate; up]` 行序为 model-owned packed weights，并通过 `stacked_params_mapping` 将独立 Q/K/V 接到 packed QKV。
- 强制：Turbo 仅在非零 scale 的实际 active recognized adapter 时限制请求；只支持 FL2VA/T2VA，要求五个 sigma points（四次 denoiser evaluation）、video `flow_shift=6` 与 audio `audio_flow_shift=3`。每次真实 load 都替换该 client ID 的 Turbo classification，避免 eviction 后同 ID generic adapter 被误分类。
- 强制：DLO + active Turbo 可用时，DLO 只 stream base blocks；manager 注入的 request-switchable A/B sidecars 必须留在 compute device，且任何因更大 LoRA rank 触发的 wrapper reallocation 后仍重放该 placement。固定 sidecar HBM 是此组合的预算，不得把它算作 base-block DLO lifecycle 或 collective payload。
- 禁止：将 exact Turbo artifact 的损坏 metadata 静默交给 generic fallback；将任意 H3 PEFT checkpoint、prefusion、multi-LoRA composition 或 Ref2VA 宣称为此功能支持；在 model-level CPU 或 standard layerwise offload 下激活 Turbo。不得为动态 sidecar 重建 DLO host shards、随每个 block/denoise step stream A/B，或让 LoRA 进入 DLO AllGather；没有 active LoRA 的 DLO 不得进入此 loader path。现有 HWR eligibility 仍拒绝 `lora_path`，AllGather 也不走该 BF16 HWR path，不能将 DLO+Turbo evidence 扩展为 HWR support。
- 验收：覆盖 file/metadata/alpha/target/pair/shape rejection、QKV and FC1 packing、scale-zero/generic same-ID/Ref2VA lifecycle、steps/shifts errors、CPU/standard-layerwise rejection，以及 DLO admission、resident A/B device placement 和 rank-driven reallocation 后的 placement；真实 artifact evidence 必须另绑定 exact checkpoint、task、topology、sampling 和 video/audio output。DP validation 至少以同 wave 的并发 request 覆盖所声称 DP topology；DLO no-AllGather/AllGather evidence 只证明对应 base-weight transport，sidecars 不参与 collective。PR #6550 报告的 0.911 GiB/TP2-rank 与 1.355 GiB/TP1-rank 只绑定 rank-128、312-target 的该 Turbo artifact，不是任意 adapter 的容量保证。转换后的 native mixed-rank PEFT artifact 不属于本 PR 的 supported contract；其 generic fallback rank/scale mismatch 是 post-merge follow-up，不可用本页的 Turbo success 证明安全。^[PR #6476] ^[PR #6550]

## MMH3-2k — H3 step execution 必须保持请求状态、attention 文档和 rank-0 prepare 隔离

- 触发：MiniMax H3 实现或修改 `prepare_encode`、`denoise_step`、`step_scheduler`、`post_decode`、`batched_packing.py`、step-mode attention metadata，或改变与 DLO、Cache-DiT、TeaCache、task-specific DiT 的组合。
- 强制：request 与 step path 复用 request-input、denoise-row prepare 与 unpack helper；每个 `StepRequestState` 保持一份 video rows、audio rows、audio sigma schedule、anchors、shape 和 output，只有同宽 video rows 交给 runner split。可融合时每个 request 向 `cu_seqlens` 贡献一个 real-row document 和一个独立的 64-row alignment-tail document，单 DiT forward 后按原 request rows 回拆；不同 task DiT、Ring 或任一 resolved backend 不支持 multi-document packed varlen 时逐 request forward。rank-0-only reference preparation 的异常必须在任何后续 broadcast 前由 H3-local helper 同步为同一异常。step mode 必须明确拒绝 `num_outputs_per_prompt>1`、distributed layerwise offload 和 `quality=high` request-scoped Cache-DiT；这些状态不能安全跨交错 step 或 packed forward 共享。
- 禁止：因 backend 名称为 `FLASH_ATTN`、平台默认或容量大于 1 就假设可合批；在多 document `cu_seqlens` 不被 backend 消费时去掉 mask；将不同宽度的 audio rows 混入 video batch；让 request-scoped Cache-DiT hooks、DLO resident window 或多输出 latent 跨 state 复用。不得把 H3-local broadcast 夸大为通用 runner 防护：target 的 `_dit_any_rank_failed()` 无法取得 DiT group 而退回 local flag，且 group-device 选择仍有 backend mismatch 风险。
- 验收：CPU contract 覆盖 request/step helper parity、two-request packed document boundaries、video/audio split/reassembly、mixed-DiT/Ring/unsupported-backend fallback、abort-after-inflight-step，及三个明确 rejection；TeaCache extractor 继续以 omitted `num_requests=1` 走 request-mode path。真实权重只可在固定 checkpoint、seed、task、backend、topology 下比较 single vs packed outputs；并发 step run 的 packing composition 会随 arrival timing 改变，PR 的 4×H100 结果已显示 step rerun 和 request-vs-step 都非 bitwise 等价。有限 CPU、H100/B300 observations 和 workload-specific throughput 都不是所有 backend、small request、确定性或 multi-rank failure synchronization 的证明。^[PR #5810]

## MMH3-2m — FlashGen native LoRA 必须保持 artifact、schedule 与 legacy-manager 边界

- 触发：FlashGen native artifact loading、H3 dynamic LoRA classification/binding、adapter schedule、packed QKV/FC1，或与 task、step execution、CPU/layerwise/DLO/HWR offload 的组合。
- 强制：只接受 exact v1.0 safetensors file；metadata 必须为 `key_format=minimax-h3-native`、`qkv_layout=grouped`、rank/alpha `64/64`、`tasks=t2va` 和五个 boundary 的四-interval `base_schedule`；target set 必须完整且精确（259 个），A/B pair、matrix shape、文件名或 metadata 任一不符均 fail closed。按 native module name 映射；grouped `qkv_proj` 先复用 H3 base-loader reorder 再拆 Q/K/V，`fc1` 拆 gate/up，二者复用 full-input A、以 slice-local B 绑定 packed layers。
- 强制：artifact format 而非 running platform 选择 native loader；loader 读取 CPU safetensors、无 `torch_npu` dispatch，但最终 binding/execution 仍由 selected runtime platform 负责。adapter 仅在 nonzero-scale active request 时覆盖 checkpoint schedule；T2VA request mode 可省略 steps 并从 adapter 取 4 intervals，explicit step 必须为 4；step execution 必须显式给 4，因为 admission 早于 adapter schedule。native adapter 不得与 checkpoint-pinned `base_schedule` 或 Ref2VA 组合；真实 reload/eviction 必须清掉 reused client ID 的 native classification/schedule。
- 强制：保持既有 legacy `DiffusionLoRAManager`，不引入 native-only manager、prefusion 或 multi-active composition。动态 A/B tensors 不参与 model-level CPU 或 standard layerwise weight lifecycle，因此二者拒绝；request-mode DLO 仅 stream base blocks、A/B 留 compute device。step execution 仍拒绝 DLO；HWR 的 `lora_path` eligibility 与 AllGather transport 未被本 PR 改变，不能据此宣称 HWR 或 LoRA-AllGather support。
- 禁止：把 NPU directory/训练来源解释为 NPU-only 或已验证跨平台性能；把 request-mode omission 扩展到 step execution；把 on-disk adapter size 作为 rank-local HBM bound；或以 unit/mocked binding、作者的单一硬件报告声称真实 artifact E2E、quality、throughput 或 other topology evidence。
- 验收：mock/synthetic artifact 覆盖 metadata/file/target/pair/shape/schedule rejection、grouped QKV 与 FC1 packing、legacy manager complete binding、active vs scale-zero、same ID reload/eviction、T2VA/Ref2VA、request/step count、offload gates 与 TP slice divisibility。PR 新增 native-LoRA unit contracts，未提交真实 release artifact 的 GPU/NPU E2E 或 independent quality/performance gate。^[PR #6666]

共享 component quantization、checkpoint mapping 与 quality evidence 见
[Diffusion rules](../../components/diffusion/rules.md)。

部署与容量证据见 [部署与证据规则](rules-deployment.md)；共享 diffusion 缓存机制见 [diffusion 规则](../../components/diffusion/rules.md)。
