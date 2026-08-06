---
title: "AFD compatibility 规则"
created: 2026-08-06
updated: 2026-08-06
type: rule
tags: [afd-plugin, components, compatibility, review]
sources:
  - "afd-plugin@a432692:AGENTS.md"
  - "afd-plugin@a432692:afd_plugin/compat/**"
  - "afd-plugin@a432692:docs/design/module/compatibility_and_patches.md"
confidence: high
---

# AFD compatibility 规则

这些规则从 [仓库规则](../../rules.md) 迁入最近 owner，保留原有稳定 ID。

## AFD-3a — patch 必须 upstream-first 且可移除

触发：新增 patch、修改已有 patch 或升级 vLLM/vLLM-Ascend。

- 必须记录精确 upstream file/symbol/version/signature，优先复制对应版本函数，并保持签名和返回类型。
- AFD 差异必须用 `# ### PATCH START: ...` / `# ### PATCH END: ...` 标出；函数上方必须说明 patch reason、行为变化和 upstream/移除条件。
- 禁止在便利的全局 hook 中放置本应属于 AFD model、worker 或 connector 的功能。
- 验收：AFD 和 non-AFD 分支、初始化/失败/shutdown 及需要时的 reload/idempotence 都有 focused tests，并写明移除路径。

## AFD-3b — 上游 API drift 必须直接暴露

触发：访问 vLLM/vLLM-Ascend 结构、添加 fallback 或选择 original-function delegation。

- 必须直接访问预期上游函数和字段，让静态检查和原始错误暴露缺失/改名。
- 禁止用宽泛 `getattr`、`hasattr`、`Any`、`object` 或 `_original_*` delegation 掩盖 drift。只有 `AGENTS.md` 明确允许的超大/不适合内联函数例外才可 delegation，且必须就地解释。
- 验收：当前 pinned signature 对齐，故意缺失字段不会被 fallback 吞掉，保存的 original 不会在 reload 时被 wrapper 覆盖。

patch 生命周期见 [architecture](architecture.md)，版本支持声明见 [仓库规则](../../rules.md)。
