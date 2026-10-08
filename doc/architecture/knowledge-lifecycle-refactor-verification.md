# 知识生命周期复用：验收记录

> 历史阶段记录：本页对应 `f88d7e78` 的验证快照。后续 Copilot / bot 联合重构的最终范围、数量与未通过门禁见[最新验收记录](copilot-reviewbot-refactor-validation.md)；本页数值不代表当前分支。

本轮基线为 `f17d8022f7fca7d00063f85213321ed4ef8e5187`。
功能迁移进入草稿审查；**生产代码净减少门槛尚未通过**。
不将移目录、注释变化或类数不变表述为代码收敛。

## 代码量

运行 `python tools/measure_knowledge_refactor.py` 可复现统计。
范围包含生产 Python、新增公共模块、adapter 插件和运行 YAML，排除测试、文档和工具。
同时报告物理行数和 AST 语句数，避免用压缩排版制造减少。

| 范围 | 基线行数 | 当前行数 | 净变化 | AST 语句净变化 | 类数 |
|---|---:|---:|---:|---:|---:|
| 知识模块 | 32,678 | 32,772 | +94 | 0 | 124 → 124 |
| Provider（含 adapter 插件与运行 YAML） | 91,251 | 91,604 | +353 | +179 | 396 → 396 |

Provider 的 Python 部分净增 336 行，新增执行计划另增 17 行。
AST 语句与类只统计 Python；分层图的完整附录范围为 src 包中的 390 个类，
表格另包含未改动的 6 个 adapter 插件类。

新增的不可变阶段产物、缓存绑定和恢复核验超过了本轮删除的重复实现。
后续收敛必须继续删除同功能实现；不能删除这些校验来满足行数要求。

## 已删除的重复执行与函数体

| 原实现 | 本轮共享实现 | 保留的业务边界 |
|---|---|---|
| `_Stage.run` 通用运行循环、`_PrHistory.run` 和 discovery 的运行包装 | `WorkflowExecution.execute`、Executor 和五阶段计划 | 批次锁、原始 inputs digest、原生来源证明、阶段业务单元恢复及精确 head 审核 |
| 知识 runner 单独组装 Executor；步骤模块 `_RUNTIME`、`_STATE_DIR` 全局状态 | 注入 `StepContext.runtime` 的公开执行底座 | 初始化运行环境不依赖服务 SQLite；运行对象不序列化 |
| 知识 ModelGateway 与 HarnessLLM 的 completion、事件及失败整理 | `providers.completion.complete_native` | 显式模型、独立模型族、schema、fallback 和 transport 权限 |
| 多个 transport 的缓冲子进程、JSONL 解析、用量到结果转换 | `providers.base.run_cli/json_events`、SessionUsage 方法 | 认证、环境白名单、工作目录、隔离、流式协议与模型核验 |
| 初始化、维护、自改进的金额计算与预留调用生命周期 | `budgeting` 函数 | 初始化记录/journal、维护 SQLite、自改进周 JSON 的各自上限与锁 |
| 多处临时文件、fsync、替换与清理函数体 | `persistence` 字节写入函数 | 序列化、权限、硬链接排他、调用方的目录同步策略 |
| 服务端与发布端的 Git tree/blob/raw diff 解析循环 | `git_objects` | 独立读取、缺失语义、模式、UTF-8 与 SHA-1/SHA-256 |
| intake、sweep、纠错的候选解析/应用/反馈循环 | 受限的 `draft_operations`、`prepare_operations` | 操作集合、范围、重试次数、既有提示词和完整发布门禁 |
| 初始化 serial/parallel 的逐条生成审核、重复 depth 证据及页面组装 | 领域函数和 `_sections` | 原始审核回执顺序、累计页面顺序、每次重新读取来源 |

## 恢复与费用验证

阶段产物绑定正文、来源 pin、知识 base、原业务 inputs digest 和执行指纹。
新发布准备绑定固定内容及正文；旧 prepared 按原发布协议优先恢复。
知识主干出现无关提交不重新生成候选，也不改变原发布提交。
损坏、越界或绑定错误的产物拒绝重放；缺失业务事实不能借用旧成功进度。

原生证明失效时保留原记录字节，不覆盖为新空记录。
Partial 输出可传递到后续门禁，但不保存阶段成功标记。
并行 worker 的在途预留与协调器领域进度在同一预算锁内保存。
无可信用量按完整预留结算；重复结算 token 不重复扣费，旧待结算额度继续占用。
持久化失败传播并阻止继续派发。

## 最终离线验证

- Provider 完整离线测试：4,253 通过、18 跳过；按测试文件分为三个互不重叠的进程，退出码均为 0。
- Review bot 完整测试：2,213 通过；使用本轮 provider 源码，bot 生产代码没有改动。
- 最终安装包与源码中的 2,191 个代码及资源文件一致，85 个公开 SDK 签名与原接口一致。
  从隔离环境安装 wheel 后，Direct、Strict、候选处理和签名撤回协议检查均通过。
- 初始化领域处理与基线差分：152 个页面放置输入和 12 个 depth 页面、证据、顺序及 observer 调用场景一致。
- 文档链接与引用检查通过；严格 SPEC 检查覆盖 102 页，无过期、漏项或孤立声明。

最终验证未调用付费模型，也未写入生产服务状态。

## 兼容与上线

SDK、同步 run_stage 签名、InitRecord 必填字段、页面与证据字节保持兼容。
Review bot 继续通过公开 SDK 接入；生产业务代码无改动。
MoA 本轮未迁移。维护策略指纹覆盖新增公共机制；旧观察、校准和演练保留，
不能授权新策略。预算、模型、部署配置与发布权限未修改。
自动维护仍须经过新策略校准和七个有效夜间观察周期。
