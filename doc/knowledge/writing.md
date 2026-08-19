# 怎么写和更新知识库（`knowledge/`）

要在仓库根目录 `knowledge/` 这棵精选 Markdown wiki 里**新增或修改一页**，**从这里
开始**。本页是操作指南：一条事实该落在哪、由哪种页型承载、copilot 会怎么消费它、
以及怎么过两道门禁。

三个surface，分清你在读哪一个：

| Surface | 是什么 | 什么时候读 |
|---|---|---|
| **本页** | 工作流 —— 决策树、页型、消费模型、门禁 | 你正准备动笔写 |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) → [`contributing/`](contributing/_index.md) | **有约束力的规范**，一个动作一篇专题 | 你需要那条硬规则；本页与它冲突时**以它为准** |
| [`templates/`](templates/) | 可复制的页面骨架，一种页型一个文件 | 你已经知道页面放哪，想直接开写 |

中文的手把手走查（含组件与模型的填写示例）：
[`maintainer-walkthrough.md`](maintainer-walkthrough.md)。

`knowledge/` 在本仓库内作为普通受版本控制的文件维护；布局、消费方式与维护规则见
[KNOWLEDGE.md](../architecture/KNOWLEDGE.md)。

> 同一套工作流被蒸馏成一个可检索 skill
> [`skills/knowledge-base-contribution/SKILL.md`](../../skills/knowledge-base-contribution/SKILL.md)，
> 让 copilot 自己的 agent 在复盘时也遵守它。

---

## 0. TL;DR —— 四步循环

1. **选定 owner 目录**（§1）。按**已验证的根因**路由，绝不按症状最先出现的地方。
2. **写/改一页**正确页型的内容（rules / architecture / guide / incident）——
   从 [`templates/`](templates/) 复制对应骨架（§4），并读一遍它
   所对照的那篇 vLLM-Omni 实页（§3）。每条事实**只保留一份正文**，其他入口只链接。
3. **在同一次修改里注册它**：在**最近的 `_index.md`** 里加一行
   `遇到什么 → 查看哪里`（或一条子目录链接）。未注册的页面过不了门禁。
4. **校验**（两道门禁都必须 0 错误）：

   ```bash
   python knowledge/tools/check_knowledge_tree.py    # 结构 / 索引 / 链接 / incident
   python knowledge/tools/check_wiki_lint.py         # 沉淀层 frontmatter + 标签分类法
   ```

交付见 §7。**本页描述的是人工写入路径**；上游发版驱动的结构事实走 `imupdate`
（[发版漂移审计](../contributing/release-maintenance.md)）—— 它只更新机器已证明的
baseline、catalog、source map、SHA pin 和 manifest，不做 owner 归属判断，也不写规则。
运行中的 agent 只能提 candidate 由人工晋升。下面的落盘位置判断和页型选择属于人工
路径；两个校验器三条路径都要过。

---

## 1. 该放哪？—— owner 决策树

### 第一层 —— general 还是仓库专属

| 这条经验… | 放到 |
|---|---|
| 在**任何**仓库都成立（review、ci、debug、git、planning、remote、docs、benchmark、agents、environment） | `knowledge/general/<topic>/` |
| 只对**某一个仓库**成立 | `knowledge/repos/<repo>/` |
| 是**当前这台机器**的事实（主机、路径、账号、cache、venv、token） | `knowledge/local/` —— 已被 git 忽略，永不入库 |

### 第二层 —— 仓库切片内部

| 这条经验讲的是… | 放到 |
|---|---|
| 仓库级的工作主题（review、ci、git、benchmark、remote、rebase…） | `repos/<repo>/<topic>/` |
| 多个模型**共用的源码**（diffusion、scheduler、serving…） | `repos/<repo>/components/<module>/` |
| **某一个模型**自己的实现 / 配置 / checkpoint | `repos/<repo>/models/<model>/` |

按**已验证**的根因路由。"前端看到 404" 不等于根因在前端 —— 页面沉到**证明了原因**
的那一层，而不是症状冒出来的那一层。

### 第三层 —— 选哪种页型

| 你手上有… | 页型 | 说明 |
|---|---|---|
| 一条必须改变**下一次**执行的规则（触发 → 必须 → 禁止 → 怎么验收） | 最近 owner 目录里的 `rules.md` | 复盘的默认产物。**always-on**（见 §2），必须写紧 |
| 一段**稳定的**数据流 / 职责 / 边界描述 | `architecture.md` | 不允许只有标题的空壳页 |
| 一套不是硬门禁的较长方法 | owner 根目录下的专题页；工作主题集合可以用 `guides/` | 组件/模型 owner 保持扁平，更深的页面一律按需拉取 |
| 规则装不下的**复杂可复现历史** | `incidents/YYYY-MM-DD-short-name.md` | 可选。只有当复现链/证据本身仍有独立查阅价值时才建 |

**复盘的经验法则：** "复盘 / 记一条教训" 的默认产物是**规则**，不是 incident。
只有当证据链复杂到规则本身承载不了时，才追加一个 incident。

---

## 2. copilot 怎么消费它（所以你才知道该把什么写紧）

接线在 `src/infermatrix_copilot/engine/agent_runtime/knowledge.py` +
`src/infermatrix_copilot/config.py` + 每个 `adapters/<repo>/manifest.yaml`。

- **always-on briefing** —— 注入**每一次** run，各自有上限：
  - general 切片 `settings.knowledge_general_docs`（`general/_index.md`）；
  - adapter 的 `briefing_docs` —— vllm-omni 是 `repos/vllm-omni/rules.md` +
    `repos/vllm-omni/_index.md`；
  - `briefing_docs_extra` —— 所有档位都加载的扩展切片，vllm-omni 目前是
    `repos/vllm-omni/review/guides/maintainer-pattern-routing.md`；
  - 强模型额外的 `performance_briefing_docs`（精简版评审模式）；
  - `review_checklist` —— 单页仓库评审清单，前 4k 字符注入 Strict reviewer 的
    system prompt，vllm-omni 指向
    `repos/vllm-omni/review/guides/strict-review-checklist.md`。
- **按需** —— `doc_search` / `doc_read` 工具可递归到达 `general/` 里每一页更深的
  Markdown，**外加当前 adapter 的 `repo_subdir`**（其他仓库的切片一律拒绝；路径穿越
  被阻断；`doc_read` 每页窗口 24k 字符，用 offset 翻页）。
- **MCP** —— 同一套按仓库限定的 `doc_search` / `doc_read` 以只读形式暴露在 MCP 上，
  所以宿主模型不启动 run 也能查询 wiki。

**对作者的现实含义：** `rules.md` 和 `_index.md` 是**预算** —— 它们每个任务都会加载。
把它们控制在触发器 + 门禁 + 导航。叙述、长复现、逐步方法推到按需拉取的专题页或
`incidents/`，那些只有真正需要时才被取用。

**agent 写不进这棵树。** 运行中的 agent 经 `skill_update_candidate` 只能提出
**candidate**；把 candidate 变成生效的 `SKILL.md`，或把一条 profile fact 写进
`profile.yaml`，都是**人工/策展动作**（`SPEC/memory/skills.md`、`SPEC/profiles/store.md`）。
这就是"读宽写窄"：事实随便记（RunTrace、debug memory），知识必须过门。
所以本页的落盘规则约束的是**人**——以及那个替人准备 candidate 的 agent。

要注册一个**新仓库**的切片，把它的 adapter manifest 指过去
（`knowledge.repo_subdir`、`briefing_docs`，可选 `briefing_docs_extra`、
`performance_briefing_docs`、`review_checklist`）—— 见 §5。

---

## 3. 动笔之前先读真实的树

vLLM-Omni 切片是下面每一条约定的参考实现。模板里的占位符含义不清时，**实页才是
ground truth**：

| 要写… | 先读这篇 |
|---|---|
| owner 门禁页 | [`components/configuration/rules.md`](../../knowledge/repos/vllm-omni/components/configuration/rules.md) —— 规则组、审查组、`VOMNI-CFG-*` ID |
| 模型门禁页 | [`models/hunyuan-image3/rules.md`](../../knowledge/repos/vllm-omni/models/hunyuan-image3/rules.md) —— `HY3-*` ID，以及什么才算可审计 ID |
| 路由索引 | [`components/_index.md`](../../knowledge/repos/vllm-omni/components/_index.md) —— 一行一个 owner，以及**什么时候不要**打开 `architecture.md` |
| 仓库入口 | [`repos/vllm-omni/_index.md`](../../knowledge/repos/vllm-omni/_index.md) —— review 最短路径表 |
| 组件架构 | [`components/diffusion/architecture.md`](../../knowledge/repos/vllm-omni/components/diffusion/architecture.md) —— 负责什么 / 不负责什么 / 带 commit pin 的布局 |
| incident | [`ci/incidents/`](../../knowledge/repos/vllm-omni/ci/incidents/_index.md) —— 五个字段，以及规则是怎么从中提炼出来的 |

那些页面共同遵守、而新手通常会漏掉的三条约定：

1. **owner 的 `rules.md` 以 Direct 代码快速入口开头。** vLLM-Omni 现有的 12 个
   owner 规则页（5 个 component + 7 个 model）全都这么做：*意图 → 规则组 → 第一批
   live 源码*，写成 producer→consumer 链
   （`stage_config.py::{build_stage_runtime_overrides}` → `omni_config.py::…`）。
   这一页是 always-on 预算，读者必须能在不消化其余 20 条的情况下够到命中的那 3 条。
2. **规则 ID 带 owner 前缀，并且永不重新编号。** 一个 owner 一个前缀，新 owner 起
   新前缀，不复用别人的：vLLM-Omni 在用 `CONF`、`SERV`、`DIFF`、`EXEC`、`SCHED`、
   `VOMNI-CFG`、`HY3`、`COSMOS`、`FLUX2`、`KREA`、`MCPMO`、`MING`、`Q3TTS`，另有
   afd-plugin 的 `AFD` 和通用 `REV`。评审和 incident 会引用这些 ID，所以只能
   **retire**，不能改派。页面上要明确写出哪些文字才是可审计 ID；章节标题只是分组。
   （数量会漂移，需要准确值时现数：ID 定义写成 `## <ID> — …` 或
   `- **<ID> — …**`。）
3. **写清楚什么**不**在这里。** 树里每一页好文档都会点名邻居并把读者路由过去。
   这正是"一条事实只有一处"得以成立的原因 —— 整棵 wiki 依赖的唯一性质。

## 4. 模板

**骨架在 [`templates/`](templates/)** —— 一种页型一个文件，
其 [README](templates/README.md) 给出 复制 → 填写 → 注册 → 校验 的流程。
**它们是唯一副本**：本指南刻意不再内联重复一遍，因为上一版就是这么做的，两份副本
最终漂移成了两套。

```bash
cp doc/knowledge/templates/rules.md \
   knowledge/repos/<repo>/components/<module>/rules.md
```

只要你 (a) 替换掉占位符、(b) 在最近的 `_index.md` 里注册页面，每个模板都是过门禁的。
frontmatter 由两条规则决定：

- **沉淀层** —— `general/` 和 `repos/` 下的 `rule` / `guide` / `architecture` /
  `index` 页 —— **必须**带 frontmatter，由 `check_wiki_lint.py` 强制：`title`、
  `created` + `updated`（都是 `YYYY-MM-DD`）、`type`（四者之一）、非空的 `tags`
  （取自 [`SCHEMA.md`](SCHEMA.md) 的 `## 标签分类法`）。
  `confidence` 如果出现，必须是 `high|medium|low`；`sources` 不是必填字段。
  **这包括 `_index.md`** —— 全树 123 个索引页里，109 个沉淀层索引全部带着它，
  另外 14 个是 `incidents/`、`history/`、`results/` 的证据层索引，按规定不带。
- **证据层** —— `incidents/`、`history/`、`results/` —— **不带** frontmatter；
  incident 模板改用 `- 编号/…` 这组扁平字段，由 `check_knowledge_tree.py` 检查。

目录名用小写 `a-z0-9-`。`_index`、`local`、`components`、`models`、`incidents`、
`guides` 是**保留角色名**，不要拿来当自定义主题。

## 5. 接入一个新仓库切片

1. 建出 wiki 骨架，并逐级注册上去：

   ```text
   knowledge/repos/<repo>/_index.md      # 用 templates/repo-index.md
   knowledge/repos/<repo>/rules.md       # 仅当确实存在仓库级门禁时才建
   # 在 knowledge/repos/_index.md 里为 <repo> 加一行
   ```

2. 把 adapter 指向该切片（`adapters/<repo>/manifest.yaml`）：

   ```yaml
   knowledge:
     repo_subdir: repos/<repo>              # 它在 knowledge/ 下的切片
     briefing_docs:                          # always-on：保持极小
     - repos/<repo>/rules.md
     - repos/<repo>/_index.md
     briefing_docs_extra:                    # 可选，所有档位都加载
     - repos/<repo>/review/guides/<routing>.md
     performance_briefing_docs:              # 可选，仅强模型
     - repos/<repo>/review/guides/<patterns>.md
     review_checklist: repos/<repo>/review/guides/<checklist>.md   # 可选，单页
   ```

   这六个键之外的字段会被 `check_wiki_lint.py` 拒绝；briefing 和 checklist 都不能
   指向 `incidents/`、`history/`、`results/`。

3. 如果你是从上游 fork 的 wiki，删掉不属于你的 `repos/` 切片，并相应更新
   `repos/_index.md`。

---

## 6. 门禁速查 —— 两道门到底卡什么

`check_knowledge_tree.py`（结构）和 `check_wiki_lint.py`（frontmatter/schema）
都在评审时运行，**两个都必须 0 错误**（提醒需要人判断，见表末一行）。

| 检查项 | 门 | 规则 |
|---|---|---|
| 索引存在 | tree | 任何含 Markdown 的目录都要有 `_index.md` |
| 已注册 | tree | 每个非索引页**以及**每个子目录，都要被最近的 `_index.md` **恰好链接一次** |
| 链接 | tree | 相对链接必须可解析；绝对路径一律拒绝 |
| 体量 | tree | ≥300 非空行或 16 KiB 告警；≥500 行或 32 KiB **必须拆分**（豁免要在同目录 `_index.md` 里同时出现该**文件名**和字面词 `暂不拆分`，再补复查日期） |
| 目录扇出 | tree | 非分组目录超过 7 个普通页告警；分组目录（`guides` `incidents` `history` `references` `results` `rfcs`）超过 20 个硬失败 |
| incident 格式 | tree | `YYYY-MM-DD-short-name.md` + 五个 `- 编号/归属/状态/搜索词/影响范围` 字段 + 合法状态 + 全树唯一的编号 |
| 隐私 | tree | 受版本控制的页面里不得出现真实 IPv4、Windows `C:\Users\…`、远端用户 home 或私钥块 |
| 安全 | tree | 不得出现 `StrictHostKeyChecking=no`、全局 `safe.directory *`、`--gpus all`、`pkill`、`rm -rf`、`find … -exec rm` |
| `local/` | tree | 必须保持 git 忽略（未入库） |
| 根入口 | tree | `doc/knowledge/CONTRIBUTING.md` 保持 ≤100 非空行 / ≤8 KiB（细节下沉到 `contributing/`；校验器跨树检查这一条） |
| owner 轴 | tree | `components/`、`models/` 必须直属仓库；源码 owner 下不得有 `guides/` |
| 整页重复 | tree | 两个 owner 下逐字节相同的整页正文（≥200 字符）硬失败 |
| frontmatter | lint | 沉淀层页面（`general/`+`repos/` 下的 `rule/guide/architecture/index`）需要 `title`、`created`+`updated`（`YYYY-MM-DD`）、`type`（四者之一）、非空 `tags`；可选 `confidence: high\|medium\|low` |
| 标签分类法 | lint | 每个 `tags` 取值都必须出现在 `SCHEMA.md` 的 `## 标签分类法` 里 |
| 证据层 | lint | `incidents/` `history/` `results/` **不做** frontmatter 检查（它们用扁平 incident 字段） |
| adapter briefing | lint | `manifest.yaml` 的 `knowledge:` 只允许 `source`/`repo_subdir`/`briefing_docs`/`briefing_docs_extra`/`performance_briefing_docs`/`review_checklist`；briefing 与 checklist 不得指向证据层页面，`review_checklist` 指向的页面必须存在 |
| 提醒（不失败） | 两者 | 接近拆分线、目录超过 7 个普通页、孤页、超过 365 天未更新、`confidence: low` / `contested` —— 需要人判断，不是必须清零的门 |

`rules.md`、`architecture.md`、`_index.md` 属于"特殊页"，不计入 7 页扇出告警。

---

## 7. 交付

- 像改任何受版本控制的内容一样就地改 `knowledge/`；wiki 门禁在评审时运行 ——
  **不要**直接推保护分支。**目标仓库不会向本仓库提 PR**：它的 owner 提
  `[Knowledge]` issue，由维护者落盘。
- 引入任何外部页面时**有选择地**导入具体页面并只取语义增量 ——
  **整树替换不是合法的更新方式**（这里没有 submodule 链接）。
- 机器事实（主机、路径、账号、token、cache、venv）**只**放在被 git 忽略的
  `knowledge/local/`；受版本控制的页面里不得出现（门禁会拦，但提交前请自己也看一眼）。
- 改到 `repos/vllm-omni/` 时还有**第三道门**：`owner_documents` 入口页、`pin_documents`
  里的 SHA pin 和 `sources:` 由发版审计对账，两个校验器看不见它；任何触及该切片的 PR
  都会在 CI 里跑 `enforce`。见
  [同步与校验 §发版审计](contributing/validation.md#vllm-omni-页面还有一道发版审计)。

---

## 8. 可检索 skill

[`skills/knowledge-base-contribution/SKILL.md`](../../skills/knowledge-base-contribution/SKILL.md)
把这套工作流编码给 copilot 自己的 agent（owner 路由、页型选择、`_index.md` 注册、
always-on 紧凑度、以及校验器）。它经 `skill_search` 被检索，在 agent 被要求记录一条
教训时浮现。**本指南每次变更，都要在同一个 PR 里更新它。**
