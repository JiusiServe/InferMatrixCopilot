---
title: "SoulX-Singer（SVS/SVC 歌声流匹配 + 内联神经预处理）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/soulx_singer/, vllm_omni/model_executor/models/soulx_singer/pipeline.py, vllm_omni/deploy/soulxsinger_svs.yaml]
---

# SoulX-Singer

以下事实在 `main @ 5d44868e` 复核。

## 名称与范围

- 正式名称 SoulX-Singer（Soul-AILab）歌声家族,两条单 stage diffusion
  pipeline（各自单 stage 0 `dit`,`execution_type=DIFFUSION`,final 音频
  输出,**无 connectors**）：**SVS**（乐谱/歌词驱动合成;registry 架构键
  `SoulXSingerPipeline`,pipeline key `soulxsinger_svs`,pre-process
  `get_soulxsinger_pre_process_func`）与 **SVC**（歌声转换;架构键
  `SoulXSingerSVCPipeline`,key `soulxsinger_svc`,pre-process
  `get_soulxsinger_svc_pre_process_func`）——这些是架构/注册标识,不是模型
  别名。
  **命名陷阱**：registry key `SoulXSingerPipeline`（checkpoint config.json
  的 architectures 值）加载的类是 `PipelineSoulXSingerSVS`;
  `SoulXSingerSVCPipeline` → `PipelineSoulXSingerSVC`——grep 时勿被
  key/类名错位误导。
- 虽是单 stage diffusion,**两个 key 都在 `OMNI_PIPELINES`**;少数注册了
  diffusion **pre**-process 的音频家族——神经预处理栈在 `pre_process_func`
  内**懒加载内联运行**,产出音频/F0 载荷,且按变体取用：SVS 走歌词 ASR
  （Paraformer/Parakeet）+ ROSVOT MIDI/note 条件;SVC 走 RMVPE F0,
  **MIDI 强制关闭**;人声分离（BS-RoFormer）对两者都是可选项
  （`vocal_sep`）。**冻结 Whisper 特征不在预处理里,而由
  `PipelineSoulXSingerSVC` 在条件构建阶段计算**。
- 入口路径：registry `vllm_omni/diffusion/registry.py` 与
  `vllm_omni/config/pipeline_registry.py`;拓扑
  `model_executor/models/soulx_singer/pipeline.py`;实现
  `diffusion/models/soulx_singer/`（base/svs/svc 三个 pipeline 文件 +
  `modules/` + `preprocess/`）;deploy
  `vllm_omni/deploy/soulxsinger_{svs,svc}.yaml`;无 stage input processor、
  无 AR 入口。
- **双仓权重** + 一个 HF 不发的文件：`Soul-AILab/SoulX-Singer`（合成）+
  `Soul-AILab/SoulX-Singer-Preprocess`（预处理）,另需从 GitHub 手拷
  `phoneme/phone_set.json`（e2e 测试的报错信息就是这么教的——部署陷阱）。
- 依赖共享模块：[Diffusion 组件](../../components/diffusion/_index.md)
  （CFGParallelMixin、组件发现/offload 分组）。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 三层输入、prompt 拼接 inpainting、自管权重 | [architecture](architecture.md) | 数据流与 reviewer 陷阱 |

## 配置与 checkpoint 差异

- 两份 deploy **只差 `pipeline:` 键**（fp16、32 步、guidance 3.0、单卡
  `gpu_memory_utilization: 0.5`、seed 42）,**都不 pin checkpoint ID**;
  离线 README 要求分别建 SVS/SVC 的 "view" 目录并手拷 `phone_set.json`。
- extra-body 面在 pipeline 类的 ClassVar（无 model_extras 文件）：SVS 收
  metadata/语言/control/max_merge_duration…出 `f0_shift`;SVC 收 wav/F0 路径
  出 `pitch_shift`（`auto_shift` 支持,SVC 移调 = `pitch_shift×5` 粗 F0 bin）。
- 自动化测试仅见离线 e2e（`test_soulxsinger.py`）;本次调查未发现在线示例
  的 CI 覆盖。

## 什么时候查这里

- 审查 soulx 的预处理栈、双仓布局或 SVS/SVC 条件差异;新加"带内联预处理的
  diffusion 家族"时以本家族为形态参考。
- 语义验收见 [model-validation](../../review/guides/model-validation.md)。
