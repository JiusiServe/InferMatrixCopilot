---
title: "Maintainer pattern owner 路由"
created: 2026-07-20
updated: 2026-07-20
type: guide
tags: [vllm-omni, review]
sources: ["PR #3576", "PR #3642", "PR #4106", "PR #4281", "PR #4341", "PR #4718", "PR #4730", "PR #4980", "PR #5001", "PR #5031", "PR #5037", "PR #5052", "PR #5084", "PR #5087", "PR #5088", "PR #5136", "PR #5157"]
confidence: high
---

# Maintainer pattern owner 路由

本页只负责把 review diff 路由到知识 owner，不复制各 owner 的规则。看到关键词不能直接
报 finding；必须先证明当前 diff 的 producer、consumer、失败路径与链接规则一致。
通用执行合同见 [review execution contract](../../../../general/review/guides/review-execution-contract.md)。

## 先固定 diff，再选 owner

1. 记录 review head 和 base；base 不是 head 祖先时使用 merge-base，不能把后来 main 的
   改动算进 PR。
2. 按 changed files 建 scope ledger，每个 scope 至少覆盖一次；再按 churn 与跨模块调用
   链分配深度，不能只读一个醒目大文件。
3. finding 的改动点必须位于 pinned diff；未改文件只能证明影响链，不能把既有问题冒充
   本 PR 回归。
4. 先命中下表的一个主 owner。只有 live 调用链跨模块时才打开第二 owner，避免横向加载
   整棵知识树。

## Changed-file / 风险到 owner

| Diff 或风险信号 | 主 owner | 重点 |
|---|---|---|
| `tests/diffusion/quantization`、可选包 import、硬件支持文档 | [CI environment](../../ci/guides/ci-environment-gotchas.md) | 未安装环境、真实 kernel、claim 一致性 |
| benchmark 脚本、percentile、warmup、replica isolation | [performance evidence](../../benchmark/guides/performance-evidence.md) | 计时、统计、失败退出、完整 key set |
| 模块移动、compat shim、重复 class/schema | [API surface](../../../../general/review/guides/code-taste-api-surface.md) | identity、旧行为、返回合同 |
| checkpoint adapter、component quantization、graph/eager、HSDP/FSDP | [Diffusion rules](../../components/diffusion/rules.md) | namespace/consumer、数值 parity、真实 fully_shard |
| composable strategy、stage YAML、headless override | [Config rules](../../components/config/rules.md) | wired axis、拓扑单源、显存预算 |
| runtime bridge、`runtime_info`、`OmniOutput` | [Model Executor rules](../../components/model-executor/rules.md) | producer→consumer、逐请求 batch |
| prefix-cache side stream、pinned host tensor | [Scheduler rules](../../components/scheduler/rules.md) | buffer 生命周期、CPU fallback |
| SSE/audio format、artifact readiness、Prometheus replica stats | [Serving rules](../../components/serving/rules.md) | 首 chunk 前校验、cache capability、owner 生命周期 |
| Cosmos3 Edge/Distilled | [Cosmos3 rules](../../models/cosmos3/rules.md) | scheduler、RNG、zero、offload |
| FLUX.2、Mistral text encoder FP8 | [FLUX.2 rules](../../models/flux2/rules.md) | component prefix、量化排除项、meta/offload |
| Krea 2 | [Krea 2 rules](../../models/krea2/rules.md) | dtype、config fetch、online/capability |
| MiniCPM-o 4.5 | [MiniCPM-o rules](../../models/minicpm-o-4-5/rules.md) | registry、remote code、TTS bridge/batch |
| Ming dense/MoE、CFM CUDA Graph | [Ming-TTS rules](../../models/ming-omni-tts/rules.md) | solver dtype、CFG、last step、lazy import |
| Qwen3-TTS、`ref_audio`、x-vector/ICL | [Qwen3-TTS rules](../../models/qwen3-tts/rules.md) | readiness 方向、一次重算、engine 存活 |

## 完成标准

大 diff 最终按 scope ledger 回看 loader/registry/bridge/output、RNG/优化 parity、streaming
preflight、并行设备合同和异步资源生命周期是否实际适用并已检查。输出 comment 时包含：

- 当前 diff 做了什么；
- 沿哪个调用/数据路径造成什么用户或系统结果；
- 验证过的文件、测试或命令；
- 本 PR 内的具体最小修法。

只有关键词相似、尚未验证 consumer 的内容留在调查记录，不作为阻塞意见。新模型还需
同时使用 [model adaptation guardrails](model-adaptation-guardrails.md) 和
[model validation](model-validation.md)。
