---
title: "关键模块与 Owner"
created: 2026-08-14
updated: 2026-08-14
type: guide
tags: [vllm-omni, components]
sources: []
---

# 关键模块与 Owner

记录 vLLM-Omni 中关键共享代码模块对应的 owner（负责人），用于 review、debug 和
benchmark 时快速路由到正确的人。模块清单以 [components 目录](../components/_index.md)
为准，本页只维护“模块 → owner”映射。相关入口：[owners 索引](_index.md)、
[关键模型与 Owner](model_owner.md)。

## 关键模块与 Owner

| 模块 | Owner | 备注 |
|---|---|---|
| Benchmark/metrics/profiler |  | 区至豪 |
| Config/deploy/pipeline/cli | 外部负责 | |
| scheduler |  | 杨蕊蕊 |
| coordinator | NumberWan | 温梓健 |
| Engine | | 郑晨光/吴艺辉 |
| input/output processor | tzhouam | 周太昶/Shi Bo ao |
| stage_input_processor | amy-why-3459 | 吴海燕 |
| platforms | FayeSpica | 廖维明 |
| Weight loading/transformers | NumberWan | 温梓健 |
| worker/modelrunner | tzhouam | 周太昶 |
| api_server |  | 戴昊曌 |
| OmniConnector | natureofnature/spencerr221 | 刘威志/Liu Bingyu |
| Quantization | david6666666 | 陈炜青 |
| Diffusion-attention | david6666666 | 陈炜青 |
| Diffusion-cache | yangjianjuan | 杨剑娟 |
| Diffusion-distributed | bjf-frz  | 白竞帆 |
| Diffusion-Executor/Scheduler/Worker/ModelRunner | fhfuih | 黄泽宇 |
| Diffusion-hooks/lora/layers/model_loader | congw729 | 王聪 |
| Diffusion-models/registry | congw729 | 王聪 |
| DiffusionEngine/StageDiffusionClient/IO | bjf-frz  | 白竞帆 |
| Diffusion-model_extras | TaffyOfficial | 温智仁 |
| Diffusion-config | TaffyOfficial | 温智仁 |
| Tests | yenuo26/zhumingjue138 | 王语/朱铭觉 |

