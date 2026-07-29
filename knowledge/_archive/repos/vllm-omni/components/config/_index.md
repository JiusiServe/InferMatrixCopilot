---
title: "Config（pipeline 与 deploy 配置系统）"
created: 2026-07-16
updated: 2026-07-16
type: index
tags: [vllm-omni, components, config]
sources: [vllm_omni/config/stage_config.py, vllm_omni/config/config_factory.py, docs/configuration/stage_configs.md]
---

# Config（pipeline 与 deploy 配置系统）

- 源码入口：`vllm_omni/config/`（`stage_config.py`、`config_factory.py`、
  `pipeline_registry.py`、`omni_config.py`、`endpoint_policy.py`、`server_settings.py`、
  `yaml_util.py`、`composable_parallel/`）与逐模型 deploy YAML `vllm_omni/deploy/*.yaml`
- 源码校验：以上路径与下列锚点均已在 `main @ 5c390096` 验证存在：
  `build_stage_runtime_overrides`（stage_config.py:48）、`strip_parent_engine_args`（:93）、
  `resolve_deploy_yaml`（:576）、`load_deploy_config`（:602）、`merge_pipeline_deploy`（:831）、
  `StageConfigFactory`（config_factory.py:47）、`OmniServingCapability`
  （endpoint_policy.py:21）；`vllm_omni/deploy/` 含 58 个 YAML
- 官方配置 spec：`docs/configuration/stage_configs.md`、`composable_parallel.md`、
  `pd_disaggregation.md`、`gpu_memory_utilization.md`
- 测试入口：`tests/config/`、`tests/test_config_factory.py`

## 什么时候查这里

- 排查 CLI / deploy YAML / per-stage override 的合并语义与最终生效配置。
- 新模型接 pipeline registry、deploy YAML 或 endpoint 限制。
- stage 显存预算（`gpu_memory_utilization`、`kv_cache_memory_bytes`）类 OOM。

## 不放什么

- runner 侧 stage 并行度与设备容量的验收规则在
  [Model Executor 规则](../model-executor/rules.md)（这里管配置语义，那里管启动验收）。
- 配置审计的"说人话"工作法在 [dev 配置审计](../../dev/guides/config-audit-plain-language.md)。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解 PipelineConfig/DeployConfig 双层 schema 与解析链 | [architecture](architecture.md) |
| stage 显存预算与配置合并的硬规则 | [rules](rules.md) |
