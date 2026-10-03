---
title: "legacy engine args 投影隔离"
created: 2026-09-05
updated: 2026-09-22
type: rule
tags: [vllm-omni, components, config]
sources: ["PR #6783", vllm_omni/engine/stage_init_utils.py, tests/engine/test_build_engine_args_no_mutate.py, "PR #5929", "PR #7237", "PR #7390"]
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

## VOMNI-CFG-1u — 用户可见的 upstream ModelConfig CLI 必须有 typed stage owner

- 触发：文档/示例使用的全局 ModelConfig CLI（如 `served_model_name`、`allowed_local_media_path`、`allowed_media_domains`、`max_logprobs`、`logprobs_mode`、`mm_processor_kwargs`、`mm_processor_cache_type`、`hf_token`、`hf_config_path`、`generation_config`、`override_generation_config`、`enable_prompt_embeds`）在 `from_pipeline_config` 报无 owner，或新增同类 upstream ModelConfig 输入。
- 强制：把字段同时加入 `_ModelEngineOverrides` 与 `OmniStageModelConfig`，类型跟随 vLLM `EngineArgs`，默认 `None`，使 `_project_omni_config_fields` 只投影用户显式值，并经 typed/legacy engine-args 到达各 stage。不得把这些 ModelConfig 输入塞进 `_NON_STAGE_ENGINE_CLI_FIELDS` 来绕过 ownership。
- 禁止：仅因 legacy `build_stage_runtime_overrides` 仍能透传就让 structured ownership 拒绝文档命令；把尚未归属的非 ModelConfig 开关（如 `enable_lora`/`speculative_config`）一并放行。
- 验收：对至少两个 pipeline key 参数化断言显式全局值进入每个 stage 的 `model_config`，并用 typed `build_engine_args_dict_from_omni_stage_config` 读回同一集合；字段集合 census 必须包含这些 owner。^[PR #7390]

## VOMNI-CFG-1v — `from_cli_args` 依赖的 diffusion 并行字段必须声明在 OmniEngineArgs

- 触发：新增或转发 `--text-encoder-tp-size` 等 library/`OmniEngineArgs.from_cli_args` 会过滤的 diffusion 并行字段，或修改 `from_cli_args` 的 dataclass field filter。
- 强制：凡 library 调用方经 `from_cli_args` → stage kwargs → `DiffusionParallelConfig` / `create_default_diffusion` 消费的字段，必须在 `OmniEngineArgs` 上显式声明（如 `text_encoder_tp_size: int | None = None`），使 filter 保留 namespace 值。注册 pipeline 若经 `stage_cli_aliases` 改写语义，须在规则/测试中单独钉死，不能与 generic diffusion fallback 混为一谈。
- 禁止：只在 argparse/serve 路径注册 flag 却不声明 dataclass 字段，导致值被静默丢弃并回退默认（如 TP=1）；为通过 filter 把字段错误挂到破坏 shared-fields 不变量的 `OrchestratorArgs`。
- 验收：`from_cli_args(SimpleNamespace(...))` 读回字段；再经 default diffusion factory 断言 `parallel_config` 同值；既有 serve CLI 与 shared-fields 回归不得回退。^[PR #7652]

## VOMNI-CFG-1w — 写入 model_config 的 CLI-only alias 必须移出 explicit_keys

- 触发：serve CLI 把 `--no-guardrails` 等仅入口别名改写进 `model_config`，或修改 `OmniServeCommand.cmd` 对 `TrackingNamespace.explicit_keys` 的更新。
- 强制：alias 消费后只保留 canonical `model_config`（如 `guardrails=False`）；从 `explicit_keys` 去掉 `no_guardrails` 这类 CLI-only 名，再交给 diffusion stage 的严格 ingress 校验。标准与 headless 路径同一清理。
- 禁止：映射完成后仍把 alias 当 stage engine override 转发，触发 `Unknown diffusion config field(s)`；为通过校验而放宽 unknown-field 拒绝。
- 验收：真实 parser + `normalize_and_validate_diffusion_engine_ingress_kwargs` 断言 `model_config.guardrails is False` 且 explicit kwargs 不含 alias。^[PR #7917]
