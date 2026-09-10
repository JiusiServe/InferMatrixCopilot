---
title: "legacy engine args 投影隔离"
created: 2026-09-05
updated: 2026-09-10
type: rule
tags: [vllm-omni, components, config]
sources: ["PR #6783", vllm_omni/engine/stage_init_utils.py, tests/engine/test_build_engine_args_no_mutate.py, "PR #5929", "PR #7237"]
confidence: high
---

# legacy engine args 投影隔离

## VOMNI-CFG-1r — legacy engine-args projection 必须递归 detach source config

- 触发：`build_legacy_engine_args_dict`、`_to_dict(stage_config.engine_args)`、finalizer、connector 或 default injection 修改。
- 强制：先对 `_to_dict(stage_config.engine_args)` `deepcopy`，再 pop/delete/finalize/inject；source template 和所有 nested mutable objects 不得改变，重复 build 的结果等价且 idempotent。实际 `inject_omni_kv_connector_config` 在 returned dict 的 resolved connector mutation path 也必须不能 leak 回 source。
- 禁止：只 shallow copy、只测 top-level no-mutation，或让 legacy projection 因上一次 build 的 resolved/default/connector state 改变下一次输出。
- 验收：覆盖 pop/finalizer/default/nested dict、two successive builds，以及 connector injection 后 source snapshot 不变。证据为 CPU regression/reviewer approval；不证明 typed projection、runtime connector success 或 hardware behavior。^[PR #6783]

## VOMNI-CFG-1s — global stage engine args 必须先验 owner，再按执行类型投影

- 触发：新增或修改全局 stage CLI 字段、stage-scoped alias、`diffusion_offload_config`，或调整 structured/legacy 的 stage runtime overrides。
- 强制：先对完整规范化后的 stage CLI 映射做 ownership 校验，再按每个 stage 的 `execution_type` 投影到该 stage；显式 stage 覆盖优先，全局字段只有在目标 stage 实际拥有该字段时才可透传。任何 pipeline 中没有 owner 的显式全局 engine arg 都必须在构造前 fail closed，不能静默丢给无关 stage 或靠默认值吞掉。
- 强制：`diffusion_offload_config` 这类跨进程序列化的 public mapping 必须保留 raw dict 进入 dataclass/config serialization，同时在 stage 构造前调用其专属 parser 做一次结构校验；兼容 alias 只能 materialize 成同一份内部策略，不能让 compile/offload 约束只检查旧布尔字段。
- 禁止：先按 execution type 过滤再做 unknown/owner 校验；只在 direct path 校验而让 deploy/structured 漏检；把 raw mapping 先转成内部对象后再跨进程传输；或让 `full` compile compatibility 继续只识别 legacy offload flags。
- 验收：覆盖 global 与 stage-specific override precedence、unowned global field rejection、`diffusion_offload_config` 的 direct/deploy/structured reachability，以及 compile-mode 对 module/layer/distributed-layer 三种 offload strategy 的统一 incompatibility gate。^[PR #5929]

## VOMNI-CFG-1t — CLI-only 负向 alias 不得进入 stage ownership 校验

- 触发：继承 upstream CLI 负向开关（如 `--disable-log-stats`），或修改 `_NON_STAGE_ENGINE_CLI_FIELDS`、`AsyncOmniEngine._resolve_stage_configs`、headless `cli_overrides`。
- 强制：把该 alias 标为非 stage 字段；在 `log_stats` 等 canonical 值已由 launcher/`__init__` 消费后，于 resolver 边界 `pop` 残余 alias，使 structured ownership 看不到它。标准与 headless 启动都必须消费。
- 禁止：让 residual `disable_log_stats` 落入 `resolve_omni_config` / `VllmOmniConfig` 并报 “no structured config owner”；为通过校验而放宽真正的 stage engine-arg ownership。
- 验收：断言字段在 `_NON_STAGE_ENGINE_CLI_FIELDS` 且不在 global stage CLI fields；engine 与 headless 解析后 kwargs/`cli_overrides` 不含该 alias；带 alias 的 TTS/structured pipeline 仍能构造。^[PR #7237]
