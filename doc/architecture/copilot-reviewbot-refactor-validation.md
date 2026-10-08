# Copilot / Review Bot 重构验收记录

状态：功能迁移、两仓完整离线测试及最终安装包验证已完成；provider 和 bot 的固定基线代码收敛门禁未通过，整体重构尚未验收，保持草稿。验证日期：2026-10-09（Asia/Shanghai）。设计见[细粒度重构设计](copilot-reviewbot-refactor-design.md)。

主线整合：provider 纳入 `82c69f90` 的网关输入预留修复，bot 纳入 `da22d631` 的远程 worker 能力。远程 Direct 迁入同一耐久 SDK 路径；worker 未完成的 provider 运行继续占用容量，重启保留未知状态。下文使用整合后重新冻结的生产源码。整合前的完整测试与 wheel 证据单独保留，不用于证明当前源码通过。

## 实施边界

- Copilot 的 `WorkflowExecution.execute` 统一驱动初始化、维护、自改进和 Direct 评审；Executor 不再导入知识或自改进业务。步骤授权在成功缓存重放之前执行。
- 初始化继续使用原业务批次、检查点、prepared 发布协议和账本；draft、validation 与 publication 通过不可变产物绑定。通用步骤进度不替代业务证据。
- SDK 的 `ReviewRuntime` 复用原 Strict runtime 与 RunService；旧 `StrictRuntime` 名称保持类身份。Direct 请求绑定可信部署 profile、原始幂等指纹及启动时的精确请求字节，排队后篡改命令或启动后替换输入均拒绝执行。
- bot 保存请求意图和 `provider_run_id`，管理 GitHub 输入、队列、路由和最终发布；provider 拥有知识计划、模型运行、有限修复与完成验证。
- Direct 与 Strict 共用既有 SQLite metadata 的原子执行位置绑定。恢复、采用旧 ID、提交及轮询前，核对本地固定运行目录或远程实际 URL / 配对版本 / 运行配置；配置改变时暂停，不能在另一位置重新派发。同一任务的已有付费意图若缺少历史绑定，保留原记录并暂停，不能猜测执行位置。worker 原有请求哈希检查与按原配置轮询的保护继续保留。
- 远程 worker 的 SDK 轮询切片结束或响应未知时，保留同一 job 和容量并继续查询原运行；关闭时保留未决记录。已持久化终态失败保留 failure class；未知响应不能伪装成终态失败触发新付费 fallback。
- 预算共享预留、调用事实和结算机制；各领域仍拥有自己的账本和额度。已绑定且有可信核算上界的账户覆盖未知费用、已发送失败、实际超支与重复结算。MoA 的订阅 CLI harness 不计入 API 美元上限；DeepSeek API-keyed harness 的费用未知且没有支持的美元上界。总 deadline 不会强行终止在途 SDK 调用，这些限制保持明确。
- 共享 transport 保留原生权限、禁止工具事件、进程树清理、idle/absolute 超时及同会话修复。不同原生 CLI 的权限协议未强行合并。
- 受保护规则、独立审核、来源版本、shadow、私有仓库、撤回与发布锁保持原边界。新共享实现纳入策略指纹，旧校准和观察记录不能授权新策略。

## 实际删除的重复实现

| 原实现 | 替代位置 | 保留的领域职责 |
|---|---|---|
| MoA `BudgetedLLM` 与独立 `for_member` 客户端组装 | 公共预算绑定与 `for_target` | MoA 额度与投票 |
| 自改进 judge 的原生命令、响应解析和工作区管理 | provider transport | 模型独立性与评判策略 |
| 初始化、维护和自改进的金额计算及预留/结算机械流程 | `budgeting.py` | 原 journal / 周 JSON / SQLite |
| bot `knowledge_model.py`、`knowledge_curation_cycle.py` | SDK `KnowledgeCurator.curate` 与 bounded attempts | clone、候选账本、导出和负责人交接 |
| bot Codex/Cursor 评审模型进程与修复主体 | provider JSON session 与 Direct 步骤 | 路由、GitHub 业务和发布 |
| bot 内部构造仍可触发的完整旧 Direct 流程与 Runner 旁路 | 唯一耐久 provider 路径 | 旧 SDK API 继续兼容，内部测试注入转为公开 SDK 替身 |
| triage 与 owner router 的重复 Cursor 命令和 JSON envelope 解析 | SDK 受限 JSON session | 分类政策、失败诊断及恰好一次的调用预算 |
| proposal 预检与持锁 apply 中重复的 section / ID / 来源检查 | 共享规则校验 | 持锁复验与精确回滚 |
| 多处 diff hunk 起点和添加行解析 | 既有 diff index | UT、覆盖、风险的不同判断 |
| 主候选、边界目录与合并目录审核的重复批处理 | `DiscoveryEngine._review_batches` | 各自来源绑定、历史及尝试次数 |
| 多处临时文件/fsync/replace 与 Git 对象解析 | 公共字节写入与 Git 解析函数 | 权限、编码、模式和来源错误边界 |

## 固定基线与收敛门禁

provider / 知识基线：`f17d8022f7fca7d00063f85213321ed4ef8e5187`。
bot 基线：`97afeca0112e29bde254f1963cf8b4bfee272dea`。

使用 `tools/measure_knowledge_refactor.py --bot-root <bot-worktree>` 统计全部生产 Python、运行 YAML；bot 同时计入运行 JSON。新增公共实现、兼容代码均计入，排除测试、文档及工具。知识模块是 provider 的子集，两者不可相加。

目前 provider 和 bot 相对固定基线仍净增长，不能将“删除了重复实现”表述为“全部生产代码已净减少”。未改变基线，未用迁目录、删除注释或压缩排版抵消增量。

| 范围 | 生产行数：基线 → 当前 | 行数变化 | AST 语句变化 | 类数：基线 → 当前 | 净减少门禁 |
|---|---|---:|---:|---|---|
| 知识模块 | 32,678 → 32,655 | −23 | −3 | 124 → 124 | 通过 |
| 全部 provider（含知识及公共代码） | 91,251 → 92,525 | +1,274 | +839 | 396 → 399 | **未通过** |
| bot | 33,764 → 34,757 | +993 | +1,147 | 152 → 172 | **未通过** |

累计两仓生产行数增加 2,267，AST 语句增加 1,986。bot 此次纳入的主线增加了远程 worker 等功能：相对捕获的 bot 主线 `da22d631`，本分支减少 1,309 行、426 条 AST 语句和 6 个类；这是上下文，不能替代原定固定基线验收。相对 provider 主线 `82c69f90`，本分支增加 1,515 行、945 条 AST 语句，减少 2 个类。

独立审查未找到已迁移职责中足以抵消 provider 增量的安全重复实现。初始化的产物证明、
旧记录恢复、发布协议、凭据 broker 与不同原生 CLI 权限不能仅为满足数字而删除。
因此不能报告“重构全部完成”，也不能合并或改变自动维护启用状态。

最终生产冻结清单的内容摘要（按相对路径及 SHA-256 排序序列化）：

- provider：`a3b904ef46b7fef1b467a3bc503c6caeaa2bc945e375ad5dd6caa1ddc308117f`。
- bot：`6ea4d192ded3d415d35a5ffb2e0ae7d89593033e9a5c7b1cba72779b46b071db`。

冻结清单同时覆盖生产 JSON（510 / 128 个文件）；摘要使用相对路径到 SHA-256 的映射、排序后的默认 JSON 序列化。计量表继续采用约定的统计范围，不因清单扩大而重设基线。wheel 另核对所有包内文件，包含知识及运行资源。provider 包内有 393 个类，另有 6 个 adapter plugin 类；知识的 124 个类包含在其中。

## 验证方法与范围

两端全量离线测试、真实子进程 fake CLI 的 Direct / Strict 端到端测试，以及独立 wheel 安装测试分别运行。模型输出由隔离 fake CLI 提供；Git、SQLite、SDK、运行锁、请求持久化及子进程边界使用真实实现。没有调用付费模型或向生产 GitHub 发布评审。

| 场景 | 验证范围 |
|---|---|
| 初始化完整迁入执行器 | 所有阶段门禁、阶段间崩溃、旧 prepared、预算提升、预览转发布、不可变产物损坏与并发批次锁 |
| 夜间维护 | 未变化但错误的知识、缺失/不支持来源、暂停与续跑、重复请求、未知费用、shadow 与保护规则 |
| 撤回 | 旧快照、旧缓存、Direct 文档路径、Strict 使用及最终发布；修订只恢复新内容，回滚不清除旧禁用记录 |
| Direct | Codex/Cursor、零条/多条 finding、完整 diff、既有讨论处置和 head 复查、同会话修复与终端错误分类 |
| 跨进程恢复 | 先持久化意图后预留；响应丢失和 ID 未落盘时使用同一幂等键恢复，不重复启动 |
| 执行位置与旧记录 | Direct / Strict、本地 / 远程、实际 URL / release / run root / checkout / provider 变化时暂停；旧付费意图缺少绑定时不写入推测绑定、不启动或轮询另一个运行 |
| 远程 worker | 响应丢失后只有一次 checkout、一次模型派发和一次发布；非路由任务使用稳定 job 身份；未知运行继续占用容量并保留重启阻断 |
| 权限 | 未登记 profile、排队请求换命令、启动后输入篡改、禁止工具事件与 GitHub 凭据隔离 |
| 预算 | 并发预留、跨周/跨日、可信实际费用、未知费用全额记账、重复结算与持久化失败 |
| 安装包 | 无 editable / source PYTHONPATH；公共导出冷导入、签名/序列化、资源完整性、release SDK 配对及 wheel 内真实子进程 E2E |

provider 全量覆盖全部 231 个 `test/test_*.py`；bot 全量覆盖仓库配置的 tests 目录。运行环境为 Python 3.12.13；隔离全量测试环境安装项目声明的 MCP 1.x optional dependency，未使用机器上不兼容的 MCP 2.x。

最终 provider 全量 JUnit：4,362 项，**4,344 通过、18 跳过、0 失败、0 错误**。三个不重叠、各含 77 个文件的分片分别为 1,455 / 1,433 / 1,456 项通过，17 / 0 / 1 项跳过；测试前后生产源码与最终冻结清单一致。

最终 bot 全量 JUnit：**2,589 通过，0 跳过、失败或错误**，退出码 0，耗时 396.41 秒；测试前后 128 个生产文件与最终冻结清单一致。最终源码提交为 `7fce46bb4a24b02b486ea5bfed62bd3394b17d13`。额外检查包括网关预算与公共预算 62 项、Direct / Strict 执行位置绑定相关 277 项、默认目录修复后的 104 项，以及远程配置修复后的 45 项；这些定向结果不累加到全量通过数。

最终安装包套件 **137/137 个唯一用例通过，0 跳过、失败或错误**，含原 77 项、全部 10 项真实 SDK / 原生 CLI 端到端场景、18 项恢复、30 项实际 Strict 绑定和 2 项 worker pending / 容量测试。125 项公共签名检查与上一已验证快照一致，冷导入不加载运行服务或知识实现；Direct 1.1 / Strict 1.4 / Knowledge 1.1 配对验证通过。

两个 wheel 从独立源码副本构建，并在隔离环境非 editable 安装；测试使用 `Python -I`，没有源码 `PYTHONPATH`。provider 的 2,196 个代码／资源文件和 bot 的 128 个文件在源码、wheel、已安装目录中逐字节一致。README、pyproject 和实际 METADATA 另行核验；知识、adapter、playbook 和 skill 资源完整。安装包测试结束后仍匹配最终生产冻结清单。

整合前的 77 项证明、以及后续修复前的中断测试和 129 项快照，均单独保留历史目录，仅用于追溯，不能累加为当前源码的独立通过数。

已知环境限制：外部 `vllm-omni-rebase-agent` checkout 未安装，16 项跨仓库测试和 1 项父模板比较测试跳过。补验调查确认原仓库可授权读取，但可见远端找不到适配器约定的 EXT1 pin `0395bbe`，本地也没有准确 checkout；未用远端旧 main 或重造 guard 替代依赖。内核禁用 user namespaces，1 项真实 namespace sandbox 隔离测试跳过，未改变主机内核策略。不能将这些跳过描述为通过。付费模型、生产 GitHub 写入、真实七夜观察和自动维护启用不在本次离线验收结果内。
