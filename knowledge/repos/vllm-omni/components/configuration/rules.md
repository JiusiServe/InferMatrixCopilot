---
title: "vLLM-Omni 配置开发门禁"
created: 2026-07-16
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, config]
sources: ["claude-workflow-starter-private@296ea45", "PR #4281", "PR #5031", "PR #5073", "PR #5671", "PR #5678", "zuiho-kai/claude-workflow-starter@c217fc6", vllm_omni/config/model.py, vllm_omni/config/stage_config.py, vllm_omni/config/config_factory.py, vllm_omni/config/omni_config.py, vllm_omni/config/composable_parallel/, vllm_omni/deploy/qwen3_omni_moe.yaml, vllm_omni/engine/stage_init_utils.py, tests/config/test_config_factory.py, tests/engine/test_arg_utils.py, tests/engine/test_stage_engine_args.py, "PR #4795", "PR #5842", "PR #6082", "PR #6156", "PR #5741", "PR #6068", "PR #4765", "PR #5666", "PR #5036", "PR #4222", "PR #5604", "PR #6293", "PR #6094", "vllm_omni/diffusion/data.py", "PR #6050", "PR #6322", "vllm_omni/config/pipeline_registry.py", "vllm_omni/diffusion/models/pi0_pipeline_config.py", "vllm_omni/diffusion/models/pi0/pipeline_pi0.py", "PR #5048", "PR #6458", "PR #6102", "PR #6308"]
---

# vLLM-Omni 配置开发门禁

只在修改 vLLM-Omni 的 config、deploy、pipeline、CLI 字段归属、alias、unknown-field 校验、flat→nested 归一化或默认 factory 时使用。第一次读这些规则时，先看
[config audit 说人话规则](config-audit-plain-language.md)；需要执行时再看
[config normalization parity](config-normalization-parity.md) 的矩阵和操作顺序。

## Direct 代码快速入口

- **VOMNI-CFG-0a — PR 描述先选代码地图。** Direct review 先用 PR title/body 声明的配置语义命中下表，再一次性用 pinned changed files 验证真实范围。描述只负责导航；冲突时以 live diff 和 consumer 为准。
- **VOMNI-CFG-0b — 命中函数后停止文档导航。** 打开命中行的第一批源码后，沿 live producer→consumer 审查；只有调用链跨 owner 或具体未知量阻塞时才增加一个 owner 或 guide。

| PR 描述在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| strict schema、unknown field、alias、flat→nested、structured/legacy/direct parity、typed projection | `strict-normalization`：`VOMNI-CFG-1a`–`1h` | `vllm_omni/config/stage_config.py::{build_stage_runtime_overrides,strip_parent_engine_args}` → `vllm_omni/config/omni_config.py::{_build_diffusion_config_projection,VllmOmniConfig.from_pipeline_config}` → `vllm_omni/engine/stage_init_utils.py::{build_engine_args_dict,build_engine_args_dict_from_omni_stage_config}` |
| deploy YAML、`base_config`、pipeline/stage overlay、headless/offline parity、最终逐 stage config | `deploy-topology`：`CONF-3a`, `CONF-4b`, `CONF-5a` | `vllm_omni/config/stage_config.py::{resolve_deploy_yaml,load_deploy_config,merge_pipeline_deploy,build_stage_runtime_overrides,_build_engine_args}` → `vllm_omni/config/config_factory.py::{StageConfigFactory.create_from_model,StageConfigFactory._merge_cli_overrides}` |
| composable strategy、axis、routing、load balancing、`strategy-config` | `composable-strategy`：`CONF-4a` | `vllm_omni/config/composable_parallel/strategy_loader.py::{parse_strategy_specs,load_strategy_specs}` → `translator.py::translate_strategy_stack` → `apply.py::apply_strategy_specs` → `config_factory.py::{StageConfigFactory._apply_strategy_specs,StageConfigFactory._reconcile_strategy_with_cli}` |
| `gpu_memory_utilization`、`kv_cache_memory_bytes`、多 stage 共卡、小显存 OOM | `deploy-memory`：`CONF-1a`, `CONF-2a` | `vllm_omni/config/stage_config.py::{build_stage_runtime_overrides,_build_engine_args}` → `vllm_omni/config/omni_config.py::{_build_runtime_config,_build_parallel_config,VllmOmniConfig.from_pipeline_config}` |
| multi-stage HF sub-config、stage quantization view、`hf_config_name` | `stage-model-config`：`VOMNI-CFG-1i` | pipeline stage declaration → `OmniModelConfig::{draw_hf_text_config,get_model_arch_config}` → vLLM quantization selection |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次配置审查 | `VOMNI-CFG-1b`, `VOMNI-CFG-1c` |
| `strict-normalization` | schema、alias、unknown field、structured/legacy/direct 路径 | `VOMNI-CFG-1a`, `VOMNI-CFG-1b`, `VOMNI-CFG-1c`, `VOMNI-CFG-1d`, `VOMNI-CFG-1e`, `VOMNI-CFG-1f`, `VOMNI-CFG-1g`, `VOMNI-CFG-1h` |
| `deploy-memory` | 显存预算、KV pin、多 stage 共卡 | `CONF-1a`, `CONF-2a` |
| `deploy-topology` | deploy、overlay、headless、topology wiring | `CONF-3a`–`3d`；`CONF-4b` 见 [并行拓扑合同](rules-parallel-topology.md)；`CONF-5a`–`5g` 见 [topology 与部署 profile](rules-topology-profiles.md) |
| `composable-strategy` | strategy axis、routing、load balancing | `CONF-4a`, `CONF-4c`–`4d`，见 [并行拓扑合同](rules-parallel-topology.md) |
| `stage-model-config` | HF nested config、stage-specific quantization/text config | `VOMNI-CFG-1i` |
| `author-routing` | 只供 Direct reviewer 导航，不作为 finding 规则 | `VOMNI-CFG-0a`, `VOMNI-CFG-0b` |

## 配置归一化与新老路径一致性

- **VOMNI-CFG-1a — 编码前冻结受影响合同。** 第一次业务代码修改前，只列当前 diff 会改变的入口和值状态，再加一个默认或相邻 control；不得做所有入口和值的笛卡尔积，也不得省略仍可调用的 legacy/direct 入口。
- **VOMNI-CFG-1b — 在第一位 consumer 前归一化。** 对 changed value 标出实际对象、copy/转换边界和第一位 consumer；归一化必须在该 consumer 之前完成。从 unknown 集合排除字段时，必须证明值进入明确 owner 且能从结果读回。
- **VOMNI-CFG-1c — 用同路径行为证据验收。** 受影响 legacy/structured 路径必须对相关 `null`、有效值、冲突值或可转换标量得到相同结果；至少一个非默认值走到第一位 consumer 和最终 config。helper 单测只能补充，最后必须在含 `vllm` 的兼容环境实跑目标测试。
- **VOMNI-CFG-1d — 兼容修复不能自动继承原 scope。** 新修复若引入新的 owner、来源、优先级、转换或模型/服务路由，或实现量级接近预估两倍，必须先重切片；禁止按入口堆特例和重复测试。多 PR RFC 只实现当前 PR 的 merge condition，后续切片或顺手修复的行为连同专属测试一起 `DELETE / DEFER`，不能因为已经写完或测试通过就继承为当前 scope。验收时每个生产代码 hunk 都应属于本轮目的，同一语义跨入口使用参数化矩阵并保留一个 control。
- **VOMNI-CFG-1e — 严格配置固定按“归一化、验 owner、分区、构造”执行。** deploy/stage/CLI overlay、alias 和 flat→nested 转换必须先产出一份规范化映射；mixed CLI/orchestrator namespace 只允许先路由已明确声明的非 stage scope，剩余 stage 候选必须以完整 key 集合进入 ownership validator。validator 不能同时改值、路由字段或先丢 `None`；校验通过后的规范化结果就是后续分区和构造唯一可消费的 owner artifact，禁止只调用 validator 却继续传 raw mapping，也禁止末端重新做 alias、default、precedence 或静默过滤。structured、legacy startup 和仍公开可调用的 direct factory 必须复用同一组 normalization/validation primitive。
- **VOMNI-CFG-1f — key 是否已知与 value 是否有效必须分开判定。** 缺失、已知字段的 `None`、显式 `False`/`0`、未知字段的 `None` 和两个非空来源冲突是五种不同状态：只有明确 owner 可以把已知 `None` 解释为 unset，`False`/`0` 不得被 truthiness merge 吃掉，未知 key 即使为 `None` 也必须按 strict contract 报错，alias 只在 legacy 与 canonical 都提供非 `None` 值时冲突。验收至少覆盖本轮会改变分支的这些状态，并断言错误或最终 consumer。
- **VOMNI-CFG-1g — rebase 或 schema 扩张后重新做配置归属审计。** 上游新增 dataclass 字段、默认 factory 参数、pipeline-wide 字段或 owner 集合变化时，把自动合并结果当作新的语义 diff；重新比较 base/head 的字段集合、序列化边界、默认-stage 透传和所有严格入口。默认 factory 的扩展字段应由 schema metadata 或单一声明集合驱动，禁止再加一份手写白名单。只有最新 base 上的真实 factory/legacy/structured 路径都保留合法非默认值并继续拒绝未知字段，才算 rebase 完成。
- **VOMNI-CFG-1h — typed engine projection 与生产 cutover 是两个 merge condition。**
  `build_engine_args_dict_from_omni_stage_config` 从 model/load/cache/scheduler/runtime/connector/
  parallel/quantization/diffusion typed owner 深拷贝非 `None` 字段，再与 legacy 共用 model/tokenizer
  precedence、connector injection、worker resolution、generation cache defaults 与 diffusion attention
  normalization；不允许增加 catch-all `engine_args`。但在 target `3d7fc3b9`，稳定入口
  `build_engine_args_dict` 仍明确委托 `build_legacy_engine_args_dict`，runtime/headless/diffusion startup
  仍传 legacy stage shape；`StageConfigFactory.create_from_model` 与
  `build_engine_args_dict_from_omni_stage_config` 均无 non-test caller，所以 typed path 是纯
  preparatory/test-only，不能声称生产已经“从 VllmOmniConfig 读取”。
  cutover 前须把 strategy/replica/startup-plan 一并改为 typed input，并用 live startup 测试证明。
  review 暴露的 typed-only defaults、unowned field 静默丢失、model/tokenizer subdir 与 omni-KV
  precedence 问题，final 以“保留 unset backend default、合并后按 execution type 验 owner、未知
  owner 拒绝、全 backend field 双向 effective parity”修正；新增字段后该 exhaustive census 必须
  重新运行，不能只维护几个 deferred-default 白名单。但 registry parity test 会跳过没有具体 HF
  config 就无法 `resolve_pipeline_config` 的 callable entry（当前包括 `qwen3_omni_moe`），并非字面
  exhaustive；cutover 前每种 resolver variant 都须补 concrete HF-config fixture。^[PR #5678]

### VOMNI-CFG-1i — multi-stage 模型必须显式选择同一份 stage HF config

- 触发：nested HF config 的模型新增/修改 `hf_config_name`、text config、quantization metadata、
  embedding width，或 pipeline stage 拆分。
- 强制：每个 stage 的 `hf_config_name` 必须同时驱动 `draw_hf_text_config()`、
  `get_model_arch_config()` 和 input-embedding width 查询，不能让三者各自回退到 root 的默认
  text config。top-level quantization config 继续走通用 vLLM resolver；stage sub-config 与
  ignore/exclude 规则共同决定实际 quantized modules，不增加 model-type string 特判。
- 禁止：因为 root 默认返回 Thinker 就省略 Talker/Code2Wav 声明；给每个模型复制 quantization
  resolver；仅断言 pipeline 字段存在而不追到 quant config、text hidden size 与 runner consumer。
- 验收：逐 stage 断言选中的 sub-config 与 architecture/quantization view；覆盖一个无 embedding
  override 的 AR control，证明 input width 回退到该 stage text hidden size。Qwen2.5-Omni 当前为
  Thinker=`thinker_config`、Talker=`talker_config`、Code2Wav=`thinker_config`，thinker-only 也用
  `thinker_config`。最终 diff 只测 stage 名与 Qwen3 无 override control，未直接单测 Qwen2.5
  Talker overridden-width runner path；该缺口见 [EXEC-1d](../model-executor/rules-bridge-batch.md#exec-1d-cross-stage-embedding-buffer-必须按-ingress-width-分配)。^[PR #5073]

## 部署配置与资源预算

只有 `CONF-数字字母` 是本节可审计规则 ID。

### VOMNI-CFG-1j — hybrid-Mamba stage 的 SSM cache dtype 必须贯穿 typed projection

- 触发：hybrid-Mamba stage 新增 SSM cache dtype，或同一模型提供普通与 async-chunk deploy 配置。
- 强制：把 `mamba_ssm_cache_dtype` 同时声明在 typed shared/stage config 与最终 deploy stage，并投影到 vLLM `CacheConfig`；模型 `dtype` 与 SSM state dtype 分开验收，Nemotron thinker 默认保持 `float32`。
- 禁止：只在 YAML 注释或模型内部设置 cache dtype；用 stage 的整体 `dtype` 替代 SSM state dtype；只验证 dataclass 能构造而不验证最终 runtime consumer。
- 验收：从 deploy/structured/legacy 入口读取非默认值，断言 sync 与 async thinker 的最终 stage config 和 vLLM cache consumer 均得到 `mamba_ssm_cache_dtype=float32`，并覆盖 bf16 模型、fp32 SSM state 的组合。
^[PR #5842]

### VOMNI-CFG-1k — 模型专用 attention 子配置必须贯穿 deploy 与 typed projection

- 触发：模型 deploy profile 需要通过 vLLM 顶层 attention backend 下的 `attention_config` 控制具体 decode kernel，或新增该嵌套字段并要求 structured、legacy、typed 路径保持一致。
- 强制：将 `attention_config` 纳入 `_ModelEngineOverrides` 与 `OmniStageModelConfig`，确保它从 deploy profile 投影到最终 stage engine args。Higgs 的三个 profile 必须在 Stage 0 同时设置 `attention_backend: FLASHINFER` 与 `attention_config.use_trtllm_attention: false`，Stage 1 保持不变。
- 禁止：把 `FLASHINFER` 视为原生 FlashInfer decode 的保证；依据八个 codebook 推断 attention 为 `q_len=8`；只修改一个 Higgs profile；或把 SM90/XQA capability 通过误认为 BF16 工作负载的性能结论。
- 验收：配置 schema、structured/legacy projection 测试均能读回 `{"use_trtllm_attention": false}`；解析三个 Higgs YAML 并断言 Stage 0 的 backend 与 nested pin 一致，最终日志为 `flashinfer-native`，并用同一栈 A/B 验证 TTFP/RTF 回到原生 FlashInfer 的范围。 ^[PR #6068]

### VOMNI-CFG-1l — upstream 配置复用必须保持 structured 边界与生命周期安全

- 触发：修改 `VllmOmniConfig` 的 structured stage config、复用 upstream `LoadConfig`/`CacheConfig`/`SchedulerConfig`/`ParallelConfig`，或新增 `CompilationConfig`、`ProfilerConfig` 等 upstream value object 字段。
- 强制：只有语义、配置归属、生命周期和 EngineArgs projection 均一致时才复用 upstream contract；继承的公开 structured config 必须 keyword-only，`stage.compilation_config` 与 `stage.profiler_config` 使用具体 upstream 类型并在构造期物化 mapping；保留 Omni 自有字段、延迟的 model/platform/rank/port/backend 初始化和显式 projection 边界。
- 禁止：用字段同名替代语义与 owner 审计；让 positional constructor 因 upstream 字段重排而静默改变含义；把继承字段的默认值当作显式 engine input；在 head process 执行终态初始化，或让 quantization 等未审计边界随 upstream contract 自动扩张。
- 验收：覆盖 keyword-only 签名与 positional rejection、mapping 到具体 upstream object、预构造 object 的类型保留、scheduler/parallel 传输安全 derived fields 及 msgpack/asdict registration；用非默认字段证明最终 EngineArgs projection，且默认值不泄漏、未归属字段明确失败，legacy 与 structured 结果保持一致。 ^[PR #6050]

### VOMNI-CFG-1m — 模型专用 stage 开关必须经 typed projection 且默认关闭

- 触发：为某一模型新增控制推理行为的 stage/deploy 字段，并让 deploy、CLI、structured 或 direct factory 可设置。
- 强制：把字段放在 `StageDeployConfig`、`OmniEngineArgs`、`OmniModelConfig`/`OmniStageModelConfig` 与 `_ModelEngineOverrides` 的同一 canonical projection；默认关闭（本例 `silence_ban_frames=0`），从最终 stage config 传到唯一模型 consumer，并同步更新 structured/legacy known-field inventory。
- 禁止：用未注册 env var 或模型初始化时自行读取绕过配置 owner；只在 YAML/dataclass 声明但在 engine args 或最终 stage 丢失；把模型专用字段变成所有 talker 的通用行为，或把 absent 当成显式启用。
- 验收：用 direct、structured、legacy 入口的非默认值追到最终 stage config 和真实模型 consumer；断言默认值保持关闭、其他模型不产生副作用，并覆盖字段集合与 projection parity。^[PR #5048]

### VOMNI-CFG-1n — diffusion backend 的 omitted 语义必须留给运行时解析

- 触发：修改 `distributed_executor_backend` 的默认值、配置 projection、Async stage 参数透传或 diffusion executor 选择逻辑。
- 强制：省略值必须以 `None` 贯穿 `OmniDiffusionConfig`、`_DiffusionConfigProjection` 和 async stage config，由 `DiffusionExecutor.get_class()` 按 `num_gpus` 解析为单 GPU 的 `uni`、多 GPU 的 `mp`；显式 `mp` 或 `uni` 必须保持调用方选择。
- 禁止：在配置 projection 或 `AsyncOmniEngine` 中把省略值预先改成 `"mp"`，把 `None` 当作显式 backend，或用 truthiness 合并吞掉显式 backend；不能以文档或原始 YAML 值代替最终 stage config 的传播证明。
- 验收：direct、structured 和 async 路径均断言 omitted 值在最终 stage config 仍为 `None`；覆盖单 GPU→`UniProcDiffusionExecutor`、多 GPU→`MultiprocDiffusionExecutor`、显式 `mp` 和显式 `uni`，并确认已 pin `mp` 的 deploy 配置不变。 ^[PR #6308]

### CONF-1a — 多 stage 共卡时 diffusion stage 必须显式设 gpu_memory_utilization

- 触发：多 stage 模型 stage 共卡时，分布式测试在模型加载期 CUDA OOM。
- 强制：检查并为所有 stage 显式设置最终展开后的显存预算；diffusion stage 内部可能
  同时加载 diffusion 模型与 LLM，不能沿用单 stage 默认比例。
- 禁止：只修改生成后的 CI YAML 而不改源模板；把单个 stage 的默认值当作全卡预算。
- 验收：源模板和生成配置一致，逐 stage 展开值之和不超过卡容量，并运行对应共享显存
  connector 测试。

### CONF-2a — 小显存机型对 KV 外分配模型 pin kv_cache_memory_bytes，不搞比例棘轮

- 触发：小显存 GPU 上 prefill 完成、decode 静默后被 OOM/信号终止，且模型在 vLLM
  KV-cache 记账之外还有 solver、VAE 或 diffusion 分配。
- 强制：先按 `max_num_seqs × max_model_len` 计算并固定 `kv_cache_memory_bytes`，再把
  剩余显存留给 KV 外路径；若仍 OOM，依次核对 pin 是否被 rebase 丢失、权重/激活基线、
  `max_num_seqs`、batched VAE 与 KV pin。
- 禁止：继续按轮次“顺手减 0.05” `gpu_memory_utilization`；显式 KV pin 后该比例不再
  决定 KV 大小。
- 验收：记录 pin、并发、长度与峰值，真实 decode 路径完成；任何吞吐交换都单独测量。

### CONF-2b — paged_scheduler 的 KV sizing 字段必须归一化并保持 dense_legacy 惰性

- 触发：为 diffusion stage 增加或修改 `kv_cache_memory_bytes`、`gpu_memory_utilization`、`max_num_batched_tokens`、`max_model_len`，或改变 `dense_legacy` 与 `paged_scheduler` 的配置投影。
- 强制：这些字段必须经同一 diffusion owner 归一化；只有 `paged_scheduler` 才能传入 native `VllmConfig` 的 cache/scheduler 配置。正值 `kv_cache_memory_bytes` 固定 KV 预算，`None` 或 `0` 使用自动 sizing；`max_model_len=-1` 必须保留 native auto-fit sentinel，同时为 Scheduler 解析出正的 admission bound。`kv_cache_memory_bytes` 不得为负，`gpu_memory_utilization` 必须在 `(0,1]`，`max_num_batched_tokens` 必须为正，`max_model_len` 必须为正或 `-1`。
- 禁止：让 `dense_legacy` 因这些字段改变既有 pipeline parallel、cache 或 scheduler 配置；用 truthiness 把 `0` 误判为非法或显式 KV pin；在末端静默丢弃非默认值，或把文本 encoder 的长度字段未经模型语义确认当作 DiT KV 上限。
- 验收：structured、legacy 和 direct 配置路径覆盖默认、非默认、非法值与显式 `0`；paged 路径断言字段进入 native cache/scheduler consumer，`-1` 触发 auto-fit；dense 路径断言原有并行、显存和 token budget 保持不变。 ^[PR #6094]

### CONF-2c — paged_scheduler 的请求行上限必须是正整数且贯穿配置投影

- 触发：启用 `paged_scheduler`，或修改 diffusion KV 的请求行容量、native metadata builder 和 BlockTables 初始化。
- 强制：`diffusion_kv_max_rows_per_request` 必须是严格的正整数，并在 `OmniDiffusionConfig` 与 `_DiffusionConfigProjection` 中统一校验；`paged_scheduler` 必须显式设置该字段，Worker 用它把一个 public request 的 sequence/context rows 容量传入 native cache 初始化。
- 禁止：接受缺失、`0`、负数、`bool` 或浮点行上限；用 truthiness 合并吞掉显式值；让 `dense_legacy` 因该字段创建 native paged KV，或把 CUDA 平台限制写进通用配置校验。
- 验收：direct、structured 与 deploy/config projection 分别覆盖缺省、正值和非法值，断言 paged mode 的最终 Worker/native consumer 读取行上限，dense mode 保持原有行为，并覆盖平台无关的配置构造。^[PR #6102]

### CONF-3a — 争议以展开后的最终配置为准

- 触发：CLI、deploy YAML、`base_config` overlay、platform 覆盖、per-stage override
  或 `engine_extras` 各层说法不一致。
- 强制：以 `resolve_deploy_yaml → load_deploy_config → merge_pipeline_deploy →
  build_stage_runtime_overrides` 展开后的最终逐 stage 配置为唯一事实，逐字段打印核对。
  overlay 中的显式 `null` 也是有语义的值：例如 MUSA Qwen3-Omni profile 在 Talker 与
  Code2Wav 用 `hf_overrides.quantization_config: null` 清除 checkpoint root 的 ModelOpt
  metadata，避免 BF16 audio stage 被自动识别为量化；Thinker 与非 MUSA base 保持不变。
- 禁止：拿某一层 YAML 原文当生效值；用默认值脑补缺失字段。
- 验收：争议字段在最终逐 stage 对象中可读回，并与第一位 consumer 一致；平台 overlay
  必须同时断言受影响 stage 和未覆盖 control，不能只验证 YAML 原文。^[PR #5671]

### CONF-3b — 显式 deploy YAML 统一经 `deploy_config` 解析

- 触发：修改 `Omni`、`AsyncOmni`、`OmniEngineArgs`、orchestrator 参数或阶段解析链中的显式 YAML 配置入口。
- 强制：将 `deploy_config` 作为唯一显式 deploy YAML 入口；未提供时走模型默认配置解析，并让 CLI、headless、offline、runner 和测试调用方使用同一字段，直到最终逐 stage 配置可读回。
- 禁止：在该解析链中恢复 `stage_configs_path` 字段、双路径互斥判断、格式探测或 legacy `stage_args` 直接加载分支；不得让旧参数静默改变最终配置。
- 验收：覆盖显式 `deploy_config`、未提供配置时的模型默认回退，以及标准/headless/offline/runner 传播路径，断言最终 stage config 一致，并确认公开参数与内部 args 不再包含 `stage_configs_path`。 ^[PR #5741]

### CONF-3c — 模型专用 deploy profile 必须真正自动生效

- 触发：新增带模型专用 side-path 或多模态输出标记的 AR pipeline，并同时提供默认 deploy YAML。
- 强制：让 model config、architecture registry、pipeline registry 与 `default_deploy_config_name` 指向同一模型；对 dots.tts 保持 `enforce_eager: true` 与 `enable_prefix_caching: false`，并从未显式传入 deploy 配置的真实 `Omni` 初始化中核对最终逐 stage 值；在 prefix-cache merge 尚未保留 `sparse_audio` 前，不得移除该 pin。
- 禁止：以 YAML 文件存在或 pipeline key 存在推断默认配置已经自动加载；只验证原始 YAML 而跳过最终 stage config；覆盖 `enable_prefix_caching` 后仍宣称 dots.tts 输出合同不变。
- 验收：用 HF `model_type=dots_tts` 的无显式配置启动路径断言 architecture、pipeline、默认 deploy 文件和最终 flags 一致，并完成超过一个 160 ms patch 的离线生成，确认没有 prefix-cache 导致的单 patch 截断。^[PR #4765]

### CONF-3d — checkpoint 身份与模型架构路由必须分层闭合

- 触发：checkpoint 的 `config.json` 自报为上游 backbone，但 Omni 需要独立的 model architecture、pipeline 和默认 deploy 配置时。
- 强制：让 model registry、pipeline registry、`model_arch`、`default_deploy_config_name` 与 deploy stage 的 `hf_overrides.architectures` 闭合指向同一模型；保留 backbone 的 `model_type`，并让无显式配置的入口解析打包的 deploy YAML。
- 禁止：只注册 pipeline 或放置 YAML 就依赖 `model_type` 推断；用 `hf_overrides.model_type` 替代 stage architecture 路由；要求离线入口额外传参来弥补默认配置未接通。
- 验收：真实无显式 deploy 配置的初始化能读回最终 pipeline 与 architecture，backbone `get_text_config()` 仍解析为原模型类型，并覆盖 registry、默认 YAML 与最终 stage config 的一致性。 ^[PR #5666]

### CONF-3e — MiniCPM-o 4.5 Stage 1 默认采样参数必须与模型语义一致

- 触发：修改 `minicpmo_4_5.yaml`、`minicpmo_4_5_2gpu.yaml`、`minicpmo_4_5_3gpu.yaml` 或 `minicpmo_4_5_8x4090.yaml` 的 Stage 1 Talker 默认采样参数。
- 强制：四份 profile 的 Stage 1 默认值保持一致：`temperature=0.8`、`top_p=0.85`、`top_k=25`、`repetition_penalty=1.05`、`min_tokens=50`、`max_tokens=4096`；duplex overlay 可按 `generate_chunk` 合同将 `min_tokens` 设为 `0`，而 Talker 离线逻辑仍独立限制为 2048 或剩余上下文。
- 禁止：只更新一个 profile；把旧的 whole-stream penalty 值 `1.02` 沿用到 16-frame frequency penalty；将 Sampler ceiling `4096` 解释为离线 Talker 的实际生成预算；把 `min_p`、`win_size` 或 `tau_r` 当作已由上游 `gen_logits()` 消费的必需字段。
- 验收：展开四份 MiniCPM-o 4.5 deploy 配置，逐一断言 Stage 1 的采样字段与上游默认一致，并单独验证 duplex overlay 的 `min_tokens=0` 不改变其余继承值；真实 Talker 测试还需确认最终配置到达 Sampler 与模型预算逻辑。^[PR #6458]

### CONF-6a — MOSS-TTS-Local 部署必须采用官方采样参数

- 触发：修改 MOSS-TTS-Local 的 deploy YAML 或其默认采样参数时。
- 强制：采用 MOSS-TTS-Local 官方示例参数：`temperature=1.7`、`top_p=0.8`、`top_k=25`、`repetition_penalty=1.0`；如需变更，必须有模型级行为证据支持。
- 禁止：沿用通用默认采样值，或仅凭经验调整敏感采样参数而不核对官方示例。
- 验收：解析 `vllm_omni/deploy/moss_tts_local.yaml`，断言上述参数与官方示例一致，并确认最终 stage 配置实际读取这些值。 ^[PR #6156]

### CONF-7a — 对象存储模型解析必须物化配置而保留原始 URI

- 触发：父进程在 stage-specific `ModelConfig` 初始化前，需要从 `s3://`、`gs://` 或上游 `is_runai_obj_uri` 支持的对象存储 URI 推断模型类型、读取 HF 配置或解析 `model_index.json`。
- 强制：通过 `is_runai_obj_uri` 将对象存储模型的 `*.model`、`*.py`、`*.json` 轻量文件按 URI 缓存一次到确定性的 `model_streamer/<hash>` 目录；`get_config`、`config.json` 和 `model_index.json` 的读取统一使用该本地目录，同时让各 stage 继续接收原始 URI 以保留 `model_weights` 的流式加载语义。
- 禁止：把原始对象存储 URI 交给 Hugging Face 仓库解析；把临时 `model_streamer/<hash>` 路径传播成 stage 的模型身份；用完整 URI、bucket 或组织名参与模型类型 basename 匹配。
- 验收：用 mock 覆盖对象存储 URI 的单次物化、配置驱动的 pipeline 选择、`model_index.json` 回退和 basename-only 匹配，并确认欺骗性 bucket 名不能劫持 pipeline；真实对象存储运行另行验证。^[PR #5036]

### VOMNI-CFG-2a — 配置公开导出必须延迟加载以保持导入链无环

- 触发：修改 `vllm_omni.config` 的公开导出，或新增会经 pipeline registry、模型 pipeline 与 diffusion 数据模块回环的配置导入路径。
- 强制：对会 eagerly 导入 `pipeline_registry`、`StageConfigFactory` 或其他重型 pipeline 依赖的公开配置符号使用模块级延迟解析；首次访问时通过 `importlib` 解析并缓存真实对象，同时保持 `__all__`、`__dir__` 与直接子模块导入的身份一致。导入链测试必须在干净解释器中先验证轻量配置导入不会预加载 registry/PI0，再验证公开导出仍解析到直接实现。
- 禁止：在 `vllm_omni.config` 包初始化阶段无条件导入会反向加载 `DiffusionOutput` 的 registry；用 import 顺序或已预加载模块掩盖循环；删除公开导出或让 lazy proxy 与直接导入得到不同对象。
- 验收：静态检查顶层导入不含重型 registry/factory，干净子进程按 `vllm_omni.config.lora` → `vllm_omni.diffusion.data` 顺序导入成功，并断言 `StageConfigFactory`、`register_pipeline` 与直接模块导出的对象相同；覆盖仍需用这些公开符号的调用方。^[PR #6293]

### VOMNI-CFG-2b — pipeline registry 必须只依赖轻量拓扑配置

- 触发：修改 `pipeline_registry.py` 的模型拓扑注册，或配置/插件导入链可能在配置解析期间预加载模型 runtime。
- 强制：将 registry 所需的静态 `PipelineConfig` 放入无 runtime 副作用的轻量模块；registry 只导入该模块，runtime pipeline 继续 re-export 同一对象以保持既有导入路径，并用干净子进程验证 registry 解析不加载 runtime。
- 禁止：让 `pipeline_registry` eager import 模型 runtime、依赖已预加载模块或导入顺序掩盖循环；不得因拓扑模块轻量就改变模型 runtime 的实际加载语义。
- 验收：隔离进程中导入并解析目标 registry key，断言对应 runtime module 不在 `sys.modules` 且返回的 `PipelineConfig` 身份与字段正确；再验证 runtime 的兼容导入路径仍 re-export 同一拓扑对象。^[PR #6322]

