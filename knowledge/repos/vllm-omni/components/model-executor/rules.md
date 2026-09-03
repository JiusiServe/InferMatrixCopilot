---
title: "Model Executor 规则"
created: 2026-07-10
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, model-executor]
sources: [vllm_omni/worker/gpu_model_runner.py, vllm_omni/worker/gpu_ar_model_runner.py, vllm_omni/platforms/interface.py, vllm_omni/platforms/musa/platform.py, vllm_omni/platforms/npu/worker/npu_ar_model_runner.py, vllm_omni/engine/stage_init_utils.py, vllm_omni/utils/mm_outputs.py, tests/worker/test_omni_gpu_model_runner.py, tests/worker/test_gpu_ar_model_runner.py, docs/design/feature/omni_async_output_materialization.md, vllm_omni/config/model.py, vllm_omni/config/stage_config.py, vllm_omni/config/omni_config.py, vllm_omni/engine/stage_runtime.py, vllm_omni/engine/stage_engine_startup.py, vllm_omni/experimental/fullduplex/, tests/e2e/features/fullduplex/, vllm_omni/model_executor/models/common/qwen3_code_predictor.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni.py, vllm_omni/model_executor/models/qwen3_tts/configuration_qwen3_tts.py, vllm_omni/diffusion/models/minimax_h3/encoder.py, vllm_omni/model_extras/registry.py, examples/offline_inference/text_to_image/text_to_image.py, examples/offline_inference/image_to_video/image_to_video.py, tests/diffusion/models/minimax_h3/test_minimax_h3_contract.py, tests/examples/offline_inference/test_image_task_prompts.py, tests/engine/test_arg_utils.py, "PR #3422", "PR #3642", "PR #4730", "PR #4958", "PR #5073", "PR #5074", "PR #5310", "PR #5610", "PR #5671", "PR #5777", "PR #5792", "PR #5824", "PR #5957", "PR #5976", "PR #6049", vllm_omni/engine/arg_utils.py, vllm_omni/model_executor/models/qwen3_omni/qwen3_omni_moe_thinker.py, vllm_omni/model_executor/models/qwen2_5_omni/qwen2_5_omni_thinker.py, vllm_omni/model_executor/models/dynin_omni/dynin_omni.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/worker/base.py, vllm_omni/worker/gpu_generation_model_runner.py, tests/model_executor/models/qwen3_omni/test_qwen3_omni_forward_contract.py, "claude-workflow-starter-private@09dca46", "PR #4795", "PR #5842", "vllm_omni/model_executor/stage_input_processors/nemotron_voicechat.py", "vllm_omni/model_executor/models/nemotron_voicechat/nemotron_voicechat_code2wav.py", "PR #5146", "PR #5068"]
---

# Model Executor 规则

## Direct 代码快速入口

- **EXEC-0a — PR 描述先选代码地图。** Direct review 先按 title/body 声明的 runner、stage、bridge、loader 或设备语义命中下表，再用 pinned changed files 验证真实模型 consumer；路径只负责范围反查。
- **EXEC-0b — 共享 producer 先于模型补丁。** 命中共享 runner、stage runtime 或 bridge producer 后立即沿 live consumer 审查；只有 producer 正确且问题只属于一个模型时才进入该模型 owner。

| PR 描述在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| strict stage config、known-fields/projection、service/stage 字段归属、runtime config | `strict-stage-config`：`EXEC-3a` | `vllm_omni/config/stage_config.py::{build_stage_runtime_overrides,_build_engine_args}` → `vllm_omni/config/omni_config.py::{_build_common_stage_config_kwargs,VllmOmniConfig.from_pipeline_config}` → 真实 startup consumer |
| runner `_preprocess`、逐请求 metadata、prefill/decode phase、batch preprocess、MTP | `runner-preprocess`：本页“Runner 到模型的预处理合同” | `vllm_omni/worker/gpu_model_runner.py::{OmniGPUModelRunner._maybe_run_batch_preprocess,_preprocess,_build_model_kwargs_extra,_talker_mtp_forward}` → `vllm_omni/model_executor/models/<命中模型>` consumer |
| stage TP/PP/DP、devices、replica、visible devices、worker 启动、容量 fail-fast | `stage-runtime`：本页“Stage 并行度和设备容量必须一起验收” | `vllm_omni/config/stage_config.py::build_stage_runtime_overrides` → `vllm_omni/engine/stage_runtime.py::{StageRuntime.initialize,StageRuntime._resolve_replica_physical_devices}` → `stage_engine_startup.py::{launch_stage_replica,get_headless_replica_devices}` |
| `runtime_info`、request RNG、batch compaction、跨 stage bridge/串线 | `bridge-batch`：`EXEC-1a`–`1c` | shared runner request state → stage input processor → model consumer |
| cross-stage embedding width、pre-projection buffer | `bridge-batch`：`EXEC-1d` | stage HF config → `get_inputs_embeds_size()` → `GPUARModelRunner.inputs_embeds` → model projection |
| loader dtype、只取 checkpoint config、避免整仓权重下载 | `loader-contract`：`EXEC-2a` | `vllm_omni/model_executor/model_loader/weight_utils.py::download_weights_from_hf_specific` → `vllm_omni/model_executor/models/<命中模型>` loader |
| fused projection、HF source shard 完整性、consumer 委托、packed TP | `loader-contract`：`EXEC-2b` | H3 text encoder fused owner；其他模型先确认目标 main 是否已有 fused parameter |
| async Omni output、background builder、D2H snapshot、connector drain/fallback | `async-output`：`EXEC-5a` | `worker/gpu_ar_model_runner.py::{_should_use_async_omni_output,OmniAsyncGPUModelRunnerOutput}` → platform runner → connector output |
| Talker-MTP FULL graph、平台 capture 能力、显式 opt-out | `mtp-graph`：`EXEC-4c` | `platforms/interface.py::supports_talker_mtp_graph_capture` → platform override → model `talker_mtp_graph_safe` → `OmniGPUModelRunner._init_talker_mtp` |
| `model_extras`、shared T2I/I2V example、canonical prompt envelope | `image-task-envelope`：`EXEC-6a` | `examples/offline_inference/{text_to_image/text_to_image.py,image_to_video/image_to_video.py}` → `model_extras/registry.py::{build_text_to_image_prompt,build_image_to_video_prompt}` → model pipeline validation |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次 model-executor 审查 | `EXEC-1a` |
| `strict-stage-config` | stage schema、projection、known fields | `EXEC-3a` |
| `bridge-batch` | runtime info、跨 stage payload、batch、request RNG | `EXEC-1a`–`EXEC-1i`，见 [跨 stage bridge 与 batch 合同](rules-bridge-batch.md) |
| `loader-contract` | dtype、checkpoint config 获取、loader、fused shard 拼装 | `EXEC-2a`, `EXEC-2b` |
| `async-output` | AR async output、snapshot/live state、平台与 guard/fallback | `EXEC-5a` |
| `mtp-graph` | Talker-MTP FULL graph、平台能力与 tri-state fallback | `EXEC-4c` |
| `image-task-envelope` | shared image task example 或 `model_extras` prompt builder | `EXEC-6a` |
| `author-routing` | 只供 Direct reviewer 导航，不作为 finding 规则 | `EXEC-0a`, `EXEC-0b` |

## 严格配置校验

### EXEC-3a — 严格配置校验不能靠扩大白名单

- 触发条件：新增或收紧 stage config、deploy YAML、CLI 到 runtime config 的未知字段校验，或者准备向 projection、`TypedDict`、known-fields 集合、compat/service allowlist 增加字段。
- 必须做：先冻结 PR 基线，逐个枚举相对基线新增的可接受字段；对每个字段写清公开 producer、入口归一化、唯一 canonical owner 和最终 runtime consumer。CLI/legacy 别名只允许在入口转换，转换后不得继续出现在核心 schema；service-only 字段必须交给 service owner，不能混入 stage runtime config。直接 constructor、结构化 YAML 和真实 startup builder 必须使用同一组最小正负样例核对。
- 禁止：不能因为严格校验开始报错，就把报错字段加入核心 dataclass、projection、known-fields 或专门白名单；不能接受字段后在分区时丢弃；不能为同一语义新增两个核心字段再补优先级；不能用“构造成功”“字段不在最终 payload”或只有测试 fixture 使用来证明字段必要。
- 验收：每个新增可接受字段都必须有 PR 前已存在或本次明确新增的真实 consumer，并有从公开入口到 consumer 的正向断言；无 consumer 或 owner 不在 stage runtime 的字段必须在入口报错；别名与 canonical 同时出现必须报冲突。最终 diff 中新增的 schema 字段数量应与 producer-consumer 表逐项一致。

### EXEC-3b — stage loader metadata 与 stateful chunk 能力必须一同到达 consumer

- 触发：新增 per-stage `model_subdir`/`tokenizer_subdir`、模型 architecture override，
  或模型在 async chunk 间保留执行状态。
- 强制：从 `PipelineConfig`/deploy 合并结果把 checkpoint/tokenizer 子目录和
  `retains_state_across_chunks` 传入最终 `OmniStageModelConfig`/runner；空的
  `model_arch` 表示使用 checkpoint 自带 architectures，而不是一个空 override。
  Stateful chunk 必须与 scheduler 的容量计数和 connector requeue 合同一起审查。
- 禁止：只在 legacy YAML 或 model helper 中记录子目录；用空字符串覆盖 checkpoint
  architecture；让 scheduler 看不到仍占用 runner slot 的 parked request。
- 验收：structured 与 legacy stage config 都能读回子目录/状态字段；Audex 等多子目录
  checkpoint 做 loader smoke；stateful async-chunk 测试证明容量上限、requeue 和 cleanup。

### EXEC-4a — full-duplex chunk metadata 必须按 span 隔离且可安全序列化

- 触发：`experimental/fullduplex` 修改 PCM/audio span、force-listen、rollback、
  resumable append、runtime-control 或 silence continuation。
- 强制：把 speech/PCM metadata 与 rollback 状态绑定到具体 span；resumable append 重新
  arm 所需 EOS 但不得重复 turn EOS；runtime-control 输出先转换 dataclass/enum 等为
  JSON-safe 值，并在等待后重新检查 session/request 是否仍然有效。
- 禁止：用上一 chunk 的 force-listen 或 speech marker 污染不规则下一 chunk；把 stale
  session 的 silence continuation 继续发送；直接把 Python runtime object 放进控制消息。
- 验收：覆盖不规则 PCM span、rollback、resumable append、stale continuation 和控制
  redaction；首批测试看 `tests/e2e/features/fullduplex/` 下的 input、runtime adapter
  boundary 与 runtime-control redaction。

### EXEC-4b — shared runner 必须保留 resolved model architecture 与 model-owned hooks

- 触发：模型 architecture override 为空、checkpoint 含多个子目录，或模型实现拥有
  native duplex/sampling policy。
- 强制：空 `model_arch` 回退到 checkpoint architectures；loader 先按 resolved
  architecture 解析 connector/checkpoint 子目录；共享 runner 只提供 typed rows 和
  hook seam，真正的 model-owned sampling/turn-boundary policy 由模型 consumer 执行。
- 禁止：用空 override 覆盖 checkpoint metadata；只按默认架构初始化 connector；用
  generic runner policy 替换 MiniCPM/Audex 等模型自己的 native policy。
- 验收：覆盖 blank override、多子目录 checkpoint、hook 调用顺序和 mixed-batch
  request-local metadata；初始化失败必须在 scheduler/worker 继续运行前暴露。

### EXEC-4c — Talker-MTP graph 能力必须保留 tri-state 语义

- 触发：修改 Talker-MTP 的 FULL graph wrapper、模型 `talker_mtp_graph_safe`、平台 graph
  capability，或把 talker 与其他 stage 共用同一层 wrapper。
- 强制：只有实际 Talker stage 从平台声明模型能力；runner 读取能力时保留三态：未声明
  `None` 回退到既有 `has_separate_talker`，显式 `True` 允许 wrapper，显式 `False` 即使存在
  separate talker 也必须阻止 wrapper。上述判断只控制 dedicated Talker-MTP FULL graph
  wrapper，不能跳过 MTP buffer 初始化或关闭该 stage 其余 compile/capture 路径。
- 禁止：用 `has_separate_talker or talker_mtp_graph_safe` 吃掉显式 `False`；把 platform
  默认支持误写成所有模型未声明时一律开启；因一个算子 capture 失败而全局切 eager。
- 验收：CPU runner 测试至少覆盖 explicit false、未声明且 separate talker、explicit true，
  以及无 separate talker 的非 Talker stage。MUSA 当前 override 为 false，因为其 stream
  capture 到 `torch.multinomial` 会报 `operation not permitted when stream is capturing`；
  其他平台沿接口默认 true，但仍受模型声明与 FULL graph mode 共同约束。^[PR #5671]

## Runner 到模型的预处理合同

- 触发条件：修改或排查 runner `_preprocess` 的逐请求 metadata 生产、phase 判定、normal/batched preprocess 选择、MTP 路由条件，或多模型共用的输入预处理合同。
- 主要 owner：先查 `vllm_omni/worker/gpu_model_runner.py` 的 `_preprocess` 和调度状态，再查 `vllm_omni/model_executor/models/` 中命中的 consumer。共享 producer 或路由错误不能只在某个模型内打补丁。
- 必须做：把每个字段的生产时点、Python 类型、逐行语义、normal/batched preprocess 入口和后续路由写成明确 contract；phase 必须来自 prompt progress 等真实调度状态，不能用当前 span 长度代替。
- 回归测试：最近 owner 是 `tests/worker/`。直接调用生产 `_preprocess`，在同一 mixed batch 中放一个应进入和一个不应进入该路由的逐行对照，断言 metadata、hook 调用和 embedding/code 等可观察结果。只在模型 helper 测试里手动喂 metadata，或把真正的后续 helper 整个 mock 掉，不能证明 runner contract。
- MTP 内部行为：只修改 `_talker_mtp_forward` 内部的采样参数、空 batch、output key、graph wrapper 或 generator 生命周期时，使用最近生产 owner 的针对性测试；只有它同时改变逐行 phase 或 `_preprocess` 路由时，才强制上述 mixed-batch 合同回归。
- 平台边界：查 GPU generation/AR runner 和 NPU 等平台是继承共享实现还是覆盖它；没有 live 继承或调用链证据时，不得声称所有平台合同已经一致。
- 文档与兼容：已向 out-of-tree 模型开放的字段必须从 model-contribution 入口可发现，并明确旧 runtime 和新 consumer 需要怎样配套升级；不能用某个 in-tree 模型的 fallback 充当公开合同。

## Async Omni output materialization

### EXEC-5a — snapshot、live drain 与 fallback 必须构成同一个 output-cycle 合同

- 触发：修改 `GPUARModelRunner` async output、background builder、D2H copy、connector
  output、model opt-in/postprocess，或 prefix cache/spec decode/routed-expert/platform guard。
- 强制：下一 decode step 会覆盖或 mutate 的 scheduler metadata、request mapping、token span
  和 CUDA output 必须先做 step-owned snapshot；可复用 tensor 要 clone，并由独立 stream、
  pinned host buffer 和 ready event 固定 D2H 生命周期。采样 token feedback 与下一步所需的
  model postprocess state 保持 eager。未 snapshot 的 connector signal 必须只有 background
  builder 一个 drain consumer；`get_output()` 必须 join builder 并传播 background exception。
- 禁止：把 live connector state 写进 snapshot 清单；让同步路径和 background path 重复 drain；
  把“CUDA/ROCm 已验证”写成不存在的 platform guard；在 prefix cache、speculative decode、
  routed-expert output 或非 eager stateful postprocess 下强开异步路径。
- 验收：覆盖 reusable buffer 被下一 step 覆盖、逐请求 snapshot 隔离、connector drain 次数/
  顺序、builder exception 和每个 compatibility guard 的 synchronous fallback。平台结论按真实
  runner 分开：CUDA/ROCm 已验证，XPU/MUSA 可能进入共享 GPU path 但未验证，Ascend NPU 的
  独立 runner 仍同步 materialize。 ^[PR #5610]

## Stage 并行度和设备容量必须一起验收

- 触发条件：修改或排查全局 CLI、per-stage override、deploy YAML、平台 overlay、stage 并行度、`runtime.devices`、设备映射或 worker 启动。
- 必须做：沿公开入口展开配置合并，记录每个 stage 最终生效的 TP、PP、DP 和其他会增加 local world size 的并行参数，以及解析后的设备列表；在创建底层 worker 前校验所需设备数不超过该 stage 的可见设备数。
- 禁止：不能只证明并行参数和设备参数各自解析正确；不能截断设备列表或用 fallback 继续；best-effort 的锁、清理、日志和观测代码不能吞掉配置、拓扑或容量错误。
- 验收：至少有一个从全局参数加 per-stage override 进入最终配置的负向测试。并行 world size 大于解析后设备数时，测试必须在 worker 创建前失败，并在错误中报告 stage、并行参数、所需设备数和实际设备列表；匹配的配置必须保留原有启动行为。

源码中已经存在校验、但实际日志仍越过它继续执行时，必须读完校验所在函数及 caller 的完整控制流，包括后续 `except`、fallback 和返回值。只有代码 diff 或运行环境证据排除控制流吞错后，才可以把原因留给版本或镜像不一致。

最终配置、设备容量、被绕过的校验和 worker 失败已经形成一条与用户日志一致的因果链时，根因即闭环，应先报告。只有版本差异会改变这条因果链或修复位置时才继续查 tag、commit 和历史 PR。

首次根因报告只需要四项：用户最终配置、runtime 实际设备、失效或被吞的前置校验、与日志一致的失败点。四项齐全就立即给出“结论 / 证据 / 未验证边界”；相关 warning、硬件排除、完整版本历史和扩展修复建议随后按需补充，不得延迟首次报告。

当 issue 已提供最终配置和失败堆栈、current source 可读时，先按 [架构职责锚点](architecture.md#当前源码职责锚点) 完成一轮窄调查，目标是在 owner 确定后两分钟内给出首次根因。超时仍未闭环时必须指出缺失证据，不能静默扩大到历史 commit、其他模型或环境猜测。

Stage 拓扑错误的最小充分源码证据只有三段：一处最终配置日志加全局/per-stage 合并函数；一处启动前容量校验及其完整异常控制流；一处与日志一致的 worker 失败点。三段一致即可决定“配置触发 + fail-fast 缺陷”的主要修复位置，不再为首次结论读取 config factory、模型 pipeline、完整 deploy、spawn 实现或 tag diff；只有三段之间发生冲突时才补这些文件。

## 跨 stage bridge 与 batch 合同

### EXEC-2a — loader 的 dtype 与 config 获取必须显式、最小化

- 触发：模型 loader 构造 text encoder、VAE、transformer 或只读取 checkpoint config。
- 强制：所有子模块显式接收目标 dtype；读取单个 config 使用精确文件/metadata 获取路径。
- 禁止：为读取 `config.json` 同步下载整套权重；依赖默认 fp32 后再靠下游 cast 修补。
- 验收：mock 下载层证明只请求目标 config，loader 测试断言各子模块 dtype；真实 smoke
  记录峰值显存和 dtype。Krea 2 的具体约束见
  [Krea 2 规则](../../models/krea2/rules.md)。 ^[PR #4730]

### EXEC-2b — fused shard 必须按 source 完整性与布局数值闭环

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

### EXEC-6a — shared image example 先建 canonical envelope，model-extra 只做特化变换

- 触发：修改 shared T2I/I2V example、`model_extras` prompt registry 或模型 prompt builder。
- 强制：task runner 先构造完整 canonical dict：T2I 含 `prompt`、`modalities=["image"]`；I2V
  另含 `modalities=["video"]` 与原样 `multi_modal_data`。只有 `negative_prompt is not None` 才写 key，
  因而显式空字符串必须保留。registry 接收该 dict；无 model-specific builder 时 identity-return，
  有 builder 时只翻译模型 token/template/mm kwargs。公共 online serving handler 不参与此离线 seam。
- 禁止：pipeline 已负责 validation/normalization 时复制 generic builder；让 registry 从零重建 task
  modality；用 truthiness 丢空 negative prompt；为每个模型复制 Python example。
- 验收：canonical builder 覆盖 omitted/empty/value negative prompt 与 PIL media identity；registry
  覆盖 Bagel、MammothModa2、Ming、VACE custom path及 unknown identity path；Cosmos3/LingBot
  pipeline tests继续拥有模型专属 validation。^[PR #6049]

### EXEC-7a — Omni 输出必须是扁平的 RequestOutput 子类

- 触发：修改 `OmniRequestOutput`、stage output wrapping、`omni.generate()` 返回对象或其 serving/offline 消费者。
- 强制：`OmniRequestOutput` 必须继承 vLLM `RequestOutput` 并将继承字段作为 dataclass 字段直接声明；stage 原始输出必须通过 `from_stage_output()` 显式复制 `prompt`、`prompt_token_ids`、`outputs`、`finished` 等生成内容，源对象为 `OmniRequestOutput` 时再复制 diffusion 内容；消费者直接读取扁平字段，列表归一化只在真实列表边界完成。
- 禁止：重新引入 `request_output` 嵌套字段、动态 pass-through property、修改 dataclass 生成的 `__init__` 或递归 `unwrap` 兼容层；不得在 serving、example 或工具代码中恢复 `output.request_output` 访问。
- 验收：用真实 `RequestOutput` 和 `OmniRequestOutput` 分别验证 factory 复制的 prompt、token、outputs、finished 及 images/trajectory 内容；覆盖文本、音频、图像和 pipeline stage 的直接字段消费，并确认未完成 stage 的 `finished` 不被包装过程改写。^[PR #5146]

### EXEC-8a — DiT Euler 采样循环必须只计算一次不变条件

- 触发：修改 GLM-TTS flow-matching DiT 的 Euler 采样循环、文本 embedding、RoPE、block-causal mask、CFG batch，或新增预计算输入参数。
- 强制：在每次 `_do_sample` 调用中只计算一次不随 timestep 或采样状态变化的 text embedding、RoPE、attention mask 和 CFG 双 batch 张量，并传入 DiT；同时保持 `seq_len`、设备、dtype 与 `forward()` 的合同一致，缺省参数仍保留原有调用行为。
- 禁止：在每个 Euler step 重复构造上述固定输入；让预计算 embedding 或 RoPE 在长度不匹配时静默继续；改变原有 mask device、模型 dtype 或 block-causal 语义；把 eager streaming 路径的优化结论外推为 CUDA-graph 路径或其他模型的通用结论。
- 验收：覆盖 CFG/non-CFG 和 block-causal streaming 路径，验证预计算输入的长度、设备、dtype 与采样序列匹配，并以数值/字节一致性、输出 shape 及 profiling 证明循环内不再重复执行固定计算；确认非 streaming CUDA-graph 和未提供预计算参数的旧调用仍正常。 ^[PR #5068]
