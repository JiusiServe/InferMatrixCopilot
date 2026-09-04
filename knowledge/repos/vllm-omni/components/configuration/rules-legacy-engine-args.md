---
title: "legacy engine args 投影隔离"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, config]
sources: ["PR #6783", vllm_omni/engine/stage_init_utils.py, tests/engine/test_build_engine_args_no_mutate.py]
confidence: high
---

# legacy engine args 投影隔离

## VOMNI-CFG-1r — legacy engine-args projection 必须递归 detach source config

- 触发：`build_legacy_engine_args_dict`、`_to_dict(stage_config.engine_args)`、finalizer、connector 或 default injection 修改。
- 强制：先对 `_to_dict(stage_config.engine_args)` `deepcopy`，再 pop/delete/finalize/inject；source template 和所有 nested mutable objects 不得改变，重复 build 的结果等价且 idempotent。实际 `inject_omni_kv_connector_config` 在 returned dict 的 resolved connector mutation path 也必须不能 leak 回 source。
- 禁止：只 shallow copy、只测 top-level no-mutation，或让 legacy projection 因上一次 build 的 resolved/default/connector state 改变下一次输出。
- 验收：覆盖 pop/finalizer/default/nested dict、two successive builds，以及 connector injection 后 source snapshot 不变。证据为 CPU regression/reviewer approval；不证明 typed projection、runtime connector success 或 hardware behavior。^[PR #6783]
