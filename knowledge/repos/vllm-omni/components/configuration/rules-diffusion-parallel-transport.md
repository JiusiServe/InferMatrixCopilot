---
title: "Diffusion parallel transport 配置规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, config, diffusion]
sources: ["PR #6340", vllm_omni/config/stage_config.py, vllm_omni/config/omni_config.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/engine/arg_utils.py, vllm_omni/entrypoints/cli/serve.py, tests/config/test_omni_config.py, tests/entrypoints/test_async_omni_diffusion_config.py, tests/entrypoints/test_serve.py]
confidence: high
---

# Diffusion parallel transport 配置规则

## VOMNI-CFG-1q — SymmMem Ulysses transport 开关必须完整投影且默认关闭

- 触发：新增/修改 diffusion 并行 transport flag、`StageDeployConfig`、`OmniStageDiffusionParallelConfig`、default diffusion stage 或 `serve` CLI。
- 强制：`ulysses_a2a_permute` 在 deploy、structured parallel config、legacy/default-stage construction 和 CLI 都以同一 bool 字段传递；省略时最终值为 false，显式 true 必须到达 strict-Ulysses consumer，不能由 `ulysses_degree` 或其他 SP mode 隐式开启。
- 禁止：只在 parser/dataclass 声明、在 default stage 或 deploy merge 丢失；以 truthiness 吞掉明确 false；把 `advanced_uaa`、Ring 或 AllGather 配置解释为已启用 SymmMem；将 JIT/capability failure 推迟到首个请求。
- 验收：覆盖 CLI true/false、deploy true、structured/default-stage true 与 omitted false，断言最终 `parallel_config`；再由 DIFF-4x 覆盖 eligible consumer init 与不合资格组合不走 fused path。^[PR #6340]
