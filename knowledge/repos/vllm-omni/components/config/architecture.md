---
title: "Config 共享架构"
created: 2026-07-16
updated: 2026-07-16
type: architecture
tags: [vllm-omni, components, config]
sources: [docs/configuration/stage_configs.md, docs/configuration/composable_parallel.md, vllm_omni/config/stage_config.py, vllm_omni/config/config_factory.py, vllm_omni/config/omni_config.py]
---

# Config 共享架构

以下事实在 `main @ 5c390096` 复核；官方 spec 见 `docs/configuration/stage_configs.md`
（schema 全表）与 `composable_parallel.md`。

## 双层 schema：PipelineConfig vs deploy YAML

- **`PipelineConfig`**（模型的冻结 stage 拓扑）由模型的 `pipeline.py` 注册；
  **deploy YAML**（`vllm_omni/deploy/*.yaml`，58 个）只描述"这些 stage 怎么跑"。
  未迁移模型仍走 legacy `--stage-configs-path` + `stage_args` schema
  （`vllm_omni/model_executor/stage_configs/*.yaml`）。
- 未显式给 `--deploy-config`/`--stage-configs-path` 时，registry 按 `model_type`
  自动解析 pipeline + bundled deploy YAML（如 `qwen2_5_omni.yaml` 在 1×H100、
  `qwen3_omni_moe.yaml` 在 2×H100 验证过）。
- deploy 顶层字段：`base_config`（overlay 父配置，`stages:`/`platforms:` 按 stage_id
  深合并、标量 overlay 胜）、`async_chunk`（默认 true）、`connectors`/`edges`（KV
  传输图；省略时由 stage 输入自动推导）、`stages`（必填）、`platforms`
  （npu/rocm/xpu 覆盖，叠在 CUDA 默认之上）、`pipeline`（覆盖 registry key，用于
  `qwen2_5_omni_thinker_only` 这类结构变体）以及 pipeline-wide 标量
  （`trust_remote_code` 默认 true、`dtype`、`quantization`、`enable_prefix_caching`
  默认 false、`data_parallel_size`/`pipeline_parallel_size` 默认 1 等）。
- per-stage `StageDeployConfig` 字段直接平铺（无嵌套 `engine_args:`）：`stage_id`
  （必填，对齐 `PipelineConfig.stages[*].stage_id`）、`max_num_seqs`（默认 64）、
  `gpu_memory_utilization`（**默认 0.9**——多 stage 共卡时必须显式设，见
  [rules](rules.md) `CONF-1a`）、`tensor_parallel_size`、`enforce_eager`、
  `max_num_batched_tokens`（默认 32768）、`max_model_len`、`devices`（默认 "0"）、
  `input_connectors`/`output_connectors`（`from_stage_<n>`/`to_stage_<n>` 键引用顶层
  `connectors:` 注册名）、`default_sampling_params`、`engine_extras`（未知键兜底，
  也承载 stage 级覆盖 pipeline-wide 值）。

## 解析链（函数级）

`resolve_deploy_yaml`（stage_config.py:576，处理 base_config overlay）→
`load_deploy_config`（:602）→ `merge_pipeline_deploy`（:831，冻结拓扑 + 部署参数
合并，平台覆盖在此叠加）→ `build_stage_runtime_overrides`（:48，产出逐 stage
运行时 override）；`strip_parent_engine_args`（:93）决定哪些父 EngineArgs 字段
进入/剥离每个 stage（消费端在 `engine/async_omni_engine.py`）。

## StageConfigFactory 与 pipeline registry

`StageConfigFactory`（config_factory.py:47）按 `model_type` 从
`pipeline_registry.OMNI_PIPELINES`（~44 个 key）解析出 `PipelineConfig` 或 resolver
callable（如 `resolve_qwen3_omni_pipeline`）；HF `model_type` 冲突用
`hf_architectures` 消歧（如 MiMo Audio 的 HF model_type 是 qwen2）；未注册模型报错
并列出可用 key（:360）。单 stage diffusion 模型**不在**该 registry（走
`async_omni_engine.py` 的 `_create_default_diffusion_stage_cfg` 兜底）。
`register_pipeline(...)` 支持 out-of-tree 注册。

## 结构化配置与 endpoint 策略

- `omni_config.py`：RFC #4021 Phase 2 的结构化配置——`VllmOmniConfig.from_registry`
  组装逐 stage 投影（`OmniStageModelConfig`/`CacheConfig`/`SchedulerConfig`/
  `ConnectorConfig`/`ParallelConfig`/`DiffusionParallelConfig` 等）。
- `endpoint_policy.py`：`OmniServingCapability`（:21，`RouteTarget` 枚举）+
  `shutdown_unsupported_routes`（:65）——pipeline 可关闭自己不支持的 serving 路由。
- `composable_parallel/`：`--strategy-config` 把逐 stage 并行轴栈
  （tp/dp/pp/ep/stage_replica 已接线；sp/cfg/vae_pp/hsdp 等保留位）以声明式 overlay
  叠加到合并后的 stage 上、先于 CLI override；**不能**与 legacy
  `--stage-configs-path` 组合。

源码会变化，具体函数与行号在改代码前必须以目标仓库当前版本为准。
