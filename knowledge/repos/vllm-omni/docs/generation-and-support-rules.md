---
title: "Generated docs and supported-model evidence rules"
created: 2026-08-10
updated: 2026-08-10
type: rule
tags: [vllm-omni, docs]
sources: [.claude/skills/quantization/references/modelopt-fp8.md, docs/.nav.yml, docs/mkdocs/hooks/generate_examples.py, docs/models/supported_models.md, recipes/README.md, tests/docs/test_generate_examples.py, "PR #5969"]
---

# Generated docs and supported-model evidence rules

只有 `DOCGEN-数字字母` 是可审计规则 ID。模型实际能力仍回 model/component owner；本页只拥有
生成文档的 URL/navigation 与 supported-model recipe 证据边界。

## DOCGEN-1a — 页面 URL 与 navigation 分类是两个独立合同

- 触发：移动 example 分类、修改 `generate_examples.py`、MkDocs Features/Examples navigation，
  或增删 quantization example source。
- 强制：generated page URL 始终从 source category/stem 派生；改变导航归属不能改旧 URL。
  `examples/quantization/<name>` 的页面若存在，仍生成到
  `user_guide/examples/quantization/<name>.md`，但 nav 只挂在 User Guide → Features →
  Quantization → Generated Examples，不能同时创建 Examples → Quantization。
- 禁止：用 nav 目标目录重写生成 URL；覆盖 hand-authored Quantization items；重复 build 累加
  Generated Examples；目标 Features/Quantization 缺失时退回错误的 Examples 分类。
- 验收：连续运行两次仍只有一个 hook-owned group，保留 Overview 等手写项；下一次无
  quantization source 时清掉 stale generated group；目标 section 缺失时不挂载并记录 warning。
  当前 `examples/quantization/*.py` 已全部删除，因此 target build 不应生成这些页面或链接；规则
  保护未来重新增加 source 时的旧 URL。^[PR #5969]

### 已知完整性缺口

- target 的 `.claude/skills/quantization/references/modelopt-fp8.md` 仍要求运行已删除的
  `examples/quantization/check_modelopt_fp8_export.py`。现有
  `tests/docs/test_generate_examples.py` 用构造的 `SimpleNamespace.path` 验证 nav mutation，
  不会发现这种 repository 内的悬空引用。完成该清理需要更新 skill reference，并增加覆盖真实
  仓库路径/链接存在性的检查；在此之前不能把“删除 quantization examples”视为引用完整性已验收。

## DOCGEN-1b — Recipe link 与硬件 checkmark 必须共享可审计证据

- 触发：修改 `docs/models/supported_models.md` 的 Recipe 或 hardware 列、增加 recipe，或发布
  `recipes.vllm.ai` 页面。
- 强制：Recipe 列是 model row → deployment recipe 的直接映射；有已确认 published page 时优先
  链它，否则链 repository recipe，未审计 row 写 `—`。commands、参数和验证详情只由 recipe
  文件拥有，supported-model table 不复制。只有已审计 recipe 明示的硬件才能据此改该 row 的
  hardware checkmark；unlinked row 继续保留原 implementation-support metadata。
- 禁止：把 recipe 中仅用于 platform delta/config 的提及当成运行验证；因为另一个同架构 row
  有 recipe 就传播硬件结论；把空 hardware cell 解读为已证明不支持；为避免外链而复制 recipe
  命令到 supported-model table。
- 验收：逐个 linked row 检查 model identity、published/repository fallback、目标存在性和 recipe
  的显式硬件证据；未 linked rows 的硬件列不随本轮 audit 改动。#5969 审计的变化范围仅是
  Qwen3-Omni、Qwen-Image、Qwen-Image-2512、Qwen3-TTS CustomVoice、Higgs Audio V3 TTS 的
  NVIDIA，以及 MiniMax H3 的 NVIDIA+AMD；这不是其他 row 的平台支持 census。^[PR #5969]
