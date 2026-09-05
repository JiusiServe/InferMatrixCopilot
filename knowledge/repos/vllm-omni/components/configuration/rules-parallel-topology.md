---
title: "并行拓扑合同"
created: 2026-09-04
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, config]
sources: [vllm_omni/config/composable_parallel/, vllm_omni/config/config_factory.py, vllm_omni/config/stage_config.py, "PR #5531"]
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

## CONF-4e — WORLD、DP 与 HSDP 拓扑必须在实际设备数上闭合

- 触发：修改 `DiffusionParallelConfig`、`OmniStageDiffusionParallelConfig` 对 `WORLD_SIZE`、DP、HSDP、SP/CFG/TP/PP/EP 的解析，或修改 async stage 的设备展开。
- 强制：普通并行必须满足 `WORLD_SIZE = TP × SP × PP × CFG × DP`；省略 DP 时保留 `None`，直到获得实际 `num_gpus`/WORLD 后推导，显式 DP 必须与推导值一致。HSDP 必须令普通 DP 为 1，并满足 `WORLD_SIZE = hsdp_replicate_size × hsdp_shard_size`；SP/CFG 只能复用同一 WORLD 拓扑，其乘积必须为 1 或 WORLD。解析 DP 后再生成 devices，并将 `num_gpus` 保留到最终 stage engine args。
- 禁止：在配置解析期把省略的 DP 固定为 1 后据此生成不足的设备列表；接受与 WORLD 推导值不一致的显式 DP；允许 HSDP 与 TP、普通 DP、PP 或 EP 组合；只用 `num_gpus` 做校验却不传播到 stage 配置。
- 验收：覆盖 direct、structured 和 async stage 路径；`num_gpus=8`、TP=2、SP=2 必须得到 DP=2、WORLD=8 和 devices `0`–`7`，省略 DP 的配置在运行时解析前仍保持未指定；覆盖 HSDP mesh 不匹配及不支持组合，并确认都在进程组创建前失败。^[PR #5531]

