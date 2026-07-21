---
title: "vLLM-Omni 模型"
created: 2026-07-10
updated: 2026-07-21
type: index
tags: [vllm-omni, models]
sources: []
---

# vLLM-Omni 模型

有运行经验沉淀（rules/incidents/history）的家族在上半表;2026-07-21 起,全部
registry 家族均有源码派生落脚页（`main @ 5d44868e` 复核,全量清单见文末
"全局入口"）。

## 有经验沉淀的家族

| 模型 | 查看哪里 |
|---|---|
| Cosmos3（常规 / Edge / Distilled） | [cosmos3](cosmos3/_index.md) |
| FLUX.2（含 Mistral text encoder FP8） | [flux2](flux2/_index.md) |
| HunyuanImage3 | [hunyuan-image3](hunyuan-image3/_index.md) |
| Krea 2 | [krea2](krea2/_index.md) |
| LTX-2 家族（含 2.3） | [ltx2](ltx2/_index.md) |
| MiniCPM-o 4.5 | [minicpm-o-4-5](minicpm-o-4-5/_index.md) |
| Ming-Omni-TTS（dense / MoE） | [ming-omni-tts](ming-omni-tts/_index.md) |
| Qwen-Omni 多模态家族（2.5/3） | [qwen-omni](qwen-omni/_index.md) |
| Qwen3-TTS（ref audio / artifact cache） | [qwen3-tts](qwen3-tts/_index.md) |

## 多 stage / 统一模型家族（源码派生）

| 模型 | 查看哪里 |
|---|---|
| BAGEL（多形态部署参照） | [bagel](bagel/_index.md) |
| GLM-Image（AR→DiT token 桥,i2i 参照） | [glm-image](glm-image/_index.md) |
| Lance(BAGEL 谱系统一模型) | [lance](lance/_index.md) |
| MammothModa2（DiT 跑在 LLM_GENERATION） | [mammoth-moda2](mammoth-moda2/_index.md) |
| Ming-flash-omni（BailingMM2,4 拓扑） | [ming-flash-omni](ming-flash-omni/_index.md) |
| Dynin-Omni（三 stage,远程代码为主） | [dynin-omni](dynin-omni/_index.md) |
| Aura-Omni（4-stage 组合管线） | [aura-omni](aura-omni/_index.md) |

## 语音/音频家族（源码派生）

| 模型 | 查看哪里 |
|---|---|
| Higgs-Audio V2/V3 | [higgs-audio](higgs-audio/_index.md) |
| MiMo-Audio（融合 thinker+talker） | [mimo-audio](mimo-audio/_index.md) |
| Step-Audio2（音频 token 内嵌词表） | [step-audio2](step-audio2/_index.md) |
| MOSS-TTS 家族（Delay/Realtime/Local/Nano） | [moss-tts](moss-tts/_index.md) |
| Fish Speech S2 Pro（fish_qwen3_omni） | [fish-qwen3-omni](fish-qwen3-omni/_index.md) |
| IndexTTS2（非流式两 stage） | [indextts2](indextts2/_index.md) |
| CosyVoice3（RAS 合并停止,TRT） | [cosyvoice3](cosyvoice3/_index.md) |
| VoxCPM2（单 stage AR,48 kHz） | [voxcpm2](voxcpm2/_index.md) |
| SoulX-Singer（SVS/SVC 歌声） | [soulx-singer](soulx-singer/_index.md) |
| Covo-Audio | [covo-audio](covo-audio/_index.md) |
| GLM-TTS | [glm-tts](glm-tts/_index.md) |
| OmniVoice（离散扩散 TTS） | [omnivoice](omnivoice/_index.md) |
| Voxtral TTS | [voxtral-tts](voxtral-tts/_index.md) |
| AudioX(文/视频条件音频) | [audiox](audiox/_index.md) |
| Stable Audio Open | [stable-audio](stable-audio/_index.md) |
| MagiHuman（音频驱动人像视频） | [magi-human](magi-human/_index.md) |

## 视频/机器人家族（源码派生）

| 模型 | 查看哪里 |
|---|---|
| Wan 2.2（六架构:T2V/I2V/VACE/S2V/DMD2） | [wan2-2](wan2-2/_index.md) |
| HunyuanVideo-1.5 | [hunyuan-video](hunyuan-video/_index.md) |
| Helios（分块长视频） | [helios](helios/_index.md) |
| DreamZero（VLA 世界模型,AR-Diffusion 引擎） | [dreamzero](dreamzero/_index.md) |
| GR00T N1.7（VLA,actions 输出） | [gr00t](gr00t/_index.md) |
| InternVLA-A1（VLA） | [internvla-a1](internvla-a1/_index.md) |
| DreamID-Omni（Wan 基座音视频身份） | [dreamid-omni](dreamid-omni/_index.md) |

## 图像家族（源码派生）

| 模型 | 查看哪里 |
|---|---|
| Qwen-Image（五变体） | [qwen-image](qwen-image/_index.md) |
| FLUX.1（base/Kontext/DMD2） | [flux](flux/_index.md) |
| FLUX.2-Klein | [flux2-klein](flux2-klein/_index.md) |
| HiDream-I1（MoE DiT） | [hidream-image](hidream-image/_index.md) |
| LongCat-Image（T2I+编辑） | [longcat-image](longcat-image/_index.md) |
| OmniGen2（指令图像生成/编辑） | [omnigen2](omnigen2/_index.md) |
| Ovis-Image | [ovis-image](ovis-image/_index.md) |
| ERNIE-Image | [ernie-image](ernie-image/_index.md) |
| NextStep-1.1（AR 图像生成） | [nextstep-1-1](nextstep-1-1/_index.md) |
| SenseNova-U1（统一 LLM,无 VAE） | [sensenova-u1](sensenova-u1/_index.md) |
| Z-Image | [z-image](z-image/_index.md) |
| SD3 | [sd3](sd3/_index.md) |
| SDXL（唯一 UNet/epsilon） | [sdxl](sdxl/_index.md) |
| Diffusers Adapter（通用黑盒桥） | [diffusers-adapter](diffusers-adapter/_index.md) |

## 全局入口

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 全量注册模型清单（registry 快照） | [catalog](catalog.md) | 四注册点机械派生 |
| 新模型适配的参照定位 | [reference-models](reference-models.md) | GLM-Image/BAGEL/Qwen-Omni 等 |
