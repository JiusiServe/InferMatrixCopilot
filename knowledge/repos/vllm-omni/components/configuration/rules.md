---
title: "vLLM-Omni 配置开发门禁"
created: 2026-07-16
updated: 2026-07-30
type: rule
tags: [vllm-omni, components, config]
sources: ["claude-workflow-starter-private@296ea45", "PR #4281", "PR #5031"]
---

# vLLM-Omni 配置开发门禁

只在修改 vLLM-Omni 的 config、deploy、pipeline、CLI 字段归属、alias、unknown-field 校验、flat→nested 归一化或默认 factory 时使用。第一次读这些规则时，先看
[config audit 说人话规则](guides/config-audit-plain-language.md)；需要执行时再看
[config normalization parity](guides/config-normalization-parity.md) 的矩阵和操作顺序。

## 配置归一化与新老路径一致性

- **VOMNI-CFG-1a — 编码前冻结受影响合同。** 第一次业务代码修改前，只列当前 diff 会改变的入口和值状态，再加一个默认或相邻 control；不得做所有入口和值的笛卡尔积，也不得省略仍可调用的 legacy/direct 入口。
- **VOMNI-CFG-1b — 在第一位 consumer 前归一化。** 对 changed value 标出实际对象、copy/转换边界和第一位 consumer；归一化必须在该 consumer 之前完成。从 unknown 集合排除字段时，必须证明值进入明确 owner 且能从结果读回。
- **VOMNI-CFG-1c — 用同路径行为证据验收。** 受影响 legacy/structured 路径必须对相关 `null`、有效值、冲突值或可转换标量得到相同结果；至少一个非默认值走到第一位 consumer 和最终 config。helper 单测只能补充，最后必须在含 `vllm` 的兼容环境实跑目标测试。
- **VOMNI-CFG-1d — 兼容修复不能自动继承原 scope。** 新修复若引入新的 owner、来源、优先级、转换或模型/服务路由，或实现量级接近预估两倍，必须先重切片；禁止按入口堆特例和重复测试。验收时每个生产代码 hunk 都应属于本轮目的，同一语义跨入口使用参数化矩阵并保留一个 control。
- **VOMNI-CFG-1e — 严格配置固定按“归一化、验 owner、分区、构造”执行。** deploy/stage/CLI overlay、alias 和 flat→nested 转换必须先产出一份规范化映射；ownership validator 只检查完整 key 集合，不能同时改值、路由字段或先丢 `None`；校验通过后才按 shared、stage 和 diffusion owner 分区并构造最终 config。structured、legacy startup 和仍公开可调用的 direct factory 必须复用同一组 normalization/validation primitive，禁止各入口维护语义重叠的 allowlist、冲突判断或静默过滤。
- **VOMNI-CFG-1f — key 是否已知与 value 是否有效必须分开判定。** 缺失、已知字段的 `None`、显式 `False`/`0`、未知字段的 `None` 和两个非空来源冲突是五种不同状态：只有明确 owner 可以把已知 `None` 解释为 unset，`False`/`0` 不得被 truthiness merge 吃掉，未知 key 即使为 `None` 也必须按 strict contract 报错，alias 只在 legacy 与 canonical 都提供非 `None` 值时冲突。验收至少覆盖本轮会改变分支的这些状态，并断言错误或最终 consumer。
- **VOMNI-CFG-1g — rebase 或 schema 扩张后重新做配置归属审计。** 上游新增 dataclass 字段、默认 factory 参数、pipeline-wide 字段或 owner 集合变化时，把自动合并结果当作新的语义 diff；重新比较 base/head 的字段集合、序列化边界、默认-stage 透传和所有严格入口。默认 factory 的扩展字段应由 schema metadata 或单一声明集合驱动，禁止再加一份手写白名单。只有最新 base 上的真实 factory/legacy/structured 路径都保留合法非默认值并继续拒绝未知字段，才算 rebase 完成。

## 部署配置与资源预算

只有 `CONF-数字字母` 是本节可审计规则 ID。

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

### CONF-3a — 争议以展开后的最终配置为准

- 触发：CLI、deploy YAML、`base_config` overlay、platform 覆盖、per-stage override
  或 `engine_extras` 各层说法不一致。
- 强制：以 `resolve_deploy_yaml → load_deploy_config → merge_pipeline_deploy →
  build_stage_runtime_overrides` 展开后的最终逐 stage 配置为唯一事实，逐字段打印核对。
- 禁止：拿某一层 YAML 原文当生效值；用默认值脑补缺失字段。
- 验收：争议字段在最终逐 stage 对象中可读回，并与第一位 consumer 一致。

### CONF-4a — composable strategy 只暴露已经接通的 axis

- 触发：新增 composable parallel strategy、axis、routing/LB policy 或 stage override。
- 强制：schema 明确区分 wired 与 reserved；translator 对 unsupported/reserved 值显式
  失败。routing 与 load-balancing policy 只能有一个 owner。
- 禁止：接受但静默忽略 axis；关键 strategy/deploy 文件缺失时 conditional skip；以
  可漂移的 stage index 作为长期 identity。
- 验收：每个公开 axis 都有 spec → translator → final stage config 的正向测试和
  unsupported fail-fast 测试；stage 使用稳定名称。

### CONF-4b — 标准与 headless 启动必须解析出同一拓扑

- 触发：CLI、headless serve、offline entrypoint 或 engine factory 新增/转发配置字段。
- 强制：同一命令语义在所有入口转发相同 override，并比较展开后的逐 stage 配置。
- 禁止：只测 parser 输出，未证明值到达 engine/config consumer。
- 验收：标准与 headless 路径对同一 override 生成等价 topology；缺字段时直接失败，
  不允许用 skip 隐藏路径漂移。

### CONF-5a — 冻结 topology 只保留一份，部署开关决定 wiring

- 触发：同一模型的 sync/async processor、普通/async chunk 或部署加速出现多份近似
  pipeline/stage YAML。
- 强制：相同冻结拓扑共用一份 pipeline config，同时声明可选 processor；由 deploy
  flag 决定 wiring。模型 package `__init__` 保持轻量，FP8 等部署加速留在 deploy 层。
- 禁止：为一个 runtime flag 复制整套 topology；把无关 payload bug 或平台 cleanup
  混入 config migration。
- 验收：两种 wiring 都从同一 topology 展开，配置 diff 只包含预期 deploy 字段；
  同卡多 stage 的 `gpu_memory_utilization` 总预算不超过可用容量。
