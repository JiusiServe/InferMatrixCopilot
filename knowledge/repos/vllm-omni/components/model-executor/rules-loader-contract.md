---
title: "loader 合同"
created: 2026-09-04
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, model-executor]
sources: ["PR #4730", "PR #4765", "PR #4958", "PR #5777", "PR #5824", vllm_omni/model_executor/model_loader/, "PR #5910", "PR #6119", "PR #5791", "vllm_omni/model_executor/models/common/qwen3_code_predictor.py", "vllm_omni/platforms/npu/_310p/patch/qwen3_tts.py", "PR #6138", "PR #6640", vllm_omni/engine/stage_init_utils.py, tests/engine/test_async_omni_engine_stage_init.py, tests/engine/test_stage_engine_args.py]
confidence: high
---

# loader 合同

`loader-contract` 审查组的 `EXEC-2a`–`EXEC-2c`：dtype 与 config 获取、fused shard 完整性、多模块 checkpoint 载入。触发条件与其余审查组见 [model-executor 共享规则](rules.md) 的 Direct 代码快速入口。

## EXEC-2a — loader 的 dtype 与 config 获取必须显式、最小化

- 触发：模型 loader 构造 text encoder、VAE、transformer 或只读取 checkpoint config。
- 强制：所有子模块显式接收目标 dtype；读取单个 config 使用精确文件/metadata 获取路径。
- 禁止：为读取 `config.json` 同步下载整套权重；依赖默认 fp32 后再靠下游 cast 修补。
- 验收：mock 下载层证明只请求目标 config，loader 测试断言各子模块 dtype；真实 smoke
  记录峰值显存和 dtype。Krea 2 的具体约束见
  [Krea 2 规则](../../models/krea2/rules.md)。 ^[PR #4730]

## EXEC-2b — fused shard 必须按 source 完整性与布局数值闭环

> H3 text encoder 当前有 fused QKV 与 gate/up owner；Qwen3 code predictor 仍使用分离
> projection，其 PR #4958 fusion 已由 PR #5777 回退，不能把 H3 现状外推给 Qwen。

- 触发：准备合并 q/k/v、gate/up 等 projection，修改 HF shard 映射、wrapper/talker
  loader、packed projection TP plan 或平台 override。
- 强制：weight 与可选 bias 都按 forward split 的同一顺序数值拼装；部分 shard 和
  整组 shard 缺失都硬失败。bookkeeping 必须按 source shard id；expected 集合从实际 fused
  owner 预置，才能捕获零 shard，不能以任一 source 命中的 target name 代表完整。所有声明
  同一 fused module 的 consumer 必须委托给共享 loader，wrapper 并恢复 returned loaded-name
  的模型前缀；平台 override 同步使用新
  fused 属性与共享 split helper。
- 禁止：不得用逐 tensor `default_weight_loader` 绕过 fused assembler；不得只记录 skipped
  shard 后让随机初始参数继续；不得只用 shape 或 returned-name 断言顺序正确。GQA
  下错误偏移仍可形状合法。plain packed `nn.Linear` 不得声明泛化 colwise TP；
  未有 TP-aware packing/loading/split 与 TP=2 测试时，TP plan 保持空。
- 验收：数值比较 fused 参数与 `cat([q,k,v])`/`cat([gate,up])`，覆盖 bias、
  部分/整组缺 shard、每个 consumer 的委托和前缀；以非等 q/KV width 证明 split 能识别
  GQA 错序。平台测试或静态 guard 证明不再引用已删除的 projection 属性。H3 eager text
  encoder 还须对任何未加载 plain retained parameter 在启动时硬失败；unknown checkpoint key
  可继续告警，因为它不会留下 model parameter 未初始化。^[PR #4958] ^[PR #5777] ^[PR #5824]

## EXEC-2c — 多模块 checkpoint 载入必须按配置块与参数集闭环

- 触发：模型 checkpoint 将主干 LM 与 DiT、patch encoder、vocoder、speaker encoder 等辅助模块拆分到不同配置块、文件或命名空间，或需要额外的 latent statistics 文件。
- 强制：从 checkpoint 配置块构造并校验各模块尺寸；单次遍历权重迭代器，按每个模块的精确 `state_dict` key 集合路由，并分别处理 `llm.model.*`、辅助模块和非 safetensors 统计文件；记录各模块实际加载数与期望数。
- 禁止：缺失配置块时静默套用其他 checkpoint 的默认值；以命中一个 target name 代表整组权重完整；让 speaker 权重落入 VAE catch-all；重复消费只能遍历一次的权重迭代器，或用默认初始化掩盖未加载参数。
- 验收：对已验证 checkpoint 逐模块核对加载计数、无 missing/extra tensor 和预期 dtype；对缺失配置块、架构常量不匹配、部分 shard 及错误命名空间执行 fail-fast 测试，并确认推理前就暴露错误。^[PR #4765]

相关执行流见 [model-executor architecture](architecture.md)；跨 stage 合同见 [bridge/batch 规则](rules-bridge-batch.md)。

## EXEC-2d — 全局量化配置与组件配置必须明确区分作用域

- 触发：修改共享 quantization factory、pipeline component 配置解析或 `quantization_config` 的全局/按组件语义。\n- 强制：普通 `QuantizationConfig` 必须原样解析到每个由 pipeline 构造且支持量化的组件；只有 `ComponentQuantizationConfig` 的显式 component map 可以缩小作用域。resolver、pipeline 和 quantizable layer 必须使用一致的 runtime prefix namespace，并仅让实际支持的 vLLM quantizable layer 消费配置。\n- 禁止：用 `hasattr(quant_config, "resolve")` 等隐式约定替代共享 resolver；因为组件属于同一模型就自动重写任意 `torch.nn` layer、embedding、norm、VAE 或其他不支持量化的模块；解析到单一组件后仍要求另一套 owner prefix。\n- 验收：CPU/mock 与真实构造测试分别覆盖 global config 同时命中 `transformer`/`text_encoder`、component map 只命中指定组件、未命中返回 `None`、最长 prefix 匹配及 unsupported layer 保持 checkpoint dtype；Flux2 与 MiniMax-H3 的 resolver 必须共同通过该合同。^[PR #5910]

## EXEC-2e — 模型路径解析必须统一本地、缓存与下载失败语义

- 触发：组件需要同时接受本地目录和 Hugging Face 模型引用，或新增配置、辅助权重、speaker extractor 等模型文件解析调用。
- 强制：本地目录必须直接返回；`allow_download=True` 必须经 `download_weights_from_hf_specific` 并转发 `allow_patterns`、`cache_dir`、`require_all=True`；缓存模式必须使用 Hugging Face `snapshot_download(..., local_files_only=True)`。解析失败必须向上抛出，由调用方决定是否降级；需要兼容 ModelScope 时应传入 `allow_download=True` 或先使用已解析的本地目录。
- 禁止：在调用方重新实现相反失败语义，绕过带锁和 ModelScope 支持的下载 helper，缓存未命中时静默返回原始 repo id，或为了单个辅助文件下载整个仓库。
- 验收：覆盖本地目录短路、缓存命中、缓存未命中抛错、下载 helper 路由、`allow_patterns`/`cache_dir` 转发及 ModelScope 解析路径；调用方测试必须证明其选择的失败和下载策略。 ^[PR #6119]

## EXEC-2f — fused code predictor 必须保持 source shard、wrapper 前缀与平台路径闭环

- 触发：共享 code predictor 将 q/k/v、gate/up 改为 plain `nn.Linear` fused projection，或修改 Qwen3-TTS、Qwen3-Omni、MOSS consumer、checkpoint loader、TP plan 或 NPU override。
- 强制：fused layout 必须分别保持 `[q,k,v]` 与 `[gate,up]` 行拼接；`CodePredictorBaseModel.load_weights` 按 layer、weight/bias 和 source shard 缓存后再拼装，并对部分或整组缺失硬失败。wrapper 必须归一化 `model.*`、`layers.*`、`codec_embedding.*`、`norm.*`、`rotary_emb.*` 以及 nested `talker.code_predictor.` 前缀后委托共享 loader，并恢复 returned loaded-name 前缀；MOSS local、Qwen3-Omni 与 NPU override 必须使用共享 loader、`qkv_proj` 和 `_split_qkv`。plain packed `nn.Linear` 在具备 TP-aware packing/loading/split 前保持 TP=1 与空 `base_model_tp_plan`。
- 禁止：用逐 tensor `default_weight_loader` 绕过 fused assembler；以命中一个 source shard 或 target name 代表整组完整；保留已删除的 `q_proj`/`k_proj`/`v_proj` 属性、让 body-direct 或 nested shards 绕过 wrapper 归一化，或对 packed `[q,k,v]`/`[gate,up]` layout 宣告泛化 colwise TP。
- 验收：用非等 q/KV width 数值核对 `cat([q,k,v])`、`cat([gate,up])` 及 bias，覆盖部分/整组缺 shard；覆盖 current、body-direct、nested 前缀和跨 shard incremental loading；断言 MOSS returned names、Qwen wrapper consumer、NPU mocked `prepare_qkv_weights`/forward 均走 fused 属性，并确认无 TP plan。 ^[PR #5791]

## EXEC-2g — 预计算 speaker profile 必须由模型回调完成校验

- 触发：共享 speaker profile 载入或校验逻辑新增模型专属字段、尺寸约束或新的 TTS consumer。
- 强制：`load_validated_profile_tensors` 只负责 tensor 读取与 `expected_model_type` 校验，并必须接收 `validate_profile(profile, tensors)` 回调；Qwen3-TTS 由 talker hidden size 提供 embedding 维度，VoxCPM2 由各自 validator 提供 profile 合同，adapter 与模型运行时复用同一校验器。
- 禁止：在共享 helper 内按 model type 分支选择校验、恢复可选的模型专属尺寸参数，或让未通过模型校验的 profile 进入 capability 列表和 prompt 路径。
- 验收：分别用 Qwen3-TTS 与 VoxCPM2 的合法、错误尺寸、错误元数据和错误 tensor profile 测试回调结果；确认 adapter 载入与模型运行时载入只保留通过校验的 profile，并覆盖 validator 错误时的跳过行为。^[PR #6138]

## EXEC-2h — stage subdir 必须从完整且同 revision 的 snapshot 解析

- 触发：stage `model_subdir`/`tokenizer_subdir`、Hub cache repair、`revision`/
  `tokenizer_revision`、`download_dir` 或 Run:AI object URI model reference。
- 强制：本地目录缺少声明的 subdir 时立即失败；Hub candidate 只有该 stage 所需的 config、loadable
  weight artifact 与 index 引用的全部 shards 完整时，才可改写为本地 subdir；partial cache 必须按同一
  repo/revision/download_dir 请求精确 subset 并复验。仅当 `tokenizer_subdir is not None` 且
  `tokenizer_revision != revision` 时单独解析 tokenizer snapshot；空 tokenizer subdir 表示 snapshot
  root，仍须验证 vocabulary artifact。`is_runai_obj_uri` 命中时保留 URI 与 joined subpath，跳过
  local/HF snapshot 推断，交给 upstream streamer。
- 禁止：以 `isdir`、config/index 文件存在或单 shard 证明 stage 完整；partial snapshot 静默变成本地
  model path；把显式 tokenizer revision 改回 model revision；把 Run:AI URI 当作本地/HF cache，或把
  generic stage resolver 描述成会补齐模型专有的全部 composite root components。
- 验收：覆盖 cold/partial/warm offline stage snapshot、index 缺 referenced shard、root tokenizer、
  split tokenizer revision、download failure fail-closed 和 Run:AI URI passthrough；模型专有 root
  completeness 另由 owner 验证。unit fixture 不证明真实 checkpoint load、音质、GPU E2E 或跨平台支持。
  ^[PR #6640]
