---
title: "模型目录快照（registry 派生）"
created: 2026-07-16
updated: 2026-07-21
type: guide
tags: [vllm-omni, models]
sources: [vllm_omni/model_executor/models/registry.py, vllm_omni/diffusion/registry.py, vllm_omni/config/pipeline_registry.py, vllm_omni/deploy/]
---

# 模型目录快照（registry 派生）

从四个注册点**机械派生**的模型清单,快照于 `main @ 5d44868e`（2026-07-21）。
数字会漂移——需要精确清单时用文末命令重派生,不要凭本页断言"不支持"。

## 四个注册点与计数

| 注册点 | 位置 | 计数 |
|---|---|---|
| AR/omni 架构 | `model_executor/models/registry.py` `_OMNI_MODELS` | 69 个架构名 / 26 个模型族目录 |
| Diffusion pipeline | `diffusion/registry.py` `_DIFFUSION_MODELS` | 59 条 pipeline / 35 个模型族目录 |
| Pipeline（model_type） | `config/pipeline_registry.py` `OMNI_PIPELINES` | 46 个 key |
| Deploy YAML | `vllm_omni/deploy/*.yaml` | 65 份 |

对比上一快照（`5c390096`,2026-07-16）：diffusion pipeline 58→59,
OMNI_PIPELINES 39→46,deploy 58→65——新增的 key 集中在视频/歌声/机器人
（`hunyuan_video_15`、`wan2_2_ti2v`、`soulxsinger_svs/svc`、
`step_audio_2`、`step_audio_2_asr`、`Gr00tN1d7`）,多 stage 化趋势在继续。

## AR/omni 模型族（26）

aura_omni、bagel、cosyvoice3、covo_audio、dynin_omni、fish_speech、glm_image、
glm_tts、higgs_audio_v2、higgs_audio_v3、hunyuan_image3、indextts2、
mammoth_moda2、mimo_audio、ming_flash_omni、ming_tts、minicpmo_4_5、moss_tts、
moss_tts_nano、omnivoice、qwen2_5_omni、qwen3_omni、qwen3_tts、step_audio2、
voxcpm2、voxtral_tts

## Diffusion 模型族（35）

audiox、bagel、cosmos3、diffusers_adapter（通用 diffusers 桥）、dreamid_omni、
dreamzero、ernie_image、flux、flux2、flux2_klein、glm_image、gr00t、helios、
hidream_image、hunyuan_image3、hunyuan_video、internvla_a1、krea2、lance、
longcat_image、ltx2、magi_human、ming_flash_omni、nextstep_1_1、omnigen2、
omnivoice、ovis_image、qwen_image、sd3、sdxl、sensenova_u1、soulx_singer、
stable_audio、wan2_2、z_image

## OMNI_PIPELINES key（46）

Gr00tN1d7（注意:唯一 CamelCase key）、aura_omni、bagel、bagel_single_stage、
bagel_think、cosyvoice3、covo_audio、dreamzero、dynin_omni、fish_qwen3_omni、
glm_image、glm_tts、higgs_audio_v2、higgs_multimodal_qwen3、hunyuan_image3_ar、
hunyuan_image3_dit、hunyuan_image_3_moe、hunyuan_video_15、indextts2、lance、
mammoth_moda2、mammoth_moda2_ar、mimo_audio、ming_flash_omni、
ming_flash_omni_image、ming_flash_omni_thinker_only、ming_flash_omni_tts、
ming_tts、ming_tts_moe、minicpmo_4_5、moss_tts_delay、moss_tts_local、
moss_tts_nano、moss_tts_realtime、omnivoice、qwen2_5_omni、
qwen2_5_omni_thinker_only、qwen3_omni_moe（resolver）、qwen3_tts、
soulxsinger_svc、soulxsinger_svs、step_audio_2、step_audio_2_asr、voxcpm2、
voxtral_tts、wan2_2_ti2v

注意：单 stage diffusion 模型**多数不在** `OMNI_PIPELINES`（引擎为它们生成
默认 diffusion stage 配置,见 [Config 组件](../components/config/architecture.md)）;
但存在例外——omnivoice、soulxsinger、Gr00tN1d7、lance、dreamzero 等单 stage
家族也有显式 key,勿以"在不在 OMNI_PIPELINES"倒推 stage 数。

## 重派生方法

```bash
git -C <vllm-omni> fetch origin main
git -C <vllm-omni> show origin/main:vllm_omni/diffusion/registry.py | grep -c '":'
# 或在 python 里 import 两个 registry 与 OMNI_PIPELINES 计数
```

有专属沉淀页的模型见 [models/_index](_index.md)（2026-07-21 起全部家族均有
落脚页）;参照用途见 [reference-models](reference-models.md)。
