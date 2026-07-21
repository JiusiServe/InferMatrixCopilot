---
title: "InternVLA-A1（视觉-语言-动作机器人策略）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/internvla_a1/, vllm_omni/diffusion/registry.py]
---

# InternVLA-A1

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- **不是媒体生成模型**：vision-language-action 机器人策略（Qwen3-VL backbone +
  action-expert transformer + Cosmos flow-matching 动作头）,以"动作 pipeline"
  形态跑在 diffusion 引擎下。相关但独立的家族：[gr00t](../gr00t/_index.md)。
- diffusion registry：`InternVLAA1Pipeline` →
  （`internvla_a1`, `pipeline_internvla_a1`）,post
  `get_internvla_a1_post_process_func`（薄封装）。单 stage,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码（7 文件,尾部家族里最异构）：`model_internvla_a1.py`（41 KB,
  `Qwen3VLWithExpertModel`/`InternVLAA1Policy`/
  `resolve_cosmos_checkpoint_paths`）、`adapter_qwen3_vl.py`（重写的
  Qwen3-VL attention/caching 层）、`cosmos_ci_torch.py` + `model_cosmos.py`
  （Cosmos 动作扩散组件,家族内 vendor,勿与 cosmos3 视频家族混淆）、
  `config.py`（`OBS_IMAGES`/`OBS_STATE`/`OBS_TASK` 观测键 +
  `DEFAULT_QWEN3_VL_MODEL`/`DEFAULT_COSMOS_REPO`）。

## 结构与要点

- 输入是观测字典（images/state/task）而非 prompt;`SuffixStaticContext`
  静态 cache + `OPENPI_ATTENTION_MASK_VALUE`（OpenPI 风格掩码）。
- pipeline 用 `vllm_omni.diffusion.compile.regionally_compile`。

## 什么时候查这里

- 审查 VLA 观测输入、动作头或 Qwen3-VL adapter 改动;评审时先确认改动属于
  internvla_a1 还是 gr00t,两者不共享代码。
