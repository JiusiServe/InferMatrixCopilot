---
title: "加新模型：三条官方路径与四个注册点"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, dev]
sources: [docs/contributing/model/adding_omni_model.md, docs/contributing/model/adding_diffusion_model.md, docs/contributing/model/adding_tts_model.md]
---

# 加新模型：三条官方路径与四个注册点

官方 spec（`main @ 5c390096` 复核）：
`docs/contributing/model/adding_omni_model.md`（多 stage omni，以 Qwen3-Omni 为
完整示例——目录结构/关键组件/注册/stage 配置/stage input processor/测试/recipe
九节）、`adding_diffusion_model.md`（纯 diffusion pipeline）、
`adding_tts_model.md`（TTS）。仓库内的 `.claude/skills/add-*` 打包了同样的工作流。

## 四个注册点（漏一个都跑不起来）

| 注册点 | 位置 | 作用 |
|---|---|---|
| AR/omni 架构 | `model_executor/models/registry.py` `_OMNI_MODELS` | HF arch 名 → 模块/类 |
| Diffusion pipeline | `diffusion/registry.py` `_DIFFUSION_MODELS` | pipeline 类 → 模块 |
| Pipeline（model_type） | `config/pipeline_registry.py` `OMNI_PIPELINES` | model_type → 冻结拓扑/resolver（单 stage diffusion 不注册） |
| Deploy YAML | `vllm_omni/deploy/<model>.yaml` | bundled 默认部署 |

另有：跨 stage 转换 `stage_input_processors/<model>.py`（`ar2diffusion` 等）、
serving TTS 适配 `entrypoints/openai/tts_adapters/`、`recipes/<Org>/<Model>.md`。

## 照抄谁

参照清单见 [reference-models](../../models/reference-models.md)（GLM-Image /
BAGEL）与 [qwen-omni](../../models/qwen-omni/_index.md)；当前注册全量见
[models/catalog](../../models/catalog.md)。

## 验收档位

plumbing 绿灯（0 missing/0 unexpected、shape smoke、mock 权重）**不等于**语义
正确——semantic parity 矩阵与逐入口验收见
[model-adaptation-guardrails](../../review/guides/model-adaptation-guardrails.md)
与仓库 [rules.md](../../rules.md) 第 3 节。
