---
title: "缓存加速（cache_dit / TeaCache / stepcache / magcache）"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, components, diffusion]
sources: [docs/design/feature/cache_dit.md, docs/design/feature/teacache.md, vllm_omni/diffusion/cache/]
---

# 缓存加速（cache_dit / TeaCache / stepcache / magcache）

官方 spec：`docs/design/feature/{cache_dit,teacache,prefix_caching}.md`；源码
`vllm_omni/diffusion/cache/`（`base.py`、`selector.py`、`cache_dit_backend.py`、
`teacache/`、`stepcache/`、`magcache/`、`prompt_embed_cache.py`——
`main @ 5c390096` 复核）。

- **Cache-DiT**：DiT 加速库，跨 denoise step 缓存中间计算——相邻步的中间特征相似，
  可复用缓存跳过冗余计算；支持三类缓存策略；标准架构自动支持，自定义架构需按
  spec 写自定义实现（参照实现：Qwen-Image、LongCat-Image pipeline）。
- **TeaCache**：当相邻 timestep 的调制输入（归一化 + timestep conditioning 后）
  L1 距离低于阈值时，复用上一步 transformer block 残差——**1.5x–2.0x 加速**、
  质量损失极小（参照实现：Qwen-Image transformer）。
- 其他后端：`stepcache/`、`magcache/`（同一 selector 框架下的策略变体）、
  `prompt_embed_cache.py`（prompt 嵌入缓存）、`prefix_caching.md`（diffusion 侧
  前缀缓存语义）。
- 兼容性例外：registry 的 `_NO_CACHE_ACCELERATION = {"NextStep11Pipeline",
  "AudioXPipeline"}`——这两条 pipeline 不支持 cache_dit/tea_cache。

## 相关

- 后端选择入口在 `diffusion/registry.py::initialize_model`（加载类、量化、VAE
  slicing/tiling、并行注入的同一初始化链）；组件边界见 [architecture](../architecture.md)。
