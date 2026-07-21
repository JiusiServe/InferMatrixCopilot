---
title: "SenseNova-U1（统一 LLM 即编码器即去噪器,无 VAE）"
created: 2026-07-21
updated: 2026-07-21
type: index
tags: [vllm-omni, models, diffusion]
sources: [vllm_omni/diffusion/models/sensenova_u1/, vllm_omni/diffusion/registry.py]
---

# SenseNova-U1

以下事实在 `main @ 5d44868e` 复核（源码派生页,尚无本模型的运行经验沉淀）。

## 名称与范围

- diffusion registry：`SenseNovaU1Pipeline` →
  （`sensenova_u1`, `pipeline_sensenova_u1`）,post
  `get_sensenova_u1_post_process_func`。单 stage diffusion,引擎默认 stage
  配置（[Config 组件](../../components/config/architecture.md)）。无 deploy YAML。
- 源码：`pipeline_sensenova_u1.py`（66 KB,内含 `NEOVisionModel`/
  `TimestepEmbedder`/`ConvDecoder`/`SenseNovaU1DenoisingAdapter`）+
  `sensenova_u1_transformer.py`（32 KB）+ `fused_rmsnorm_rope.py`
  （自定义融合核）。

## 结构与要点

- **统一模型**：同一个 Qwen3 LLM 既做文本编码（经 KV cache）又做去噪
  backbone（Mixture-of-Tokenizers attention 分支）;patch 空间 flow matching;
  **没有独立 VAE/文本编码器**——`ConvDecoder` 直接 patch→pixel。改"文本编码器
  /VAE 组件发现"共享逻辑时这是特例。
- transformer 层已 TP 移植（QKVParallelLinear/MergedColumnParallelLinear/
  RowParallelLinear,docstring）;权重加载走 `stacked_params_mapping`
  （融合 QKV/gate-up）;`CFGParallelMixin`。

## 什么时候查这里

- 审查 sensenova_u1 的统一编码/去噪路径、融合核或权重映射改动。
- 共享 RNG/graph 规则见 [Diffusion rules](../../components/diffusion/rules.md)。
