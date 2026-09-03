---
title: "并行拓扑合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, config]
sources: [vllm_omni/config/composable_parallel/, vllm_omni/config/config_factory.py, vllm_omni/config/stage_config.py]
confidence: high
---

# 并行拓扑合同

`CONF-4a`–`CONF-4d`：composable strategy 的 axis 暴露、新并行轴进入最终拓扑、标准与 headless 启动的拓扑一致性，以及 strategy/CLI/pipeline-wide load balancing 的唯一 owner。触发条件与其余审查组见 [Configuration 规则](rules.md) 的 Direct 代码快速入口。

## CONF-4a — composable strategy 只暴露已经接通的 axis

- 触发：新增 composable parallel strategy、axis、routing/LB policy 或 stage override。
- 强制：schema 明确区分 wired 与 reserved；translator 对 unsupported/reserved 值显式
  失败。routing 与 load-balancing policy 只能有一个 owner。
- 禁止：接受但静默忽略 axis；关键 strategy/deploy 文件缺失时 conditional skip；以
  可漂移的 stage index 作为长期 identity。
- 验收：每个公开 axis 都有 spec → translator → final stage config 的正向测试和
  unsupported fail-fast 测试；stage 使用稳定名称。

## CONF-4b — 标准与 headless 启动必须解析出同一拓扑

- 触发：CLI、headless serve、offline entrypoint 或 engine factory 新增/转发配置字段。
- 强制：同一命令语义在所有入口转发相同 override，并比较展开后的逐 stage 配置。
- 禁止：只测 parser 输出，未证明值到达 engine/config consumer。
- 验收：标准与 headless 路径对同一 override 生成等价 topology；缺字段时直接失败，
  不允许用 skip 隐藏路径漂移。

## CONF-4c — 新并行轴必须进入最终拓扑并由 consumer 校验

- 触发：新增 diffusion parallel axis、text-encoder TP、CFG/patch parallel 或把
  `strategy-config` 的声明映射到 stage runtime。
- 强制：从 strategy spec/CLI 到 `OmniStageDiffusionParallelConfig` 和最终 process
  group 展开完整链路；记录 `data × cfg × sequence × pipeline × tensor` 的设备乘积，
  并由实际 consumer 校验 rank/head divisibility、模型不支持的组合和可见设备容量。
- 禁止：parser 接受字段后在 projection、engine kwargs 或 worker 初始化时丢失；用一个
  generic upper bound 替代模型自己的约束；用 recipe 示例或单纯 dataclass 构造代替真实
  topology/consumer 证据。
- 验收：正向测试断言新值可从最终 stage config 读回；负向测试覆盖不整除的 head/rank、
  `cfg_parallel_size` 不适用的模型和设备不足，并在 worker 创建前失败。

## CONF-4d — strategy、CLI 与 pipeline-wide load balancing 必须保留唯一 owner

- 触发：`strategy_config`、legacy YAML、`--omni-lb-policy` 或 stage replica/load
  balancing 同时提供策略。
- 强制：registry-backed strategy 才进入 translator；legacy 路径明确 warning 并保持
  原语义；合并顺序固定为 deploy/pipeline → strategy → CLI，CLI 的显式冲突必须可见，
  pipeline-wide load-balancer 只由 orchestrator 拥有并传入各 stage。
- 禁止：接受 legacy `strategy_config` 后静默声称已生效；把 CLI 的默认值误当显式覆盖；
  每个 stage 各自构造一个相互冲突的全局 load balancer。
- 验收：覆盖 registry、legacy、CLI 非默认值和冲突值，断言最终拓扑、设备乘积和单一
  load-balancer consumer；策略生效前若设备不足必须 fail fast。

部署 YAML 的展开顺序见 [deploy-yaml](deploy-yaml.md)；stage 执行合同见 [model-executor 规则](../model-executor/rules.md)。
