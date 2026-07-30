---
title: "PR intent 到 maintainer owner 路由"
created: 2026-07-20
updated: 2026-07-30
type: guide
tags: [vllm-omni, review]
sources: ["InferMatrixCopilot Issue #24", "PR #3576", "PR #3642", "PR #4106", "PR #4281", "PR #4341", "PR #4718", "PR #4730", "PR #4980", "PR #5001", "PR #5031", "PR #5037", "PR #5052", "PR #5084", "PR #5087", "PR #5088", "PR #5136", "PR #5157"]
confidence: high
---

# PR intent 到 maintainer owner 路由

本页只负责把 PR title/body 的声明目标路由到知识 owner，不复制各 owner 的规则。changed
files 用于校验真实范围，不是首要导航。看到关键词不能直接报 finding；必须先证明当前
diff 的 producer、consumer、失败路径与链接规则一致。
通用执行合同见 [review execution contract](../../../../general/review/guides/review-execution-contract.md)。

## 先固定快照，再按描述选 owner

1. 记录 review head 和 base；base 不是 head 祖先时使用 merge-base，不能把后来 main 的
   改动算进 PR。
2. 一次性读取 PR title/body，用声明的模型、组件、迁移目标、公开入口或核心符号命中
   下表的主 owner，再进入该 owner 的快速代码地图选择规则组和第一批源码。
3. 一次性解析 changed files 和完整 diff，验证描述路由是否覆盖所有真实 scope；描述与
   diff 冲突时以 diff 为准并明确记录，不能静默换 owner。
4. 生成共享路由包：`owner/model → 规则组 → 第一批源码 → changed files`。后续 caller
   搜索、测试和 findings 只向这份包追加，不能让 correctness、subtraction 或专项各自重走。
5. finding 的改动点必须位于 pinned diff；未改文件只能证明影响链，不能把既有问题冒充
   本 PR 回归。只有 live 调用链跨模块时才增加第二 owner。

## PR 描述 / 风险到 owner

| PR 描述或风险信号 | 主 owner | 重点 |
|---|---|---|
| HunyuanImage3、`model_extras`、shared task examples、`extra_body`、AR prompt/tokenizer | [HunyuanImage3 rules](../../models/hunyuan-image3/rules.md) | 按描述命中快速代码地图；registry、server/offline seam、默认值与 fallback |
| `tests/diffusion/quantization`、可选包 import、硬件支持文档 | [CI environment](../../ci/guides/ci-environment-gotchas.md) | 未安装环境、真实 kernel、claim 一致性 |
| benchmark 脚本、percentile、warmup、replica isolation | [performance evidence](../../benchmark/guides/performance-evidence.md) | 计时、统计、失败退出、完整 key set |
| 模块移动、compat shim、重复 class/schema | [API surface](../../../../general/review/guides/code-taste-api-surface.md) | identity、旧行为、返回合同 |
| checkpoint adapter、component quantization、graph/eager、HSDP/FSDP | [Diffusion rules](../../components/diffusion/rules.md) | namespace/consumer、数值 parity、真实 fully_shard |
| composable strategy、stage YAML、headless override | [Config rules](../../components/configuration/rules.md) | wired axis、拓扑单源、显存预算 |
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
preflight、并行设备合同和异步资源生命周期是否实际适用并已检查。整个 pinned head 只
输出一篇 comment，包含：

- 当前 diff 做了什么；
- 沿哪个调用/数据路径造成什么用户或系统结果；
- 验证过的文件、测试或命令；
- 本 PR 内的具体最小修法。

主审查已经收集的文件、caller 搜索、测试和 findings 必须直接复用。只有关键词相似、
尚未验证 consumer 的内容留在调查记录，不作为阻塞意见；只有新颖、矛盾或未覆盖的高风险
合同才发起有边界的专项追问。新模型还需同时使用
[model adaptation guardrails](model-adaptation-guardrails.md) 和
[model validation](model-validation.md)。
