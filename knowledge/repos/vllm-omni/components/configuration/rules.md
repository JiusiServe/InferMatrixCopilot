---
title: "vLLM-Omni 配置开发门禁"
created: 2026-07-16
updated: 2026-08-05
type: rule
tags: [vllm-omni, components, config]
sources: ["claude-workflow-starter-private@296ea45", "PR #4281", "PR #5031", "PR #5678", "zuiho-kai/claude-workflow-starter@c217fc6", vllm_omni/config/stage_config.py, vllm_omni/config/config_factory.py, vllm_omni/config/omni_config.py, vllm_omni/config/composable_parallel/, vllm_omni/engine/stage_init_utils.py, tests/engine/test_stage_engine_args.py]
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

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次配置审查 | `VOMNI-CFG-1b`, `VOMNI-CFG-1c` |
| `strict-normalization` | schema、alias、unknown field、structured/legacy/direct 路径 | `VOMNI-CFG-1a`, `VOMNI-CFG-1b`, `VOMNI-CFG-1c`, `VOMNI-CFG-1d`, `VOMNI-CFG-1e`, `VOMNI-CFG-1f`, `VOMNI-CFG-1g`, `VOMNI-CFG-1h` |
| `deploy-memory` | 显存预算、KV pin、多 stage 共卡 | `CONF-1a`, `CONF-2a` |
| `deploy-topology` | deploy、overlay、headless、topology wiring | `CONF-3a`, `CONF-4b`, `CONF-5a` |
| `composable-strategy` | strategy axis、routing、load balancing | `CONF-4a` |
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

### CONF-4c — 新并行轴必须进入最终拓扑并由 consumer 校验

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

### CONF-4d — strategy、CLI 与 pipeline-wide load balancing 必须保留唯一 owner

- 触发：`strategy_config`、legacy YAML、`--omni-lb-policy` 或 stage replica/load
  balancing 同时提供策略。
- 强制：registry-backed strategy 才进入 translator；legacy 路径明确 warning 并保持
  原语义；合并顺序固定为 deploy/pipeline → strategy → CLI，CLI 的显式冲突必须可见，
  pipeline-wide load-balancer 只由 orchestrator 拥有并传入各 stage。
- 禁止：接受 legacy `strategy_config` 后静默声称已生效；把 CLI 的默认值误当显式覆盖；
  每个 stage 各自构造一个相互冲突的全局 load balancer。
- 验收：覆盖 registry、legacy、CLI 非默认值和冲突值，断言最终拓扑、设备乘积和单一
  load-balancer consumer；策略生效前若设备不足必须 fail fast。

### CONF-5b — `trust_remote_code` 的未指定值必须保留 deploy 优先级

- 触发：CLI、structured factory、legacy stage factory 或 deploy YAML 同时提供
  `trust_remote_code`。
- 强制：调用方显式 `True`/`False` 才覆盖 per-stage deploy 值；未指定用 `None` 表示并
  保留 YAML 值，HF config resolution 才把 `None` 收敛为安全的实际 bool。
- 禁止：把 `store_true` 的 absent-False 当成显式 False 无条件写入 override；structured
  与 legacy 各自实现 precedence；在末端用默认值静默覆盖用户明确的 False。
- 验收：覆盖“未指定、显式 True、显式 False”三态，并从 structured/legacy 两条路径
  断言最终 stage config；`with_trust_remote_code_override` 是唯一合并入口。

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
