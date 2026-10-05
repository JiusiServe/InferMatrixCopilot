# 用自进化引擎改进 Copilot 工作流

默认评估模式为 `objective`，采用模式为 `automatic`。开启进化后，系统自行收集输入、提出假设、生成补丁、运行隔离实验、采用通过评估的源码制品，并观察生产调用、自动回滚。整个闭环不要求人工标注、人工批准或更强的判官模型。生成、归因和业务执行复用一个固定 API 模型。

进化总开关仍默认关闭。每周最多一个新候选，开发检查失败最多修复一次。候选生成、实验、隔离生产请求及影子比较共用每周 20 美元预算；不足时延期或恢复上一版，不自行增加预算。

## 开始使用

从干净、已提交的 Copilot 源码运行，安装仓库的固定依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,mcp,kb]'

export IMPROVE_ENABLED=true
export IMPROVE_EVOLVE_ENABLED=true
export IMPROVE_EVOLVE_SOURCE_DIR="$PWD"
export IMPROVE_LEDGER_DIR=/srv/copilot/improve-ledger
export TRACE_STORE_ROOT=/srv/copilot/traces
# 沿用现有 provider 凭据与一个固定模型，无需设置判官或 performance 模型。
export ECO_MODEL=YOUR_PINNED_API_MODEL
# 可选：明确指定同一个进化模型。
# export IMPROVE_EVOLVE_MODEL=YOUR_PINNED_API_MODEL
# 仅 gold 评估模式（improve_evaluation_mode=gold）需要另钉判官；objective 模式不用判官。
# gold 模式判官可为 api:<model> 或 cli:<cursor|codex|claude|zcode>:<model>；cli:zcode 经生产
# ZCodeTransport 的 tool-less 一次性调用执行（与 kb 质量门同一工具：空 scratch 目录、
# 移除全部原生工具、容器审计、served-model 断言），订阅计费只计判官调用次数，USD 记 0。
# export IMPROVE_JUDGE=cli:zcode:GLM-5.3

infermatrix-copilot improve workflows list
infermatrix-copilot improve workflows prepare --workflow all
infermatrix-copilot improve workflows check --workflow workflow-improve.improve.forensics
infermatrix-copilot improve evolve run --workflow workflow-improve.improve.forensics
infermatrix-copilot improve evolve run --workflow pr-review.agent.review_diff
infermatrix-copilot improve evolve run --workflow kb-intake.draft
infermatrix-copilot improve evolve run --workflow all --repo OWNER/REPO
infermatrix-copilot improve evolve list
infermatrix-copilot improve evolve show CANDIDATE_ID
```

`prepare` 自动导入已有 replay trace，并生成引擎自身的受控故障及无故障对照。业务样本只能来自真实输入，不用模型编造标签。`evolve run` 经完整周期执行这些阶段；重复调用会刷新免费输入采集并继续已有候选，不重复完成的付费调用。`--repo` 只选择指定仓库的业务证据与输入。

`check` 报告固定 API 路由、冻结输入、测试、源码、预算、沙箱和功效样本缺项。CLI 延期退出码为 3，命令错误为 1。未配置固定模型时明确延期。混合模型与 harness 路由尚未接入此代理，不会静默调用其他模型。

当前主机 `max_user_namespaces=0`。恢复 Linux user namespace 与 bubblewrap 隔离前，只能准备数据、查看证据和执行可信测试；生成的代码不会执行，也不会采用。程序不会修改主机内核配置或回退到无沙箱执行。

## 系统如何判断改进

没有独立证据时，模型的自我评价不能证明进步。这里用可信父进程持有的可执行目标代替金标与判官；候选只返回业务产物，不能修改评分、测试、预算、隔离、发布权限或控制器。

| 工作流 | 自动得到的实验输入 | 可证明的收益与保护 |
|---|---|---|
| 引擎归因／lint | 控制器注入输出截断、候选丢弃、规划回退，随机化记录标识与参数；同时保留无故障对照 | 对已知干预正确归因并引用实际证据，或正确检出对应 lint；漏答计错，负例误报计错，既有正例不得丢失。每次只改归因或 lint，避免未评估的混合变更 |
| PR 评审 | 原生步骤冻结 base/head Git 树、diff、上下文、已有发现和知识快照，写入 replay trace | 非空报告，文件／行号／证据契约正确；有效基线上的发现、处置、复查与 verdict 必须保留；比较成本或耗时。不把结构通过率当作真实问题召回率 |
| 知识草稿 | 原生起草冻结事件、证据、知识文件、版本与生成模型 | typed operations 在内存知识树可应用，范围及保护路径正确；已有有效操作不得丢失，空草稿可以正确。不奖励编造规则，不宣称新规则语义正确；实验不写生产知识库 |
| CI debug、rebase、issue 回答等 | 既有 trace 及可信回归测试 | 持续获得 Tier 1 机械检查。已有测试的基线失败／候选通过可证明限定缺陷修复；尚无隔离生产驱动的工作流不能自动采用，不宣称比较质量提升 |

引擎默认生成受控案例，干预见证只在父进程清单中。生成器只能看到开发样本、trace 证据和允许源码；工作进程只收到冻结业务输入，不能访问晋级案例的见证或报告。候选返回的分数被忽略，费用、调用数、耗时、源码与导入路径由可信控制器核验。

默认目标为契约通过率；效率提案使用资源收益。每 item 三次配对，按 item 聚类计算置信区间，提升必须获得 `supported` 且达到预注册最小效果（默认 0.05）。已有契约及输出不得退化。若实际方差使实验功效不足，保留旧实验，用新鲜独立样本注册下一次；不重新评分已消费的留出集，也不重复生成补丁。受控场景可自动补充，真实业务样本须等待 trace。

上述结论只覆盖可执行契约、受控故障和资源收益。没有可验证结果信号时，系统记录限制，不声称任意 PR 召回率或知识语义质量变好。生产知识发布仍沿用宿主已有权限及质量门；进化评分本身不调用该门的模型判官，也不授权候选写知识库。

## 输入、声明与可信边界

默认输入位于 `<ledger>/evolution/inputs/<workflow>/dataset.json`，可用 `IMPROVE_EVOLVE_DATA_DIR` 指定其他目录。每个输入文件、条目元数据和源码制品都有内容指纹。重复业务 item 归为同一聚类；旧 trace 缺少完整输入时不会猜测快照。

PR 重放读取固定 Git 对象，拒绝符号链接、凭据文件、非 UTF-8 或超限文件；知识输入冻结当前生成模型，必须与代理固定模型一致。模型输出与输入都不携带生产凭据。候选在无网络、受限文件系统的沙箱执行，模型请求只能经过宿主代理及共享预算。

工作流声明在 `src/infermatrix_copilot/improve/workflows/*.yaml`。`evolution` 指定可改路径、配置键与可信测试；共享代码变更合并所有受影响工作流的回归检查。可选 `objective` 仅接受 `metric: contract_success|resource_gain`、`min_effect`、`prior_sd`；这类控制策略不在候选允许修改的范围内。

失败候选、修复尝试、补丁及报告保留在账本旁，不进入产品知识库。同一失败补丁不能通过换提案重试。结束的候选自动关闭对应提案；中断的生成不会重发，下周可继续提出新的改动。晋级使用的新鲜留出集记录在 `evolution/holdouts.json`。

## 自动采用、观察与回滚

通过测试及可信实验后，控制器重新应用允许范围内的补丁，核验与实际评估制品相同，然后把它复制为不可变本地 release。`evolution/active.json` 原子记录当前指针、上一版和谱系；不必创建或合并 PR。

Copilot 原生评审、知识起草、周期 lint 与引擎诊断会在隔离进程执行活动制品。宿主仍控制生产写操作。真实执行 trace 确认源码指纹后才记录部署基线；指针激活本身不是部署证明。原始 Git 检出不会被自动改写。

首次试运行对同一冻结输入运行上一版，至少八个不同 item 的有效配对才能标记 `retained`。输出契约失败、已有有效产物变化、制品被篡改、隔离或预算失效，立即恢复确切上一版并阻断本次调用。七天没有足够试运行证据也自动恢复。保留后，每周最多八个新 item 继续配对；统计显著的资源退化触发回滚。无法验证上一版时关闭活动制品，不执行未知源码。

关闭 `IMPROVE_ENABLED` 或 `IMPROVE_EVOLVE_ENABLED` 后，原生流程停止使用进化制品。候选目录 `<ledger>/evolution/candidates/<id>/` 包含补丁、两个源码制品、测试报告、`objective.json`、历次实验、候选状态和 `PR.md` 审计草稿；活动制品在 `evolution/releases/`。续跑、并发与采用操作使用锁和持久化阶段进度，中断的付费调用不自动重发。

## 可选人工评估与 PR 审计

旧金标流程保留供主动选择：`IMPROVE_EVALUATION_MODE=gold`、`IMPROVE_PROMOTION_MODE=pr`。此模式才要求人工标签、策展金标及相应判官。旧 `meta export/annotate` 与 `workflows import-meta` 命令保持兼容；自主模式无需使用。

`--post` 可额外生成 `evolve-outbox/1` 审计动作，仍遵守 `ALLOW_POST`、`ALLOW_PUSH` 和 maintainer 策略；不会绕过 GitHub 仓库发布权限。自主采用不等待这一审计 PR。旧 `improve-outbox/1` 与手动 PR 合并／部署跟踪保留。

## 验证范围

`test/test_autonomous_evolution.py` 验证无人工／无判官的三个驱动闭环、可信评分、受控故障与负例、固定模型、实际制品采用、指纹篡改、自动恢复、观察、预算／隔离阻断和中断续跑。测试使用脚本化模型和工作进程来验证协议与状态机；真实 OS 沙箱不可用时相应测试明确跳过。

当前主机尚未执行真实模型生成代码的生产闭环。上线前必须在具备隔离、真实业务输入及现有预算的主机完成实际运行；脚本化测试不能替代这一证明。
