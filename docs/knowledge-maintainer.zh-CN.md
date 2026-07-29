# vLLM-Omni 知识库人工维护手册

这份手册面向 vLLM-Omni 的模块 owner 和模型 owner。目标不是让每个人研究知识库
框架，而是把维护者已经掌握的经验，稳定地交给人和 agent 复用。

社区维护者直接向 InferMatrixCopilot 提交规则即可，不需要访问私有知识源。同步流程
必须保留目标仓库已有的模块和模型规则，不能用上游知识树整棵覆盖。

## 最常见的维护方式

已有 owner 目录时，只需要：

1. 打开该目录的 `rules.md`。
2. 增加一条规则。
3. 更新页面顶部的 `updated` 和 `sources`。
4. 运行两个校验脚本。
5. 提交 PR，由对应 owner 审核。

只有新增模块、模型或页面时，才需要修改 `_index.md`。

## 第一步：找到正确 owner

| 经验属于什么 | 放在哪里 |
|---|---|
| 多个模型共用的源码模块 | `knowledge/repos/vllm-omni/components/<模块>/` |
| 单个模型的实现、配置或 checkpoint | `knowledge/repos/vllm-omni/models/<模型>/` |
| 整个 vLLM-Omni 都必须遵守的门禁 | `knowledge/repos/vllm-omni/rules.md` |
| 与任何仓库都无关的通用方法 | `knowledge/general/<主题>/` |

判断标准是“哪块代码或哪个维护者对结论负责”，不是“在哪个 PR 里发现”。

例如：

- deploy YAML 最终怎样进入 stage config → Configuration component。
- HunyuanImage3 的图片数量和 prompt token → HunyuanImage3 model。
- 所有模型共享的 scheduler 等待逻辑 → Scheduler component。

如果一个结论同时影响多个入口，只在最近 owner 留一份正文，其他地方只加链接。

## 第二步：先填一张规则卡片

维护者不需要先写 Markdown。先把下面六项填清楚：

```text
规则卡片

- owner（模块或模型）：
- 触发：什么改动、现象或任务需要使用这条规则？
- 必须：实现或审核时必须做什么？
- 禁止：过去最容易犯的错误是什么？
- 验收：什么测试、输出或代码路径能证明它满足要求？
- 来源：相关源码路径、设计文档或 PR 链接。
```

一张卡片只表达一个行为不变量。不能把一个 PR 的所有经验塞进一条规则。

## 第三步：写入 `rules.md`

现有 owner 已有 `rules.md` 时，直接增加：

```markdown
### <稳定规则 ID> — <一句话标题>

- 触发：<适用场景>
- 必须：<必须执行的动作>
- 禁止：<不允许的做法>
- 验收：<可以检查的完成标准>
```

规则 ID 使用该 owner 已有前缀并继续编号，例如 `CONF-6a`、`HY3-8a`。
不要重排或复用旧 ID。

规则不保存完整 diff、review 对话、调查时间线和大段日志。GitHub PR 本身负责保存
原始证据；知识库只保存下次可以执行的规则。

### Component 示例

下面是 Configuration owner 的规则写法：

```markdown
### CONF-3a — 争议以展开后的最终配置为准

- 触发：CLI、deploy YAML 和 stage override 对同一字段给出不同值。
- 必须：检查合并完成后的逐 stage 配置，并跟到第一位 consumer。
- 禁止：只看某一层 YAML 就断言最终生效值。
- 验收：最终配置对象能读回目标值，并与第一位 consumer 收到的值一致。
```

它没有保存某个 PR 的故事，而是保存 Configuration owner 下次仍会执行的判断。

### Model 示例

下面是 HunyuanImage3 owner 的规则写法：

```markdown
### HY3-2c — 在公开入口尽早拒绝非法图片数量

- 触发：修改图片数量、图片输入或公开生成入口。
- 必须：在文件读取、下载、解码、resize 和 VAE 之前校验数量。
- 禁止：等昂贵操作开始后才报参数错误。
- 验收：覆盖合法边界和超限输入，并证明超限请求没有进入昂贵路径。
```

这条规则只属于 HunyuanImage3，不应提升到仓库根或共享 Diffusion component。

## 新增模块或模型

如果目录尚不存在：

1. 从 [`doc/knowledge-templates/`](../doc/knowledge-templates/README.md) 复制对应模板。
2. 创建 `_index.md`，写清源码路径、职责边界、测试入口和依赖关系。
3. 有稳定架构信息时创建 `architecture.md`。
4. 第一条真实规则出现时才创建 `rules.md`，不要提交空页面。
5. 在父级 `components/_index.md` 或 `models/_index.md` 增加入口。

模块与模型的区别：

- Component：被多个模型或上层功能共享，有稳定源码和输入输出边界。
- Model：只描述某个模型自己的适配、配置、checkpoint 和行为。

## 人工与 agent 协作

推荐由 owner 提供规则卡片，agent 完成机械工作，owner 做最终语义审核。

不会或不想直接修改 Markdown 时，可以
[提交中文规则建议](https://github.com/JiusiServe/InferMatrixCopilot/issues/new?template=knowledge-rule.yml)。
表单内容就是本手册的规则卡片。知识库维护者或 agent 把它整理成 PR，再请原 owner
确认语义。

可以直接对 Codex 说：

```text
Use InferMatrixCopilot to update the knowledge base.

请根据下面的规则卡片修改最近 owner 的 rules.md：
<粘贴规则卡片>

要求：
1. 不保存原始 PR、评论、diff 或调查过程。
2. 不扩大到其他 component/model。
3. 使用该 owner 现有规则 ID 前缀。
4. 新增页面时更新最近 _index.md；只改已有 rules.md 时不要乱改索引。
5. 运行 check_knowledge_tree.py 和 check_wiki_lint.py。
6. 把最终 diff 交给我审核，不要自动发布评论。
```

agent 可以协助查路径、补 frontmatter、更新索引和运行检查，但下面三件事必须由
owner 最终确认：

- owner 是否正确；
- 规则是否真的长期成立；
- 验收是否覆盖真实生产入口。

推荐的团队分工是：

1. 模块/模型 owner 在重要 PR 合入或 review 结束后填写规则卡片。
2. 知识库维护者或 agent 负责查重、生成 Markdown、更新元数据并运行校验。
3. 原 owner 只审核自己目录中的规则语义和验收条件。
4. 合入后，后续 review 自动从该 owner 的 `rules.md` 获取规则。

## PR 前检查

- [ ] 规则放在最近的 component/model owner，没有放进宽泛的仓库根。
- [ ] 每条规则都有触发、必须、禁止、验收和稳定 ID。
- [ ] 删除 PR 编号后，规则仍能独立读懂。
- [ ] 没有保存完整 diff、review 对话、运行结果或临时路径。
- [ ] 修改已有 `rules.md` 时更新了 `updated` 和 `sources`。
- [ ] 新增页面或目录时更新了最近 `_index.md`。
- [ ] 两个校验脚本均为 0 错误、0 提醒。

```powershell
python knowledge/tools/check_knowledge_tree.py
python knowledge/tools/check_wiki_lint.py
```

更完整的目录、frontmatter 和页面规范见
[`knowledge/CONTRIBUTING.md`](../knowledge/CONTRIBUTING.md)。英文扩展说明见
[`doc/EXTENDING-KNOWLEDGE.md`](../doc/EXTENDING-KNOWLEDGE.md)。
