# Plan —— `doc/` 全量重构

> 状态：**已完成（P0–P6，2026-08-17）**。执行中发现并修正的偏差记录在各阶段下。
> 决策已定（2026-08-17 grilling）：RFC 归入 `doc/features/`；使用指南新增
> 后端介绍；**现有文件只能作为参考材料，不得直接沿用**——以代码为准重写；
> SPEC 采用**逐文件全量重写**。

---

## 1. 目标与非目标

**目标**

1. 一个新人打开 `doc/` 能在 10 秒内知道该看哪一篇。
2. 每条事实**只有一个归属**，其他文档只链接不复述。
3. 文档内容与当前代码一致——不是"曾经正确"，是**核对过**。
4. 让"再次腐烂"变成可检测的：加闸门，而不是靠自觉。

**非目标**

- 不做 mkdocs 站点化（本轮不引入构建依赖）。
- 不改 `knowledge/`（那是数据面，有自己的治理协议；本轮只修它对 `doc/` 的
  两处路径引用）。
- 不改 `eval/` 目录本身（评测产物留在原地，`doc/evaluation/` 只放叙述性报告）。

---

## 2. 现状诊断（实测，2026-08-17）

`doc/` **204 个文件**、`docs/` **8 个文件**：

| 分组 | 文件数 | 状态 |
|---|---|---|
| `doc/archive/reorg-audit/` | **127（62%）** | 7 月一次性迁移取证；**但被引用**——`knowledge/SCHEMA.md`、`knowledge/repos/vllm-omni/rebase/workflow.md`、`doc/architecture/KNOWLEDGE.md` 都把它当作溯源基线 |
| `doc/architecture/SPEC/` | 49 | **42 个内容页里 41 个落后于其源码，仅 1 个同步**；另有约 17 个模块**完全没有页面** |
| `doc/` 顶层 `.md` | 20 | 六种体裁混放，无任何分组signpost |
| `doc/contributing/knowledge-templates/` | 8 | 活跃，被 EXTENDING-KNOWLEDGE 与 knowledge-maintainer 引用 |
| `docs/`（小写） | 8 | 与 `doc/` 只差一个字母；内含三类东西：使用指南、示例、**配置模板** |

**四个具体缺陷**

1. **`doc/` 与 `docs/` 一字之差**，且 `docs/` 里混着 `codex/config.toml`、
   `cursor/mcp.json` 这类**根本不是文档**的配置模板。
2. **文件名已经编码了体裁，目录树没有反映**：`RFC-`×4、`PLAN-`×2、`EVAL-`×4、
   `RESEARCH-`×1 与常驻参考文档平铺在一起。
3. **SPEC 的空洞正好落在开发最活跃的地方**：整个 `providers/`（8 个文件）、
   整个 MCP 面（`thin_mcp_server`/`mcp_server`/`mcp_policy`/`run_status`/
   `knowledge_docs`）、`tool_bridge`、`tracing`、`review/planner` 全无 SPEC 页。
   SPEC 描述的是 7 月的架构。
4. **过期材料以现行姿态陈列**：`IMPLEMENTATION_STATUS.md` 写着 pr-review v4 /
   64 tests / 20 steps，实际是 **v6 / 430+ 用例 / 38 steps**；
   `PLAN-mcp-plugin-and-community-merge.md` 自称 "PROPOSED rev 6，尚未执行"，
   停在 07-22。

**两个降低风险的事实**

- `doc/` 和 `docs/` **都不进 wheel**（`pyproject.toml` 只 force-include
  `knowledge` / `playbooks` / `adapters` / `skills`）——迁移不影响发布包。
- `integrations/config-templates/codex/config.toml`、`integrations/config-templates/cursor/mcp.json` 只被散文引用，没有代码依赖。

**一个必须先处理的风险**

代码里一共有 **29 处指向 `doc/` 的引用**，全部是散文形式、**没有任何 linter
检查**，改路径会静默失效：

| 引用方 | 次数 | 指向 |
|---|---|---|
| `src/` | 20 | `RFC-provider-registry.md`×14、`DESIGN.md`×4、`CODE_TOUR.md`×1、`KNOWLEDGE.md`×1 |
| `test/` | 7 | `DESIGN.md`×4、`RFC-provider-registry.md`×3 |
| `skills/` | 2 | `DOCSTRING_STYLE.md`、`EXTENDING-KNOWLEDGE.md` |

其中 `RFC-provider-registry.md` 一篇就占 17 次——而它恰好是本轮要改名并迁入
`features/` 的文件。

---

## 3. 目标结构

```text
doc/
  README.md                        NEW —— 文档地图（一行一条，唯一索引）
  GUIDE.md                         总入口：概览/功能/使用/开发/playbook/step/tool/性能

  guide/                           面向使用者
    hosts/                         **宿主端**：copilot 跑在谁里面（Direct）
      README.md                    NEW —— 宿主 vs 后端的消歧表（见下方警告）
      codex.md                     ← doc/guide/hosts/codex.md（重写）
      claude-code.md               NEW —— 从 README 安装章节抽出
      cursor.md                    NEW —— 同上
    backends.md                    NEW —— **后端**：谁跑在 copilot 里面（Strict）
    mcp.md                         ← doc/guide/mcp.md（重写）
    autonomous-workflow.md         ← doc/guide/autonomous-workflow.md（重写）
    knowledge-maintainer.md        ← doc/guide/knowledge-maintainer.md（重写）
    samples/                       ← doc/guide/samples/ 三篇（核对）

  features/                        面向"这个特性怎么回事"
    provider-registry.md           ← RFC-provider-registry（已实现）
    strict-review-deep-engine.md   ← RFC-strict-review-deep-engine（已实现）
    review-recall.md               ← RFC-review-recall-v14（已实现）
    auto-run.md                    ← RFC-auto-run（**未实现**，状态头标 draft）

  architecture/
    CODE_TOUR.md                   核对 + 补 providers/ 与 MCP 段
    DESIGN.md                      重构：v1 / v2 / **v3（provider registry + MCP 面）**
    KNOWLEDGE.md                   核对
    SPEC/                          **62 页逐文件全量重写**

  contributing/
    DOCSTRING_STYLE.md             核对
    EXTENDING-KNOWLEDGE.md         核对
    release-maintenance.md         ← VLLM_OMNI_RELEASE_MAINTENANCE.md
    knowledge-templates/           原样保留（活跃引用）

  evaluation/
    README.md                      NEW —— 评测索引 + 当前结论一句话
    EVAL-goal-strict-vs-opus5.md   冻结记录（加日期头）
    EVAL-v14-v16-recall-campaign.md
    EVAL-goal-report.md
    EVAL-PR20-report.md
    RESEARCH-reference-agents.md

  archive/                         冻结，不再维护，全部加 superseded 头
    IMPLEMENTATION_STATUS.md
    PLAN-knowledge-reorg.md
    PLAN-mcp-plugin-and-community-merge.md
    PLAN-doc-refactor.md           （本文件，完成后归档）
    reorg-audit/                   ← 连同 2 处 knowledge 引用一并更新

integrations/config-templates/     ← 从 docs/ 迁出（不是文档，是模板）
    codex/config.toml
    cursor/mcp.json

docs/                              ← 目录取消
```

---

### 3.1 必须消歧：宿主 ≠ 后端

`claude-code`、`codex`、`cursor` 这三个名字**同时是宿主和后端**，方向相反。
不把它讲清楚，`guide/backends.md` 和 `guide/hosts/codex.md` 在读者眼里就是同
一篇的两个标题。

| 名字 | 作为**宿主**（Direct：copilot 跑在它里面，用它的模型） | 作为**后端**（Strict：它被 copilot 拉起，跑一个 agent step） |
|---|---|---|
| Claude Code | ✅ `/imreview` | ✅ `STRICT_BACKEND=claude-code` |
| Codex | ✅ `$imreview` | ✅ `STRICT_BACKEND=codex` |
| Cursor | ✅ `/imreview` | ✅ `STRICT_BACKEND=cursor` |
| DeepSeek（dsh） | ✗ | ✅ `STRICT_BACKEND=deepseek` |
| api（Anthropic/OpenAI） | ✗ | ✅ 默认 |

判据一句话：**宿主提供模型给你用，后端是 copilot 拿去用的模型。**
宿主端不需要 API Key（`doc/guide/hosts/codex.md` 原话："there is no API key or
model configuration"）；后端端要么要 Key，要么要订阅登录。

两篇文档各自的开头**必须**放这张表加一句 "你要找的可能是另一篇"，并互相链接。

## 4. 内容归属矩阵

重构最容易失败的方式，是把同一件事写进三个文档然后各自腐烂。本轮为每类事实
指定**唯一归属**，其他文档只允许链接：

| 事实类型 | 唯一归属 | 其他文档的义务 |
|---|---|---|
| 装什么、配什么、怎么跑 | `GUIDE §3` + `guide/*` | 只链接 |
| **宿主端**安装与用法（Direct） | `guide/hosts/<host>.md` | `README` 只留一条最短路径 + 链接 |
| **后端**选择与配置（Strict） | `guide/backends.md` | `GUIDE §2.3` 只给一句话 + 链接 |
| kind / playbook / step / tool **清单** | `GUIDE §2/§5/§6/§7` | `CODE_TOUR` 只讲数据流，**不再列清单** |
| 数据如何流动、模块为何在此处 | `architecture/CODE_TOUR.md` | — |
| 为什么这样设计（含被否决的选项） | `architecture/DESIGN.md` | — |
| 单个源文件"不能破坏什么" | `architecture/SPEC/<path>.md` | `GUIDE §4.2` 只留跨文件那四条 |
| 某特性怎么用/怎么配/实测如何 | `features/<name>.md` | — |
| 测量数字与方法论 | `evaluation/*` | `GUIDE §8` 给结论摘要 + 链接 |

**判定规则**：写一段话之前问"这条事实的归属在哪"。如果不在你正在写的文档，
写一个链接。

---

## 5. 逐组处置

> 注：本表的"原路径"一列在 P1 执行时被路径扫描一并改写成了新位置——扫描器不区分
> "引用某个文件"和"记录它搬家前的位置"。留着不改，因为它本身就是一条教训：
> 机械替换会顺手改掉历史记录，迁移计划这类文档应当写在被扫描的范围之外。

| 原路径（见上注） | 去向 | 动作 |
|---|---|---|
| `CODE_TOUR.md` | `architecture/` | 核对更新（08-12，主体仍准；补 providers/、MCP、清单去重） |
| `DESIGN.md` | `architecture/` | 重构（07-22，缺 v3 期全部内容） |
| `KNOWLEDGE.md` | `architecture/` | 核对 + 改 reorg-audit 新路径 |
| `MCP.md` | `guide/mcp.md` | 重写 |
| `GUIDE.md` | 原地（`doc/`） | 修链接以适配新树 |
| `DOCSTRING_STYLE.md` `EXTENDING-KNOWLEDGE.md` | `contributing/` | 核对 |
| `VLLM_OMNI_RELEASE_MAINTENANCE.md` | `contributing/release-maintenance.md` | 核对 |
| `knowledge-templates/` | `contributing/` | 原样移动 |
| `RFC-*.md` ×4 | `features/` | **重写为特性文档**（RFC 作为素材） |
| `EVAL-*.md` ×4、`RESEARCH-*` | `evaluation/` | 加日期/冻结头，不改内容 |
| `IMPLEMENTATION_STATUS.md` | `archive/` | 冻结（其"现状"职能由 GUIDE 承担） |
| `PLAN-*.md` ×2 | `archive/` | 冻结 |
| `SPEC/` | `architecture/SPEC/` | **62 页全量重写** |
| `reorg-audit/` | `archive/reorg-audit/` | 移动 + 修 2 处 knowledge 引用 |
| `doc/guide/autonomous-workflow.md` | `guide/` | 重写 |
| `doc/guide/knowledge-maintainer.md` | `guide/knowledge-maintainer.md` | 重写 |
| `doc/guide/samples/*` ×3 | `guide/samples/` | 核对 |
| `doc/guide/hosts/codex.md` | `guide/hosts/codex.md` | 重写（并加 §3.1 消歧表） |
| （无对应文件） | `guide/hosts/claude-code.md`、`cursor.md` | 新写：从 `README` 安装章节抽出 |
| `integrations/config-templates/codex/config.toml` `integrations/config-templates/cursor/mcp.json` | `integrations/config-templates/` | 移动（非文档） |

---

## 6. 分阶段执行

每个阶段有**退出标准**；未达标不进入下一阶段。全程 `git mv` 保留历史。

### P0 —— 先造闸门，再动文件 ✅ 完成

没有工具就搬 200 个文件，等于把断链埋进去。

1. `tools/check_doc_links.py`：校验所有 `.md` 内部相对链接可解析。跳过围栏代码块
   与 `<占位符>`；排除 `eval/dataset/`（生成的评测产物**引用的是目标仓库**的文档
   路径，检查它们产生 250+ 个假阳性）和 `contributing/knowledge-templates/`
   （模板的相对链接按"复制到 `knowledge/` 之后"书写，原地就该是断的）。
2. `tools/check_doc_citations.py`：扫描代码中形如 `doc/...` 的引用，断言存在。
   只匹配单数 `doc/`——复数 `docs/` 指的是**目标仓库**的文档树，匹配它全是假阳性。
   另外解析 `ROOT / "docs" / "codex" / "README.md"` 这种**按段拼接**的路径：本次
   迁移中恰好有一处这样的引用逃过了字符串替换并弄坏了一个测试。
   合法的例外用行内 `doc-citation-exempt` 标注。
3. `tools/check_spec_freshness.py`：**以页内 `verified-against:` 声明为准**，
   而不是 git 日期。发现于执行途中的关键缺陷：`git mv` 会把页面的最后提交日期
   重置为迁移那一次，于是 45 个 7 月的页面在 P1 之后会**永远显示为最新**——
   迁移会亲手废掉这个闸门。声明式标记不受改名、重排版和错字修复影响。
4. 建目录骨架 + `doc/README.md` 索引。

**退出标准**（已达成）：三个工具在当前树上跑通并如实报出既有问题——links 与
citations 现为绿；spec 报出 **45 页无声明 + 17 个模块无页面 = 62 页待写**。
CI 已接入：links/citations 阻塞，SPEC 覆盖率**先只报告**（17 个空缺是已知在办
事项，让 CI 常红没有意义），P5 收尾时改为阻塞并加 `--strict`。

### P1 —— 纯迁移（不改内容） ✅ 完成

`git mv` 全部文件到目标位置；修代码内引用；修 `knowledge/` 的 `reorg-audit`
路径；`docs/` 目录取消。

实际战果：**移动 ~210 个文件**，重写 **55 个文件**里的路径引用（含 `src/` 20 处、
`test/` 7 处、`skills/` 2 处、CI workflow、`knowledge/` 4 处），再逐篇修正 5 个
被移动文档内部的 **17 条相对链接**（`../` 深度变了，仓库根路径替换救不了它们）。

**退出标准**（已达成）：三个 doc 工具零断链零悬空引用；`docs/` 目录消失；
知识两个 validator 绿（0 错误）；`pytest` 只剩 1 个**先于本次改动即存在**的失败
（`test_mcp.py::test_subprocess_tamper_defense`，已在 stash 后的干净树上复现，
与本重构无关）。

### P2 —— 使用者文档 ✅ 完成

分两条互不重叠的线，边界见 §3.1：

- **后端线**：`guide/backends.md`（**新写**：五个 provider 的凭据模型、能力
  矩阵、`STRICT_BACKEND` 怎么配、harness 与 api 的差别、工具桥如何保持权限
  闸、每个后端的实测特点）。
- **宿主线**：`guide/hosts/README.md`（新写，消歧表）+ `codex.md`（重写）+
  `claude-code.md`、`cursor.md`（新写，从 `README` 抽出）。

其余：`guide/mcp.md`、`autonomous-workflow.md`、`knowledge-maintainer.md`
重写，`samples/` 核对。

**退出标准**：(a) 每篇的命令/配置项在当前 `.env.template` 与 `cli/entry.py`
里逐条核对过；(b) `backends.md` 与每篇 `hosts/*.md` 都带 §3.1 消歧表并互链——
**这条单独验收**，它是本组最容易塌掉的地方。

### P3 —— `features/` ✅ 完成

四篇特性文档，从 RFC + 代码重写。每篇固定小节：**做什么 / 怎么开关 / 怎么配 /
实测结果 / 已知边界**。`auto-run.md` 状态头必须明确标注**未实现**。

**退出标准**：每个提到的 setting 在 `config.py` 里存在；每个实测数字在
`evaluation/` 或 `eval/dataset/results/` 里有出处。

### P4 —— `architecture/` 三件 ✅ 完成

`CODE_TOUR` 核对（并按归属矩阵**删掉清单类内容**，改为链接 GUIDE）；
`DESIGN` 补 v3 期（provider registry、MCP 双入口、双路径 mode）；
`KNOWLEDGE` 核对。

**退出标准**：`CODE_TOUR` 的文件清单与 `src/` 实际文件数一致（当前它自称
覆盖 80 个 `.py`，实际 92 个）。

### P5 —— SPEC 全量重写（工作量主体）✅ 完成

62 页，按包分 13 批，每批一个提交：
`engine/` · `engine/agent_runtime/` · `engine/steps/` · `providers/` ★ ·
MCP 面 ★ · `profiles/` · `memory/` · `review/` · `ci/` · `cli/` ·
`adapters/` · `playbooks/` · 顶层散文件。（★ = 全新，零基础）

每页强制格式：**职责 / 不变量（逐条指向源码符号）/ 失败模式 / 相关测试**。
"不变量"一栏必须能指到具体符号或测试，写不出来的条目不许留。

**退出标准**：`check_spec_freshness.py` 报零落后；每页至少引用一个存在的测试。

### P6 —— 根目录收口 ✅ 完成

`README.md`、`DEVELOPMENT.md`、`QUICKSTART.md`、`AGENTS.md` 重新指路。
处理 `QUICKSTART.md` 与 `GUIDE §3` 的重叠——按归属矩阵，**QUICKSTART 收缩为
指向 GUIDE 的短页**，或直接并入 `guide/`（待定，见 §8 未决项）。

**退出标准**：三个 doc 工具全绿；从 `README` 出发三跳内可达任意文档。

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 29 处代码内 doc 引用静默失效 | 注释指向不存在的文件，`RFC-provider-registry` 一篇占 17 处 | P0 的 `check_doc_citations.py` **先于**迁移落地，并进 CI |
| `knowledge/` 两处 reorg-audit 引用 | 溯源链断裂 | P1 内一并修改，跑两个知识 validator |
| 重写 59 页 SPEC 引入**错误**的契约 | 比过期更糟——错的约束会误导修改 | 每条不变量必须指向源码符号或测试；写不出来就不写 |
| 重复内容卷土重来 | 三处描述同一事实，各自腐烂 | §4 归属矩阵 + `CODE_TOUR` 清单类内容在 P4 主动删除 |
| 再次腐烂（41/42 复发） | 半年后回到原点 | `check_spec_freshness.py` 进 CI；源码改了而 SPEC 未改即失败 |
| 阶段做一半停工 | 半新半旧比全旧更难导航 | P1 是**纯迁移**，任何时刻中断，树都是自洽的；P2–P5 每篇独立可交付 |

---

## 8. 未决项（需要你拍板，不阻塞 P0–P1）

1. **`QUICKSTART.md` 的归宿**：收缩为指路短页，还是并入 `guide/` 后删除？
   （它是英文，`GUIDE` 是中文——并入涉及语言统一。）
2. **`archive/` 的存续**：`reorg-audit/` 127 个文件是否值得留在主仓库？
   备选是打成 tarball 或迁到独立分支，但会削弱 `knowledge/SCHEMA.md` 的溯源
   链条。**建议：留在仓库内**（它是被引用的证据基线，不是垃圾）。
3. **`evaluation/` 与顶层 `eval/` 的边界**：本计划让 `doc/evaluation/` 只放
   叙述性报告，数据与脚本留在 `eval/`。若你希望合并，P0 前告诉我。
4. **语言**：新写与重写的文档默认中文（与 `GUIDE.md` 一致），标识符/路径/
   flag 保留英文。`DESIGN.md` 现为英文——重构时是否统一为中文？

---

## 9. 工作量估算

| 阶段 | 产出 | 相对规模 |
|---|---|---|
| P0 | 3 个校验工具 + 索引 + 目录骨架 | 小 |
| P1 | ~210 次移动 + ~24 处引用修正 | 小（机械） |
| P2 | 9 篇（`backends.md` + `hosts/` 四篇全新） | 中 |
| P3 | 4 篇特性文档 | 中 |
| P4 | 3 篇（`DESIGN` 需补一整个时期） | 中 |
| **P5** | **62 页 SPEC** | **大——约等于其余全部之和** |
| P6 | 4 篇根文档收口 | 小 |

P0–P1 可立即执行且低风险；P5 建议按批推进，每批独立提交、独立可回滚。


---

## 10. 完成记录（2026-08-17）

### 最终状态

```
check_doc_links       OK（279 个文件，零断链）
check_doc_citations   OK（39 处代码内引用全部解析）
check_spec_freshness  62 页 —— 62 declared-verified / 0 stale / 0 undeclared
                      / 0 orphan；**0 个模块无覆盖**（起点：45 无声明 + 17 无页面）
knowledge validators  0 错误
pytest                1 处失败，**先于本次改动即存在**
                      （test_mcp.py::test_subprocess_tamper_defense，已在 stash
                      后的干净树上复现）
```

CI 已接入三个校验器；SPEC 一项在 P5 收尾后按计划从"只报告"改为
**阻塞 + `--strict`**。

### 执行中改掉的计划本身

1. **SPEC 的新鲜度不能靠 git 日期。** 原计划用"页面提交日期 vs 源码提交日期"。
   实测发现 `git mv` 会把页面日期重置为迁移那一次——**迁移会亲手废掉这个闸门**，
   45 个 7 月的页面在 P1 之后会永远显示为最新。改为页内声明
   `<!-- verified-against: YYYY-MM-DD -->`，不受改名/重排版影响。
2. **62 页，不是 59 页。** 初测把 `engine/steps/_common.md` 这类嵌套下划线页误判
   为跨切页；`__main__.md` 也因 dunder 名被同一条规则吞掉。工具修正后真实数字是
   45 + 17 = 62。
3. **45 页里只有 15 页真的需要改写。** 其余 30 页的唯一改动来自同一个提交
   （`91be10a` 重命名扫描），不改契约。对这 30 页做了**程序化的公共契约核对**
   （规格里点名的每个符号是否仍存在于源码），29 页干净，1 页有真实漂移
   （`profiles/establish.md` 仍列着 `LANGUAGE_SUFFIXES`，它已被并入
   `profiles/languages.py` 的 `suffixes()`）——这正是那页自己的 refactor note
   当初预告的 K2 合并。盲目重写会把这条漂移一起抄下去。
4. **字符串扫描抓不到按段拼接的路径。** `ROOT / "docs" / "codex" / "README.md"`
   逃过了路径替换并弄坏一个测试。`check_doc_citations.py` 因此增加了段拼接解析，
   合法例外用行内 `doc-citation-exempt` 标注。

### 顺带发现的代码缺陷（已修）

- **`providers/registry.py` 给 `deepseek` 声明了 `mcp_tools`，而该 transport
  测得根本用不了工具桥**（其运行时未编译进 `dsh-mcp-client`，会话跑在原生 bash
  上并记 `capability_gap`）。`base.ProviderSpec` 把 capabilities 定义为"集成方
  可以依赖的标志"，所以这是一条假声明。没有任何代码分支读它——**正因如此这个
  错误才活了下来：它只会误导读者**（本次就误导了 `guide/backends.md` 初稿）。已移除。
- **`tool_bridge.py` 的模块 docstring 与自身代码矛盾**：说 `repo_map` 未被桥接，
  而第 270–282 行就在桥接它。已改正，并补上"skill/memory 检索刻意不开放"的真实边界。
- `doc/architecture/CODE_TOUR.md` 自称覆盖"全部 80 个 `.py`"，实际 92 个，缺的
  9 个正好是 `providers/` 与 `tool_bridge`、`review/anchor`、`review/repo_tools`。
  已补齐并核对为 92。

### 仍未做（明确留白）

- `doc/guide/mcp.md`、`autonomous-workflow.md`、`knowledge-maintainer.md`、
  `samples/` 只做了链接修正与位置迁移，**未逐句重写**。它们内容当前无已知错误，
  但没有像 SPEC 那样被逐条核对。
- `QUICKSTART.md` 仍是英文，与中文文档树并存（§8 未决项 1 按"收缩为指路页"处理，
  未合并删除）。
- `doc/architecture/DESIGN.md` 仍是英文（§8 未决项 4 未统一）。
- 顶层 `eval/` 与 `doc/evaluation/` 的边界按计划划定（数据 vs 叙述），未合并。
