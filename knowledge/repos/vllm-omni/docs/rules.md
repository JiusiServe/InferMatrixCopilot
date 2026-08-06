---
title: "vLLM-Omni 文档规则"
created: 2026-08-06
updated: 2026-08-06
type: rule
tags: [vllm-omni, docs]
sources: [README.md, docs/README.md, docs/configuration/README.md, docs/getting_started/installation/README.md, docs/getting_started/installation/gpu/cuda.inc.md, docs/getting_started/installation/npu/npu.inc.md, "PR #5715"]
confidence: high
---

# vLLM-Omni 文档规则

只有 `DOCS-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则组 | 第一批文档 |
|---|---|---|
| release/version、compatibility、CUDA/NPU image、supported models | DOCS-1a | root/docs README → configuration upstream link → installation index 与 GPU/NPU includes |

## DOCS-1a — release version 与支持声明必须作为一个文档集合更新

- 触发：发布 vLLM-Omni 版本，更新 vLLM compatibility、安装命令、CUDA/NPU 镜像或支持
  模型列表。
- 强制：同一变更同步核对 root README 的发布公告/节奏、configuration 的 upstream 链接、
  installation compatibility、CUDA package/image pin、NPU branch/image pin 和 supported-model
  声明；每处版本都来自本次发布矩阵，而不是从相邻示例复制。
- 禁止：只更新首页版本而保留旧安装 pin；CUDA 与 NPU 文档指向不同发布代际；链接文字
  已更新但目标仍是旧 upstream；用一次发布的具体版本号写成永久规则。
- 验收：对文档树做 repository-wide 的旧版本/旧分支扫描并逐个归类预期保留项；严格模式
  构建完整文档，检查内部链接、includes 与导航；从每个公开安装入口回读到同一兼容矩阵。
  ^[PR #5715]

owner 边界见 [vLLM-Omni 文档索引](_index.md)；跨仓库写作方法见
[通用文档知识](../../../general/docs/_index.md)，仓库级规则见 [vLLM-Omni rules](../rules.md)。
