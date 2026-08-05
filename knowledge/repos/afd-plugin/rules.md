---
title: "afd-plugin 硬门禁"
created: 2026-08-05
updated: 2026-08-05
type: rule
tags: [afd-plugin, review, config, distributed, model-executor]
sources: ["vllm-project/afd-plugin:AGENTS.md", "vllm-project/afd-plugin:README.md", "vllm-project/afd-plugin:pyproject.toml", "vllm-project/afd-plugin:.github/workflows/cpu-only-ci.yml", "vllm-project/afd-plugin:.agents/skills/run-e2e/SKILL.md"]
---

# afd-plugin 硬门禁

只在当前任务明确属于 `vllm-project/afd-plugin` 时应用本页。先按 [afd-plugin 入口](_index.md) 确认仓库身份，再结合 [通用 review 入口](../../general/review/_index.md) 做常规审查。

## 1. 仓库身份和权威来源

- AFD-1a：review 或 issue 回答前必须确认目标是 canonical `vllm-project/afd-plugin`，不能把 vLLM-Omni 的知识树、模型规则、远端策略或 rebase 假设带入 AFD。
- AFD-1b：AFD 仓库自己的 `AGENTS.md`、`CLAUDE.md`、`.agents/skills/run-e2e/SKILL.md`、CI workflow 和仓库脚本是权威来源；InferMatrixCopilot 只做只读路由、提示和证据组织。
- AFD-1c：默认路径保持只读；不能自动发 PR 评论、push、改 protected branch，不能要求 AFD runtime 行为因为本 adapter 初始化而改变。

## 2. 兼容范围和插件边界

- AFD-2a：兼容结论必须精确写当前声明的 runtime：vLLM `0.19.1`；Ascend NPU baseline 是 vLLM-Ascend `0.19.1rc1`、CANN/NNAL `8.5.1`、torch/torch-npu `2.9.0`。不得推断更宽版本范围。
- AFD-2b：AFD 通过 `vllm.general_plugins` entry point、`VLLM_PLUGINS`、`additional_config["afd"]`、自动 worker 选择、plugin-owned model wrapper 和窄 compatibility shim 生效；不得建议新增独立 `--afd-config` 之类的公开入口。
- AFD-2c：`additional_config["afd"]` 之外的 connector 私有字段必须进入 `connector_extra_config`，并由对应 connector parser 校验；未知 AFD 顶层字段应暴露为错误，而不是静默透传。
- AFD-2d：没有 `additional_config["afd"]` 时必须保持非 AFD 路径隔离；非 AFD 请求、worker、模型和上游 vLLM 行为不能被 AFD patch 或自动选择污染。

## 3. Patch、connector 和 worker review

- AFD-3a：`afd_plugin/compat/` patch 必须 upstream-first：复制目标 tag 的上游函数，保持函数签名和返回类型，使用 `# ### PATCH START` / `# ### PATCH END` 标出 AFD 差异，并写清 patch reason、功能变化和移除或 upstream 计划。
- AFD-3b：不得用宽泛 `getattr`、`hasattr`、`Any`、`object` 或 `_original_*` delegation 掩盖上游 API 漂移；只有 AGENTS 明确允许的例外才可使用，并必须在 patch 注释说明原因。
- AFD-3c：`afd_plugin/connectors/`、`afd_plugin/distributed/` 改动必须审 rank 布局、attention/ffn 数量约束、同步/异步语义、端口/host、进程组生命周期、资源 cleanup 和跨 role 同步失败路径。
- AFD-3d：`afd_plugin/v1/worker/`、`afd_plugin/model_executor/` 改动必须审自动 worker 选择、role-specific runner、Attention/FFN 组件加载边界、scheduler-driven FFN fail-fast、CUDA/ACL graph 模式和 DBO/ubatch 条件。
- AFD-3e：`csrc/gpu/`、`csrc/npu/` 改动必须区分 CUDA 与 Ascend CANN/ACLNN toolchain；NPU op 构建只能在明确 Ascend 环境或显式 `AFD_BUILD_ASCEND_OPS=1` 下作为证据。

## 4. 验证和证据

- AFD-4a：CPU-safe 默认检查是 `uv run pytest`、`uv run pytest -q tests/unit -m "not gpu and not vllm_runtime"`、`uv run ruff check .`、`uv run ruff format --check .`；它们不能证明 GPU/NPU runtime、模型精度或性能。
- AFD-4b：GPU/NPU E2E 必须通过 AFD 仓库 `.agents/skills/run-e2e/SKILL.md` 或仓库测试入口运行，记录 backend、设备数、模型路径、vLLM/vLLM-Ascend/CANN/torch 版本、拓扑、connector、graph/DBO/async 配置和 skipped 原因。
- AFD-4c：性能、精度或硬件支持 claim 必须给可复现证据：硬件型号、软件版本、driver/toolchain、rank 拓扑、命令、日志或 pytest node id；CPU import/config smoke 不能替代硬件证据。
- AFD-4d：changed files 没有命中 adapter route 时，必须把 unmatched path 明确留给 host reviewer 继续人工审，不得把它当作已覆盖。
