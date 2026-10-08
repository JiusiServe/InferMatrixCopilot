# 知识初始化与维护：分层与边界

初始化和维护都经 `WorkflowExecution.execute` 运行各自的计划，复用 Copilot 的
执行锁、步骤调度、检查点验证和清理。知识领域仍持有业务事实。Review bot 通过公开 SDK v1
提出候选、读取知识并执行消费侧防护。主图展示职责；Python 类清单作为展开视图，
不把记录、异常或协议各自画成一个服务。

![知识生命周期分层](knowledge-lifecycle.svg)

## 现有抽象与职责

| 层／组件 | 现有实现 | 职责 |
|---|---|---|
| 执行入口 | `Copilot`、`WorkflowExecution`、`Executor` | 选择入口后执行绑定的计划；管理运行锁、步骤进度、类型化失败和清理。 |
| 初始化 | `InitRuntime`、`run_stage`、`init_execution`、`_Stage`、`InitRecord` | 五阶段计划；领域步骤固定范围和版本，生成、审核、验证并准备发布。 |
| 维护 | `Scheduler`、`KbRuntime`、`maintenance`、`MaintenanceStore` | 现有调度器提交纠错／夜间复查两步计划；SQLite 持有周期、请求、预算与发现。 |
| 内容与证据 | `Page`、`Section`、`Footer`、`KnowledgeOperation`、`Claim`、`Evidence` | 无损内容变换、生命周期操作、来源身份和适用版本。 |
| 审核与准入 | `gate`、`maintenance_policy`、`maintenance_resolution` | 确定性验证、独立审核、纠错资格及带证据的负责人处置。 |
| 分发与撤回 | `InitPublisher`、`Publisher`、`activate`、`containment` | 各自权限内发布；独立于快照的签名撤回和恢复确认。 |
| 消费 | `KnowledgeView`、`KnowledgeDocs`、`KnowledgeContextService`、SDK v1 | 固定任务快照、限定读取、累计会话预算、交付与使用回执。 |
| Review bot | `ReviewPipeline`、`KnowledgeDistiller`、`KnowledgeMaintenance`、`ReviewPublisher` | PR 输入、候选交接、消费侧防护及共同的 GitHub 发布边界；模型执行由 SDK 统一管理。 |

模型／Git transport、账本、签名和预算支撑各层。初始化记录、维护 SQLite、
improve 周预算、发布 outbox、消费会话及撤回高水位保持各自存储和恢复范围。
共用执行器的进度只记录步骤结果和内容绑定的产物引用，不再建立另一套业务账本。
执行内核不反向依赖知识流程；
bot 的运行代码只依赖 `infermatrix_copilot.sdk.v1`。

## 两条流程入口

初始化继续使用 `run_stage(...) -> InitRecord`，阶段名、参数和记录格式保持兼容。
CLI、Python 和 `knowledge.init` 都进入 `init_execution.execute_init`，提交同一五阶段
计划给 `WorkflowExecution.execute`。入口先在阶段批次锁内绑定输入与执行身份；
`_Stage` 及其专用阶段保留领域操作和扩展点，
不再自行运行一套准备、恢复、验证和发布循环。

| 执行阶段 | 领域职责 |
|---|---|
| `prepare` | 在已绑定的仓库、范围、pin、基线及策略上检查依赖和已有记录，恢复领域进度。 |
| `draft` | 调用对应初始化阶段；生成候选、审核，并保存原始来源与审核回执。 |
| `validate` | 对确定的正文及证据运行确定性验证、容量和完整性检查。 |
| `prepare_publication` | 应用该阶段准入要求，固定待发布正文、元数据及验证绑定。 |
| `publish` | 复验发布资格，再生成预览或推进原有幂等发布。 |

执行进度和领域记录职责分开：步骤恢复须验证产物及当前事实；旧步骤成功记录不能代替
来源、原生审核回执、当前配置或发布准入。`InitRecord` 保存领域结论及发布事实，
不可变产物绑定正文与验证依据；缺少业务事实时不能仅凭执行检查点继续发布。

维护模块提供以下函数，不新增流程门面类：

| 函数 | 行为 |
|---|---|
| `plan(rt, repos=None)` | 只读选择计划，不调用模型。 |
| `status(rt, repos=None)` | 原有计划、运行、发现、费用和传播报告。 |
| `request(rt, request_id, repos=None, *, options=None)` | 只持久化一个仓库或全部仓库的请求；同 ID 和输入幂等，不获取调度租约。 |
| `run_due(rt, *, on_correction=None)` | 验证现有租约，先推进纠错，再运行夜间复查；返回两类结果。可选回调立即记录纠错事件，即使后续复查失败也保留诊断。 |
| `run_due_async(rt, *, on_correction=None)` | 异步执行入口；直接等待同一维护计划。同步入口保留现有调度器兼容性。 |

`repos=None` 表示全部仓库；`request` 的明确选择只接受单个仓库。CLI 继续使用
`kb maintain plan|run|status --repo ID|--all`。Intake、版本巡检及消费者升级顺序不变。

维护计划注册 `knowledge.maintain.correction`、`knowledge.maintain.nightly_audit` 两步，
同样调用 `WorkflowExecution.execute`。两步均设置 `checkpoint=False`，每次重新检查
当前租约和领域状态；SQLite 周期、请求及费用记录继续决定续跑范围。执行目录绑定周期
和策略，运行器只持有本次资源与结果。它不复制 SQLite 进度，也不拥有发布权限。

`maintenance_policy` 提供策略指纹、就绪条件、纠错发布资格和精确提交 CI 证明。
合并与恢复直接使用这些函数，并在执行边界重新读取当前证据。
`maintenance_resolution` 在调度租约下验证签名、负责人和原始证据，追加处置及人工案例；
CLI 仅负责获取实际身份、准备签名请求和提交。

## 共享能力与预算所有者

`init_content` 是确定性内容模块。它接收文件树、操作、标题、日期、版本、路由和
快速索引配置，返回新的文件树以及 `PlacementResult` 中的页面、标题、溢出关系、
提示和拒绝原因。它不读取运行环境、检查点或模型；`_Stage` 记录返回的变化。
阶段的路由、标题和审核扩展点保留，规则仍按累计树先放置、后审核。

`KnowledgeCurator` 保留 SDK 构造参数和公开方法，委托给 catalog、prompt、proposals、
apply 模块函数；工作目录、限制和锁显式传递。它负责受限的新规则追加，成功应用仍是
本地候选，不等于通过独立语义审核或正式发布。服务端替换／退役继续走完整生命周期门禁。

`git_objects` 共用 Git 树、blob 和差异读取／解析过程，原有适配器保留独立来源、fetch、
缓存、文件模式、编码及异常策略。`providers.completion` 共用单次原生模型调用、部分事件
和最终回执；知识 schema、角色独立性、提示词及重试上限仍由调用领域决定。
Intake、版本巡检和纠错复用有界操作生成与修复循环，保护约束和目标范围由各入口检查。

`budgeting` 共用成本上界、额度判断、保守结算和预留生命周期；`persistence` 共用原子／
不可变写入。共享这些机制不会合并初始化、每日维护和 improve 周预算的额度或存储。

| 预算所有者 | 额度与恢复事实 |
|---|---|
| 初始化 `Budget` | 阶段额度；检查点在派发前记录已结算和未完成预留，重启按原记录恢复。 |
| `MaintenanceStore` | 每日复查／纠错额度及轮查预留；SQLite 事务和调度租约约束并发与续跑。 |
| improve `Governor` | 每周费用和审核调用额度；文件锁和带周期的预留身份约束结算与恢复。 |

模型调用在核算锁之外执行，先持久预留、后派发、再结算。失败或费用未知时保守计入
预留；API 实际计费与订阅核算分开记录，不能把订阅费用未知显示为零。
初始化的 `checkpoint(spent_usd, reserved_usd)` 及 `checkpoint_now` 在同一核算锁下保存
记录，防止并行任务保存进度时覆盖其他调用的预留。写入失败后停止该实例的后续派发，
从持久状态恢复后再继续。

类清单直接从当前源码生成，包含记录、异常、协议、私有、嵌套及函数局部类。
主图中的能力节点不等同于类数；实际数量与文件摘要以生成的 JSON 和覆盖证明为准。

## 与 review bot 的连接

候选学习使用 `KnowledgeDistiller → SDK KnowledgeCurator.curate`，
然后由 bot 的账本和 Git 交接记录导出，经负责人提升和现有 provider 门禁进入正式知识。

消费保持两条现有路径：

- Direct：隔离 Host 通过 SDK `ReviewRuntime` 提交耐久请求，由 provider 调用 `DirectClient.plan/validate`、共享原生模型 transport 和执行底座，分别记录检索和实际注入。
- Strict：同一隔离 Host 调用 SDK `ReviewRuntime`（兼容名 `StrictRuntime`），经过 `RunService` 和现有执行底座，传回 provider 签发的使用记录。

bot 不再保留完整的旧 Direct 分支、候选模型循环或 Codex/Cursor 评审执行入口。
远程 worker 也消费公开 SDK；它持有远程任务与容量，SDK 持有实际模型运行及其恢复身份。

两者共同经过 `ReviewPublisher`。公开边界始终为 `infermatrix_copilot.sdk.v1`；
`init_execution`、领域账本和模型适配器不成为 bot 的私有调用入口。
bot 的 `KnowledgeMaintenance` 是 SDK 消费侧适配器，
不进行权威复查或纠错。发布在共享互斥锁内检查当前可用性，并在 GitHub 写入前复查；
被撤回内容影响的结果保留历史，暂停并以新上下文重新评审。

| 身份 | 用途 |
|---|---|
| 上游适用版本 | 原始证据支持哪个版本的结论。 |
| 知识快照与正文摘要 | 任务实际使用的内容。 |
| 撤回清单代际 | 当前使用资格；回滚不能降低代际。 |
| bot/provider 配对版本 | 部署兼容性和实际安装内容。 |

服务端激活不等于 bot 已升级；bot 通过已有配对发布流程获得新的打包内容。
撤回通过独立签名通道传播，消费状态位于物理 release 之外。
`kb maintain status` 是权威维护报告；SDK `knowledge_maintenance_status` 是消费侧协议状态。

## 策略与验证

维护实现变化会改变策略指纹。提取后的策略和负责人处置实现均纳入指纹；历史观察、
校准和演练原样保留，但不能为新策略提供旧授权。默认启用状态、预算、模型、配置、
发布权限及七个有效夜间周期的上线门禁均不改变。

验证覆盖 SDK 字节和返回契约、内容容量与放置顺序、预算并发及崩溃恢复、租约与请求
幂等、旧策略拒绝、Direct／Strict 撤回与重评，以及 bot/provider 配对兼容性。
完整 Python 类展开清单由 `tools/render_knowledge_lifecycle.py` 从实际源码生成。
