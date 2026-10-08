# Copilot / Review Bot 重构验收记录

状态：功能迁移与完整离线验证已完成；provider 代码收敛门禁未通过，整体重构尚未验收，保持草稿。验证日期：2026-10-09（Asia/Shanghai）。设计见[细粒度重构设计](copilot-reviewbot-refactor-design.md)。

## 实施边界

- Copilot 的 `WorkflowExecution.execute` 统一驱动初始化、维护、自改进和 Direct 评审；Executor 不再导入知识或自改进业务。步骤授权在成功缓存重放之前执行。
- 初始化继续使用原业务批次、检查点、prepared 发布协议和账本；draft、validation 与 publication 通过不可变产物绑定。通用步骤进度不替代业务证据。
- SDK 的 `ReviewRuntime` 复用原 Strict runtime 与 RunService；旧 `StrictRuntime` 名称保持类身份。Direct 请求绑定可信部署 profile、原始幂等指纹及启动时的精确请求字节，排队后篡改命令或启动后替换输入均拒绝执行。
- bot 保存请求意图和 `provider_run_id`，管理 GitHub 输入、队列、路由和最终发布；provider 拥有知识计划、模型运行、有限修复与完成验证。
- 预算共享预留、调用事实和结算机制；各领域仍拥有自己的账本和额度。未知费用、已发送失败、实际超支、重复结算不再造成漏计。
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

目前 provider 仍净增长，不能将“删除了重复实现”表述为“全部生产代码已净减少”。未改变基线，未用迁目录、删除注释或压缩排版抵消增量。

| 范围 | 生产行数：基线 → 当前 | 行数变化 | AST 语句变化 | 类数：基线 → 当前 | 净减少门禁 |
|---|---|---:|---:|---|---|
| 知识模块 | 32,678 → 32,655 | −23 | −3 | 124 → 124 | 通过 |
| 全部 provider（含知识及公共代码） | 91,251 → 92,498 | +1,247 | +825 | 396 → 399 | **未通过** |
| bot | 33,764 → 32,318 | −1,446 | −529 | 152 → 146 | 通过 |

累计两仓生产行数减少 199，但这不能替代约定的分项门禁；AST 总量仍增长 296。
独立审查未找到冻结范围内足以抵消 provider 增量的安全删除点。初始化的产物证明、
旧记录恢复、发布协议、凭据 broker 与不同原生 CLI 权限不能仅为满足数字而删除。
因此不能报告“重构全部完成”，也不能合并或改变自动维护启用状态。

最终生产冻结清单的内容摘要（按相对路径及 SHA-256 排序序列化）：

- provider：`62ea70da020b7d924fa693bc345b59410f0f45064bcf9dd0e152171401e6a27f`。
- bot：`c95b2e86b343d689f89d1821dcf6e4dc028b57a598157a3c5ff844c97b12fee6`。

冻结清单同时覆盖生产 JSON（510 / 120 个文件）；计量表继续采用约定的统计范围，不因清单扩大而重设基线。wheel 另核对所有包内文件，包含知识及运行资源。

## 验证方法与范围

两端全量离线测试、真实子进程 fake CLI 的 Direct / Strict 端到端测试，以及独立 wheel 安装测试分别运行。模型输出由隔离 fake CLI 提供；Git、SQLite、SDK、运行锁、请求持久化及子进程边界使用真实实现。没有调用付费模型或向生产 GitHub 发布评审。

| 场景 | 验证范围 |
|---|---|
| 初始化完整迁入执行器 | 所有阶段门禁、阶段间崩溃、旧 prepared、预算提升、预览转发布、不可变产物损坏与并发批次锁 |
| 夜间维护 | 未变化但错误的知识、缺失/不支持来源、暂停与续跑、重复请求、未知费用、shadow 与保护规则 |
| 撤回 | 旧快照、旧缓存、Direct 文档路径、Strict 使用及最终发布；修订只恢复新内容，回滚不清除旧禁用记录 |
| Direct | Codex/Cursor、零条/多条 finding、完整 diff、既有讨论处置和 head 复查、同会话修复与终端错误分类 |
| 跨进程恢复 | 先持久化意图后预留；响应丢失和 ID 未落盘时使用同一幂等键恢复，不重复启动 |
| 权限 | 未登记 profile、排队请求换命令、启动后输入篡改、禁止工具事件与 GitHub 凭据隔离 |
| 预算 | 并发预留、跨周/跨日、可信实际费用、未知费用全额记账、重复结算与持久化失败 |
| 安装包 | 无 editable / source PYTHONPATH；公共导出冷导入、签名/序列化、资源完整性、release SDK 配对及 wheel 内真实子进程 E2E |

provider 全量覆盖全部 230 个 `test/test_*.py`；bot 全量覆盖仓库配置的 tests 目录。运行环境为 Python 3.12.13；隔离全量测试环境安装项目声明的 MCP 1.x optional dependency，未使用机器上不兼容的 MCP 2.x。

最终 provider 全量 JUnit：4,350 项，**4,332 通过、18 跳过、0 失败、0 错误**。三个不重叠文件分片分别为 1,437 / 1,302 / 1,593 项通过，17 / 0 / 1 项跳过。bot 最终全量 JUnit：**2,241 通过、0 跳过、0 失败、0 错误**。两端最终完整测试前后生产源码与冻结清单一致。

额外验证：冻结 API / Direct / native session / 幂等 / MCP 134 项通过，知识发现 212 项通过，分类共享 transport 103 项通过。安装包套件 **77/77 通过**，125 项公共签名冷导入及 release SDK 配对验证通过；包内、已安装内容与最终冻结生产清单逐字节一致。安装包验证没有 editable 安装或源码 PYTHONPATH。随后在相同已安装 wheel 上重复增强四个真实 SDK Host / 原生 CLI E2E，4/4 通过，验证 Cursor 实际模型名回传、路由 runner 隔离及恢复不重复派发；这是重复增强验证，不算成 81 项独立用例。

已知环境限制：外部 `vllm-omni-rebase-agent` checkout 未安装，16 项跨仓库测试和 1 项父模板比较测试跳过；内核禁用 user namespaces，1 项真实 namespace sandbox 隔离测试跳过。不能将这些跳过描述为通过。付费模型、生产 GitHub 写入、真实七夜观察和自动维护启用不在本次离线验收结果内。
