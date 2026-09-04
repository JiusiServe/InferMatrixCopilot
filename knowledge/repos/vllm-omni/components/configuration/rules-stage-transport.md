---
title: "Stage transport capability"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, config, scheduler, connectors]
sources: [vllm_omni/config/stage_config.py, vllm_omni/config/omni_config.py, vllm_omni/engine/arg_utils.py, tests/config/test_omni_config.py, tests/config/test_config_factory.py, tests/engine/test_arg_utils.py, "PR #6149"]
---

# Stage transport capability

适用于 pipeline stage 的完整 payload 输入能力、其 config projection，以及 deploy/CLI 对该能力的覆盖。
调度侧的 admission 和 async sender/receiver 合同见 [Scheduler rules](../scheduler/rules.md#sched-6b-full-payload-admission-是解析后的-downstream-capability)；worker connector 验证见 [Model Executor rules](../model-executor/rules.md#exec-3c-connector-required-stage-必须在-worker-启动前验证-runner-capability)。

## VOMNI-CFG-1p — stage transport capability 只能由 pipeline topology 解析

- 触发：新增或修改 stage 输入传输、`requires_full_payload_input`、deploy/CLI override 或 engine-args projection。
- 强制：完整 payload 的消费能力在 `StagePipelineConfig` 中声明，并在 legacy 与 structured 配置构造时无条件覆盖进最终 `OmniStageModelConfig`、`OmniEngineArgs` 与 `OmniModelConfig`；必须保留 `False`，且 deploy 的 flat key、`engine_args`、`engine_extras` 和 CLI 都不能伪造或覆盖该 topology 结论。
- 禁止：用 architecture/stage 名 allowlist 重新推断能力；让 free-form deploy/CLI 在 producer 校验之后改写 transport；把 async producer 的 `async_chunk` 发送职责误当作下游 full-payload wait capability。
- 验收：覆盖旧 allowlist 对应的 pipeline declarations 和一个 token-only control；三个 legacy YAML 拼写及 CLI override 均因没有 structured owner 而拒绝；从 pipeline 到最终 model config 断言 true/false 均完整保留。^[PR #6149]
