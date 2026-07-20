---
title: "Ming-Omni-TTS 规则"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [vllm-omni, models, model-executor]
sources: ["PR #4341"]
confidence: high
---

# Ming-Omni-TTS 规则

只有 `MING-数字字母` 是可审计规则 ID。

## MING-1a — CFM graph 保持 eager 的 float32 solver 边界

- 触发：修改 `fm/cfm_cudagraph.py`、solver、noise/timestep 或 DiT cast。
- 强制：初始 noise、timesteps、SDE random/state 和积分保持 float32；只在 DiT forward
  边界转模型 dtype，最终 latent 再按 eager 合同 cast。
- 禁止：为减少 cast 把整段 ODE solve 降为 bf16；shape 和无 NaN 仍可能掩盖音频漂移。
- 验收：固定 noise/condition 下逐步比较 eager 与 graph state，覆盖默认 temperature=0。 ^[PR #4341]

## MING-1b — CFG 近零分支与 eager 一致

- 触发：`cfg < 1e-5` 或 graph capture 中 cfg 作为 CUDA tensor。
- 强制：保留 eager unconditional 分支；graph 无法安全表达时明确回退 eager。
- 禁止：始终执行 cond/uncond chunk 和 CFG 公式，改变 cfg=0 的语义。
- 验收：cfg=0、阈值两侧和正常 cfg 的 eager/graph 输出分别对齐。 ^[PR #4341]

## MING-1c — graph 最后一步更新复刻 Solver.integrate

- 触发：手写或展开 ODE/SDE step loop。
- 强制：核对每一步 dt/shift、最后一步 SDE 更新与 `Solver.integrate` 的确切顺序。
- 禁止：用中间 step 的通用公式处理最后一步，或只比较前 N-1 步。
- 验收：逐步状态和最终 latent 同时对齐，测试必须单独断言最后一步。 ^[PR #4341]

## MING-2a — MoE-only 依赖保持 lazy import

- 触发：dense/MoE 共用 package `__init__`、config 或 model factory。
- 强制：只在确认 MoE 分支后 import 新 vLLM MoE module；dense import 路径不依赖它。
- 禁止：顶层导入 MoE-only 模块，导致旧 vLLM 或 dense-only 环境无法 import Ming-TTS。
- 验收：缺 MoE module 时 dense 模型可 import/构造；选择 MoE 时给出明确版本/依赖错误。 ^[PR #4341]

共享 graph/eager 规则见 [Diffusion DIFF-1a](../../components/diffusion/rules.md)；
模型语义证据矩阵见 [model validation](../../review/guides/model-validation.md)。
