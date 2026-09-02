---
title: "vLLM-Omni 模型 owner"
created: 2026-07-10
updated: 2026-09-02
type: index
tags: [vllm-omni, models]
sources: []
---

<!-- children: filesystem -->

# 模型 owner

模型目录就是清单，不再在本页手工复制几十个目录名。

```powershell
Get-ChildItem knowledge/repos/vllm-omni/models -Directory |
  Select-Object -ExpandProperty Name
```

## 怎么选

1. PR title/body 有明确模型名：直接进入同名目录。
2. 名称、别名或 registry key 不确定：查
   [catalog / Direct 模型代码入口](catalog.md#direct-模型代码入口)。
3. 需要找相近实现：查 [reference models](reference-models.md)。
4. 目录只有 `_index.md` 时，把它当源码落脚页；有 `rules.md` 时优先读规则；
   只有需要解释完整拓扑时才读 `architecture.md`。

PersonaPlex 的 staged 与 unified full-duplex 双入口、Mimi 状态和 lockstep 合同见
[PersonaPlex owner](personaplex/_index.md)。

选择一个模型 owner 后停止枚举其他模型。跨模型共用的不变量应进入
[components](../components/_index.md)，不要复制到多个模型目录。
