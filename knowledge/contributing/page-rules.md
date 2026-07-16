# 页面与索引

## `_index.md` 是给人看的路由表

每个正式知识目录都必须有 `_index.md`。它不是占位文件，必须说清：

1. 什么时候查这里；
2. 哪些内容不属于这里；
3. 当前目录和直接子目录的每个有效入口；
4. 每个入口适用于什么问题。

最小格式：

```markdown
# Diffusion

## 什么时候查这里

- 调查 diffusion runner、scheduler、DiT 或多个 diffusion 模型共用实现。

## 不放什么

- HunyuanImage3 独有实现放 `models/hunyuan-image3/`。
- 通用 benchmark 方法放 `framework/benchmark/`。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 理解数据流 | [architecture](architecture.md) | 当前公开架构 |
| 调查复杂历史故障 | [incidents](incidents/_index.md) | 可选错题 |
```

搜索词直接写进“遇到什么”，普通页面不需要 YAML 或重复的触发词字段。

## 不同 owner 的索引还要写什么

### 仓库入口

`repos/<仓库>/_index.md` 还要写上游仓库和适用范围，并列出现有工作主题、代码模块和模型入口。

### 代码模块入口

`components/<模块>/_index.md` 还要列出：

- 对应源码路径；
- 主要职责和输入输出边界；
- 相关测试入口；
- 会影响哪些模型或上层功能。

### 模型入口

`models/<模型>/_index.md` 还要列出：

- 正式名称和常见别名；
- 对应源码路径；
- 依赖哪些共享代码模块；
- checkpoint、尺寸和量化版本的差异。

## `architecture.md` 写稳定边界

代码模块的 `architecture.md` 至少包含：

```markdown
# <代码模块名称>架构

## 职责和边界
## 主要源码和调用入口
## 数据怎样流动
## 怎样验证
```

模型的 `architecture.md` 至少包含：

```markdown
# <模型名称>架构

## 模型专有部分与共享模块的边界
## 配置、checkpoint 和兼容范围
## 从输入到输出的主要流程
## 怎样验证功能、精度和性能
```

不提交只有标题的空架构页。

## `rules.md` 写下次必须执行的事

规则是默认执行面，不是故事摘要。按最近 owner 放置：

- 多个仓库都成立 → `framework/<主题>/`；
- 整个仓库都成立 → `repos/<仓库>/rules.md`；
- 只属于稳定的共享源码模块 → `components/<模块>/rules.md`；
- 只属于某个模型 → `models/<模型>/rules.md`。

不预建空 `rules.md`。第一条规则出现时才创建，并从同目录 `_index.md` 链接。每条至少说清：

- 什么现象或任务触发；
- 必须做什么；
- 禁止什么；
- 怎样验收。

规则必须脱离单次 issue 也能读懂，不要求人先知道事故编号。

新增或实质修改的 `rules.md` 还要给每个独立、可审计约束一个稳定 ID，例如 `HY3-2c`。章节标题只是分组，不使用会被误认成规则的 ID。一个 ID 只表达一个行为不变量；它可以要求固定证据组合，但矩阵中的每个独立入口、失败策略或测试维度必须分别编号、逐项判定，缺一项时不能 `PASS`。解释、例子和链接不编号。已有未编号规则可以逐步迁移，但 reviewer 必须把它标为 `legacy-unstructured`，不能声称精确的子规则覆盖率。

## 分类目录

`guides/`、`incidents/`、`rfcs/` 等只用来组织同类页面。创建时必须同时创建 `_index.md`，并在上一层 `_index.md` 增加入口。

分类 `_index.md` 必须列出里面的每篇当前有效页面。过期但仍有历史价值的页面单独分组，不与当前规则混在一起。

## 人类手工新增内容

### 新增仓库、主题、代码模块或模型

1. 参考一个现有同类目录的最小结构，不复制整棵模板。
2. 创建 `_index.md`，写清“什么时候查”、“不放什么”和“目录内容”。
3. 在上一层 `_index.md` 增加入口。
4. 添加真实内容，不提交空目录。
5. 运行 `python tools/check_knowledge_tree.py`。

### 新增普通页面

1. 在最近 owner 目录新建 Markdown。
2. 在当前目录 `_index.md` 增加“遇到什么 → 查看哪里”。
3. 只有检查器提醒文件或目录达到阈值时，才按需读 [何时拆分](scaling.md) 并在同一修改中整理。
4. 运行 `python tools/check_knowledge_tree.py`。

目录名使用小写英文、数字和短横线，例如 `remote-debug`。同一层不能重名。`_index`、`local`、`components`、`models`、`incidents` 和 `guides` 是框架保留角色，只能按本文定义使用，不能拿来命名自定义主题。添加新目录不需要修改检查脚本的固定名单；上一层 `_index.md` 能找到它即可。
