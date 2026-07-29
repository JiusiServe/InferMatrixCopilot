# vLLM-Omni 规则复制样本

本页只提供可复制内容。尖括号 `<...>` 表示必须替换；样本中的 `NEXT` ID 不能原样
提交。

## 最快方法：复制同文件最后一条

已有 `rules.md` 时，不要优先复制本页的通用骨架。复制目标文件最后一条现有规则，
再替换：

1. ID 和标题；
2. 触发、必须/强制、禁止、验收；
3. 规则末尾的 `^[来源]`；
4. 页面顶部的 `updated` 和 `sources`。

这样会自动沿用该文件的 `##`/`###` 标题层级和“必须/强制”措辞。不能保留旧规则的
来源冒充新规则来源。新规则没有 PR、源码路径或设计文档可核对时，先补证据，不提交。
同一规则由多个来源共同证明时放在一个标记中，用分号分隔，例如
`^[PR #5001; vllm_omni/diffusion/models/cosmos3/]`。页面顶部 `sources` 保存整页来源
的并集，规则末尾只列真正支撑该规则的来源。

## 样本 A：已有 component 增加规则

1. 打开 `knowledge/repos/vllm-omni/components/<模块>/rules.md`。
2. 查看该文件已有规则 ID 前缀和最大编号。
3. 把下面整段复制到文件末尾并替换五处：

```markdown
### <COMPONENT 前缀的新 ID> — <一句话标题>

- 触发：<什么字段、入口、数据流或故障会触发这条规则>
- 必须：<实现或审核时必须完成的动作>
- 禁止：<过去容易出现但不能再接受的做法>
- 验收：<真实入口、第一位 consumer、测试或运行结果怎样证明完成>
```

完整改写示例：

```markdown
### CONF-NEXT — 新配置字段必须到达真实 consumer

- 触发：新增或转发 deploy、CLI、stage config 字段。
- 必须：从公开入口跟踪字段经过归一化和构造，直到第一位真实 consumer。
- 禁止：只证明 parser、dataclass 或中间字典保存了字段。
- 验收：一个非默认值通过生产构造路径到达 consumer，同时未知字段仍然失败。 ^[PR #<编号>]
```

最后修改同一文件顶部：

```yaml
updated: <今天的 YYYY-MM-DD>
sources: [<源码路径、设计文档或 PR URL>]
```

已有 `sources` 时追加来源，不要删掉旧来源。已有 `_index.md` 已链接此
`rules.md` 时，不需要修改索引。`sources` 是页面的来源集合，`^[...]` 标记这条规则
具体使用哪个来源，两处都要更新。

## 样本 B：已有 model 增加规则

1. 打开 `knowledge/repos/vllm-omni/models/<模型>/rules.md`。
2. 沿用该模型已有 ID 前缀，把下面整段复制到末尾：

```markdown
### <MODEL 前缀的新 ID> — <一句话标题>

- 触发：<修改该模型的 prompt、checkpoint、processor、stage 交接或输出时>
- 必须：<必须保持的模型专有合同>
- 禁止：<不能用哪个共享默认值、mock 或其他模型行为代替>
- 验收：<真实 checkpoint、processor、公开入口或精度/性能基线>
```

完整改写示例：

```markdown
### HY3-NEXT — checkpoint 对齐必须使用真实 key 集合

- 触发：修改 HunyuanImage3 的权重映射、rename 或加载兼容逻辑。
- 必须：用受支持 checkpoint 的真实 key 集合核对映射前后覆盖率。
- 禁止：只用手写 mock 字典证明加载逻辑正确。
- 验收：至少一个受支持 checkpoint 完成 key dry-run，未知 key 明确失败且没有静默丢失。 ^[PR #<编号>]
```

同样更新文件顶部的 `updated` 和 `sources`。已有目录和页面时不要新建第二份
`rules.md`，也不要把模型规则写进共享 component。没有 PR 时可以使用稳定源码路径或
设计文档作为来源；三者都没有时先补证据。

## 样本 C：新增一个模型 owner

假设新模型目录名是 `<model-slug>`。创建以下三个文件。

### 文件 1：`knowledge/repos/vllm-omni/models/<model-slug>/_index.md`

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

### 文件 2：`knowledge/repos/vllm-omni/models/<model-slug>/architecture.md`

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

### 文件 3：`knowledge/repos/vllm-omni/models/<model-slug>/rules.md`

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

最后在 `knowledge/repos/vllm-omni/models/_index.md` 的模型表格增加一行：

```markdown
| <模型正式名称和常见别名> | [<模型正式名称>](<model-slug>/_index.md) | <一句话适用范围> |
```

## 提交前复制这组命令

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
git diff --check
```

三个命令都通过后再提交 PR。检查失败时先按报错修改，不要为了通过而删除规则或扩大
到其他 owner。

Windows 上出现 `LF will be replaced by CRLF` 是 Git 的换行符提醒，不代表校验失败。
