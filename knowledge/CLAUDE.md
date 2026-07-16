# Workflow Starter 开工入口

本文件只负责三件事：告诉 agent 先读哪里、哪些通用风险必须硬停、长期知识应该写到哪里。仓库、代码模块、模型和机器专属规则不写在这里。

## 0. 开工顺序

1. 确认用户正在操作哪个真实仓库；不要用当前 shell 路径或历史对话猜。
2. 先查下面场景触发器。精确命中具体 guide 时直接读 guide，不再先读它所在主题的 `_index.md`；没有直接命中时，才从知识地图选一个 `framework/<主题>/_index.md`。
3. 只有 canonical `repos/<slug>/` 已由本轮的显式知识路径或仓库映射验证时，才直接读它的 `rules.md`。用户只给 upstream 名、URL、显示名或本地目录名时，先只读 [仓库列表](repos/_index.md) 的映射表，不能自行拼 slug。规则精确指向 owner 就立即完成路由；没有匹配、owner 不清楚或需要职责地图时，再读 `repos/<slug>/_index.md` 和一个主要仓库主题。不能读完 `framework/` 就直接开始查源码。
4. 仓库主题入口负责继续路由。涉及源码时先看 `components/_index.md` 的职责地图，只属于某个模型时看 `models/_index.md`；确认一个主要 owner 后读取对应 `_index.md` 和其中已有的 `rules.md`，并停止横向展开。只有 live 调用链证明错误跨越另一个模块边界时才读取第二个模块，不能为了保险遍历所有相关目录。找不到 owner 时以 live 源码继续调查，复盘确认稳定边界后再补路由，不要为一次问题临时造模块。
5. 当前机器地址、路径、账号、cache、venv 和临时状态只从 ignored `local/` 获取，并用 live 命令重新验证。
6. 不要递归加载整棵知识树；历史错题不是默认入口，只在规则明确提示、出现高度相似错误或用户明确调查历史时搜索。

路由阶段只读取 `_index.md`、当前仓库 `rules.md` 和命中的 owner 规则。仓库 `rules.md` 的场景触发器已经直接指向 owner 时，路由立即完成，不再读取同级 `dev/components/models` 候选入口。只有没有直接匹配时才用职责地图选择 owner。先写出“用户入口 → 主要 owner → 准备核对的源码边界”，再按需要读取一篇具体 guide；不能在 owner 未确定前预读多篇方法正文。

仓库同名主题按任务目的选，不按通用 guide 所在的物理目录选。例如“写代码”会读 `framework/review/guides/code-taste.md`，但不因此自动进入仓库 `review/`；只有任务本身是 code review、reviewer follow-up 或仓库规则明确指向时才进入。

实现任务只选一个主题完成路由。仅因一个代码 diff 同时包含测试和文档，不需要在开工时横向读完 `ci/` 和 `docs/` 主题；选定代码 owner 后，先查真实仓库里最近的测试和文档入口。任务主目标命中 CI、测试体系或文档，或本页和仓库场景触发器明确要求专项门禁时，仍必须进入对应主题。

### 开发任务十分钟首次落盘

用户已经授权实现、真实 checkout 可写且不是纯分析任务时，记录开工时间。确认主要 owner 后立即写出四项：`owner`、开发阶段命中的规则 ID/章节、第一批要打开的源码函数、当前唯一阻塞；没有阻塞就进入 live 源码，不再继续浏览同级主题、其他 owner、incidents 或 history。开发者只读当前任务命中的 owner 规则，完整规则枚举属于写完后的 reviewer，不在编码前手工跑一遍。

开工到第一次有效落盘目标不超过十分钟。有效落盘是 owner-aligned 的最小行为改动、绑定已确认合同的失败回归测试，或文档任务中真实改变目标规则/结构的正文；TODO、注释、纯格式、占位测试和空骨架不计。测试环境与路由并行做一次不超过两分钟的最小 preflight；缺依赖、模型或 GPU 时立即记录行为验证边界，不用更多静态阅读冒充验证。十分钟仍不能安全落盘时，必须报告一个能阻止实现的具体未知量和下一处唯一源码证据；“继续熟悉代码”“再多看看相关模块”不是阻塞，也不能据此横向扩大阅读。

这个时间门禁不允许为了赶时间跳过 public contract、owner 或 live source。发现调用链确实跨 owner、官方语义冲突或当前计划会改变用户接口时，先记录证据再扩展一个必要边界。阶段耗时只使用实际时间戳，格式见 [agent loop](framework/agents/guides/agent-loop-workflow.md#开发阶段耗时记录)。

对于已有完整错误日志和可读源码的窄 bug，下面的窄 bug 快路径优先于默认第 2‑4 步完成诊断路由；`code taste` 在真正编辑业务代码前再读。目标是在开工后三分钟内先给出“根因 / 最小证据 / 未验证边界”。三分钟内无法闭环时先报告缺少哪一段证据，再扩大调查；不能先做历史考古、穷举排除和完整修复设计。

窄 bug 快路径：canonical `repos/<slug>/` 已在本轮验证时，直接检查其 `rules.md`；用户只给 upstream、URL、显示名或本地目录时，先只读 `repos/_index.md` 完成映射，不自行拼 slug。仓库场景触发器直接命中 owner 时，直接进入 owner 规则，不再读取通用 debug 索引或仓库 debug fallback。规则文件不存在、触发器没有匹配或 owner 边界不清时，立即回到标准“通用主题 → 仓库主题 → 职责地图”路由。

## 1. 知识地图：先通用，再仓库，最后代码或模型

| 正在做什么 | 第一个入口 | 识别仓库后必须检查 |
|---|---|---|
| code review 和 reviewer follow-up | [framework/review](framework/review/_index.md) | `repos/<仓库>/review/_index.md` |
| 测试选择和 CI | [framework/ci](framework/ci/_index.md) | `repos/<仓库>/ci/_index.md` |
| 写文档、RFC 和用户可见说明 | [framework/docs](framework/docs/_index.md) | `repos/<仓库>/docs/_index.md` |
| Git、commit、rebase 和 PR | [framework/git](framework/git/_index.md) | `repos/<仓库>/git/_index.md` |
| 调试和根因收敛 | [framework/debug](framework/debug/_index.md) | `repos/<仓库>/debug/_index.md` |
| benchmark 和性能证据 | [framework/benchmark](framework/benchmark/_index.md) | `repos/<仓库>/benchmark/_index.md` |
| Windows、WSL、编码和本地工具 | [framework/environment](framework/environment/_index.md) | 通常没有仓库补充 |
| SSH、容器、GPU 和远端长跑 | [framework/remote](framework/remote/_index.md) | `repos/<仓库>/remote/_index.md` |
| 多 agent 分工和交接 | [framework/agents](framework/agents/_index.md) | 通常没有仓库补充 |
| 拆需求、产品闭环和执行计划 | [framework/planning](framework/planning/_index.md) | 仓库入口中对应的业务主题 |

仓库补充目录不一定全部存在，不要预先建立空目录。只进入任务目的选中的同名仓库主题；没有对应主题时以仓库 `rules.md` 的现象路由为准。问题同时影响多个位置时只保留一份规则正文，其他入口链接过去。

## 2. 通用 P0 硬停

- **先定目标和边界**：确认真实仓库、分支、用户要求和允许修改的范围。不要把旁边 checkout、历史 worktree 或另一个仓库的规则当成当前目标。
- **Live facts > knowledge**：当前代码、远端状态、PR head、CI、进程、GPU、路径、环境变量和账号身份以本轮 live 证据为准；指南和错题只作线索。
- **No fake evidence**：没有 source、diff、日志或实测证据不下结论。编译通过、shape 正确、stub smoke 和进程已经退出不能替代真实行为验证。
- **No silent fallback**：不要用隐式默认值或静默降级掩盖错误路径。必要 fallback 必须有明确条件、可见信号和验证。
- **No broad kill/delete**：删除、移动或清理前确认绝对路径和归属；远端只清本轮能够证明归属的进程和文件。
- **保护他人状态**：共享机器、旁边仓库、用户已有改动和未跟踪文件默认不属于本轮；未经授权不修改、不清理、不覆盖。
- **公开前做隐私检查**：公开文档、commit、PR、issue 和日志不得包含凭据、私人地址、内网机器信息或用户绝对路径。
- **用户纠正后刷新证据**：用户指出目标或事实错误时，停止维护旧结论，重新确认范围和 live 状态。
- **说人话**：先报告结果、影响和需要决定的事情；内部术语只作为证据。

## 3. 场景触发器

| 用户正在做什么 | 必读入口 | 最低要求 |
|---|---|---|
| 写代码或修改公开接口 | [code taste](framework/review/guides/code-taste.md) | 先理解现有 owner、调用链、测试和用户可见行为 |
| 开发完成、准备交给 reviewer 或项目 owner | [维护者审查闭环](framework/agents/guides/agent-loop-workflow.md#开发交付的维护者审查闭环) | 独立 reviewer 全量审 diff，修复后重审，直到没有实质问题 |
| code review 或 reviewer follow-up | [独立审查执行合同](framework/review/guides/review-execution-contract.md) | 先完成 owner 规则、公开入口和 producer→consumer 覆盖，再开放找问题 |
| UI、CLI、文档或其他用户可见改动 | [用户可见验收](framework/docs/guides/user-visible-acceptance.md) | 绿测之外还要跑普通用户真实路径 |
| benchmark 或性能结论 | [benchmark contract](framework/benchmark/guides/benchmark-contract.md) | 先固定版本、工作负载、指标和证据来源 |
| SSH、容器、远端服务或长跑 | [远端入口](framework/remote/_index.md) | 先验证目标、环境、超时、状态文件和清理边界 |
| 多 agent 或并行工作 | [agent loop](framework/agents/guides/agent-loop-workflow.md) | 只拆能独立验证的任务，主 agent 复核结论 |
| 产品规划或 roadmap | [产品闭环](framework/planning/guides/product-loop-planning.md) | 先写用户可感知的完整闭环，再拆技术任务 |
| 复盘、沉淀经验或总结教训 | [复盘到规则](framework/debug/guides/retrospective-to-rules.md) | 默认更新最近 owner 的规则；只有复杂证据值得长期保留时才新增错题 |

仓库入口链接的 `rules.md` 可以增加更严格的门禁，但不能放宽这里的通用 P0。

## 4. 知识写到哪里

- 能反复避免问题、改变下一次行为的结论 → 最近 owner 的 `rules.md`。跨仓库规则放 `framework/<主题>/`，仓库规则放 `repos/<仓库>/`，模块或模型规则继续下沉到对应目录。
- 稳定的数据流、职责和边界 → 最近 owner 的 `architecture.md`。
- 需要展开说明但不是硬门禁的方法 → 对应主题的 `guides/`。
- `incidents/` 只保存规则无法承载的复杂复现、证据链或历史背景；它可有可无，不能成为正常开工必须猜路径才能找到的知识入口。
- 当前机器事实 → ignored `local/`。

用户要求“复盘”时，必须回答为什么发生、为什么原有规则或测试没有发现、怎样提前阻止，并把可执行结论写进最近 owner 的 `rules.md`。只有事故过程本身仍有独立查询价值时，才同时保留一篇 incident 并从规则链接过去。

长期知识禁止写入系统、全局或个人 memory 位置。新增、移动、拆分或删除 Markdown 前先读短入口 [CONTRIBUTING.md](CONTRIBUTING.md)，再按任务只读它链接的一篇专题规范；同步最近的 `_index.md`，然后运行：

```powershell
python tools/check_knowledge_tree.py
```

## 5. Git 和公开修改

- 先读 [通用 Git 入口](framework/git/_index.md)，再读当前仓库自己的 Git/PR 规则。
- 提交前确认 diff、分支、remote、作者身份、签名要求和目标 PR；这些不能从其他仓库继承。
- 用户只要求分析、解释或 review 时，不自动 commit、push、改 PR 或修改外部状态。
- 用户明确要求发布时，只发布已经确认属于本轮的文件；未跟踪输出和其他人的改动默认排除。

## 6. 总入口

- 通用经验：[framework/_index.md](framework/_index.md)
- 仓库经验：[repos/_index.md](repos/_index.md)
- 贡献与目录维护：[CONTRIBUTING.md](CONTRIBUTING.md)
- 当前机器信息：ignored `local/`
