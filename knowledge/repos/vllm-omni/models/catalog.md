---
title: "模型代码入口与 registry 快照"
created: 2026-07-16
updated: 2026-08-05
type: guide
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/registry.py, vllm_omni/diffusion/registry.py, vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/]
---

# 模型代码入口与 registry 快照

本页提供模型描述到代码目录的自动定位入口，不维护逐模型 class 映射。下方计数是
`main @ fbea7886`（2026-08-04）快照，数字会漂移，不能凭它断言“不支持”。

## Direct 模型代码入口

从 PR title/body 提取模型名、architecture 或 `model_type`，一次性搜索：

1. `vllm_omni/model_executor/models/registry.py::_OMNI_MODELS`
2. `vllm_omni/diffusion/registry.py::_DIFFUSION_MODELS`
3. `vllm_omni/config/pipeline_registry.py::OMNI_PIPELINES`

registry tuple 给出 folder、module 和 class 后，直接进入：

- AR/omni：`vllm_omni/model_executor/models/<folder>/`
- diffusion：`vllm_omni/diffusion/models/<folder>/`

命中 `OMNI_PIPELINES` 时继续打开对应 pipeline 定义，补齐多 stage 的所有模型目录。若正式
名称和目录 slug 不同（如 MiniCPM-o → `minicpmo_4_5`），以 registry 结果为准；若一个
模型同时命中 AR 和 diffusion（如 GLM-Image），两个目录都进入初始 scope。然后再用
changed files 校验是否还跨到 `model_extras/`、`stage_input_processors/` 或 serving
adapter。已有专属知识 owner 可从 [models index](_index.md) 按名称进入。

## 四个注册点与计数

| 注册点 | 位置 | 计数 |
|---|---|---|
| AR/omni 架构 | `model_executor/models/registry.py` `_OMNI_MODELS` | 77 个架构名 / 27 个模型族目录 |
| Diffusion pipeline | `diffusion/registry.py` `_DIFFUSION_MODELS` | 58 条 pipeline / 38 个模型族目录 |
| Pipeline（model_type） | `config/pipeline_registry.py` `OMNI_PIPELINES` | 51 个 key |
| Deploy YAML | `vllm_omni/deploy/*.yaml` | 79 份 |

对比上一审计快照（`807db6ef`）：AR 架构 72→77，diffusion pipeline 61→58，
OMNI_PIPELINES 46→51，deploy 71→79。新增 AR 家族是 `audex`；diffusion 新增
`minimax_h3`，同时 LTX-2/LTX-2.3 的五个旧 registry names 合并为两个入口。新增
pipeline keys 是四个 Audex 模式和 `nemotron_labs_audex` alias；deploy 新增八个
Audex files 与 `qwen3_omni_moe_thinking.yaml`，删除 `minicpmo_4_5_batching.yaml`。

## AR/omni 模型族（27）

aura_omni、audex、bagel、cosyvoice3、covo_audio、dynin_omni、fish_speech、glm_image、
glm_tts、higgs_audio_v2、higgs_audio_v3、hunyuan_image3、indextts2、
mammoth_moda2、mimo_audio、ming_flash_omni、ming_tts、minicpmo_4_5、moss_tts、
moss_tts_nano、omnivoice、qwen2_5_omni、qwen3_omni、qwen3_tts、step_audio2、
voxcpm2、voxtral_tts

## Diffusion 模型族（38）

audiox、bagel、boogu_image、cosmos3、diffusers_adapter（通用 diffusers 桥）、dreamid_omni、
dreamzero、ernie_image、flux、flux2、flux2_klein、glm_image、gr00t、helios、
hidream_image、hunyuan_image3、hunyuan_video、internvla_a1、krea2、lance、
lingbot_video、longcat_image、ltx2、magi_human、ming_flash_omni、nextstep_1_1、omnigen2、
omnivoice、ovis_image、qwen_image、sd3、sdxl、sensenova_u1、soulx_singer、
stable_audio、wan2_2、z_image、minimax_h3

## OMNI_PIPELINES key（51）

Gr00tN1d7（注意:唯一 CamelCase key）、aura_omni、audex_s2s、audex_thinker_only、
audex_tta、audex_tts、bagel、bagel_single_stage、
bagel_think、cosyvoice3、covo_audio、dreamzero、dynin_omni、fish_qwen3_omni、
glm_image、glm_tts、higgs_audio_v2、higgs_multimodal_qwen3、hunyuan_image3_ar、
hunyuan_image3_dit、hunyuan_image_3_moe、hunyuan_video_15、indextts2、lance、
mammoth_moda2、mammoth_moda2_ar、mimo_audio、ming_flash_omni、
ming_flash_omni_image、ming_flash_omni_thinker_only、ming_flash_omni_tts、
ming_tts、ming_tts_moe、minicpmo_4_5、moss_tts_delay、moss_tts_local、
moss_tts_nano、moss_tts_realtime、omnivoice、qwen2_5_omni、
qwen2_5_omni_thinker_only、qwen3_omni_moe（resolver）、qwen3_tts、
soulxsinger_svc、soulxsinger_svs、step_audio_2、step_audio_2_asr、voxcpm2、
voxtral_tts、wan2_2_ti2v、nemotron_labs_audex

注意：单 stage diffusion 模型**多数不在** `OMNI_PIPELINES`（引擎为它们生成
默认 diffusion stage 配置,见 [Config 组件](../components/configuration/architecture.md)）;
但存在例外——omnivoice、soulxsinger、Gr00tN1d7、lance、dreamzero 等单 stage
家族也有显式 key,勿以"在不在 OMNI_PIPELINES"倒推 stage 数。

## 重派生方法

```bash
python tools/audit_vllm_omni_release.py \
  --from 78c144f3 \
  --to fbea7886 \
  --repo <vllm-omni-checkout> \
  --mode report-only
```

命令从 Git 对象读取 registry，不 import vLLM；机器基线与完整维护步骤见
`adapters/vllm_omni/release_baseline.yaml` 和
`doc/contributing/release-maintenance.md`。

已有专属沉淀页的模型见 [models/_index](_index.md)；没有专属规则的新家族先走共享
Diffusion owner。参照用途见 [reference-models](reference-models.md)。
