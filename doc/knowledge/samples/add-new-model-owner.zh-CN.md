# 新模型还没有目录：复制完整 owner

把下面所有 `<model-slug>` 替换为小写英文目录名，例如 `my-new-model`；把其他
尖括号内容全部替换后再提交。

## 文件 1：`knowledge/repos/vllm-omni/models/<model-slug>/_index.md`

```markdown
---
title: "<模型正式名称>"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: index
tags: [vllm-omni, models]
sources: []
---

# <模型正式名称>

- 常见别名：`<别名>`
- 主要源码：`<vllm_omni/...>`
- 依赖的共享模块：<Diffusion / Model Executor / Serving 等>
- checkpoint、尺寸或量化差异：<没有则写“当前只有一个受支持版本”>

## 什么时候查这里

- 修改 <模型正式名称> 的模型专有实现、配置、checkpoint 或运行行为。

## 不放什么

- 多个模型共享的机制放到对应 `components/<模块>/`。

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 理解模型边界和数据流 | [architecture](architecture.md) |
| 修改或审核模型行为 | [rules](rules.md) |
```

## 文件 2：`knowledge/repos/vllm-omni/models/<model-slug>/architecture.md`

```markdown
---
title: "<模型正式名称> 架构"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: architecture
tags: [vllm-omni, models]
sources: [<主要源码路径>]
---

# <模型正式名称> 架构

## 模型专有部分与共享模块的边界

- 专有：<该目录真正负责什么>
- 共享：<依赖哪些 component；哪些内容不在这里维护>

## 配置、checkpoint 和兼容范围

- <支持的 checkpoint、尺寸、量化和必要配置>

## 从输入到输出的主要流程

- <公开入口> → <processor> → <模型执行> → <输出>

## 怎样验证功能、精度和性能

- 功能：<真实入口和最小用例>
- 精度：<基线、数据和指标>
- 性能：<固定 workload 和指标>

相关入口：[模型索引](_index.md)；[开发规则](rules.md)。
```

## 文件 3：`knowledge/repos/vllm-omni/models/<model-slug>/rules.md`

```markdown
---
title: "<模型正式名称> 开发规则"
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
type: rule
tags: [vllm-omni, models]
sources: [<源码路径、设计文档或 PR URL>]
---

# <模型正式名称> 开发规则

只在任务明确属于 <模型正式名称> 时应用本页。模型边界见
[architecture](architecture.md)，目录入口见[模型索引](_index.md)。

## 规则

### <模型前缀>-1a — <一句话标题>

- 触发：<适用场景>
- 必须：<必须执行的动作>
- 禁止：<不允许的做法>
- 验收：<可检查的完成标准> ^[<PR、源码路径或设计文档>]
```

## 文件 4：需要别名时才更新 catalog

`models/` 目录本身就是模型清单，不修改父级 `_index.md`。只有正式名称之外还需要
别名或 registry key 路由时，才在
`knowledge/repos/vllm-omni/models/catalog.md` 增加对应关系。

```markdown
| <别名或 registry key> | <model-slug> | <源码目录或定位信号> |
```

## 提交前复制

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
git diff --check
```

所有尖括号都必须替换。检查失败时按报错修正，不要删除规则或扩大到其他 owner。
Windows 上 `LF will be replaced by CRLF` 只是换行符提醒，不是失败。
