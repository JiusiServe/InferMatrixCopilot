---
title: "vLLM-Omni Configuration"
created: 2026-07-16
updated: 2026-08-05
type: index
tags: [vllm-omni, components, config]
sources: ["claude-workflow-starter-private@296ea45", vllm_omni/config/]
---

# vLLM-Omni Configuration

- 主要源码：`vllm_omni/config/`
- 跨边界入口：`vllm_omni/diffusion/data.py`、`vllm_omni/engine/arg_utils.py`、`vllm_omni/engine/stage_init_utils.py`、`vllm_omni/engine/async_omni_engine.py`
- 主要测试：`tests/config/`、`tests/config/test_config_factory.py`、
  `tests/diffusion/test_diffusion_config_propagation.py`，以及各公开入口附近的配置测试
- 部署配置：`vllm_omni/deploy/*.yaml`，以及 `pipeline_registry.py`、
  `endpoint_policy.py`、`server_settings.py`、`yaml_util.py`、`composable_parallel/`
- 源码校验：以上路径在 `main @ ee118ab4` 验证存在；机器基线见
  `adapters/vllm_omni/release_baseline.yaml`

## 什么时候查这里

- 修改 deploy、pipeline、stage、CLI、默认 factory 或 direct kwargs 的配置构造。
- 调查字段来源优先级、alias、flat→nested、strict unknown-field 校验、shared/stage/diffusion owner 分区。
- 核对 structured、legacy startup、默认 single-stage factory 和 direct factory 的语义一致性。

## 不放什么

- HTTP 请求字段和 serving 层限制；这些属于 [Serving](../serving/_index.md)。
- 最终 stage config 之后的并行与设备启动；这些属于 [Model Executor](../model-executor/_index.md)。
- 某个模型独有的配置或 checkpoint 语义；这些放模型目录。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解配置从 deploy、CLI、默认 factory 到 structured/legacy config 的稳定边界 | [配置构造架构](architecture.md) |
| 根据 PR 描述直达 strict schema、deploy/topology、composable strategy 或显存配置的规则组与第一批源码 | [配置开发门禁与代码地图](rules.md) |
| 审计配置来源和多层加工 | [config audit](config-audit-plain-language.md) |
| 设计配置归一化与 parity 验证 | [config normalization parity](config-normalization-parity.md) |
| 查询 `Omni()` 初始化参数 | [Omni init args](omni-init-args.md) |
| 写或修改 deploy YAML | [deploy YAML](deploy-yaml.md) |
| 核对 pipeline/deploy schema | [pipeline deploy schema](pipeline-deploy-schema.md) |
| 计算多 stage 显存预算 | [deployment memory budget](deployment-memory-budget.md) |
| 添加新模型和注册点 | [adding a model](adding-a-model.md) |
