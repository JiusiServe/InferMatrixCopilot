# 用自进化引擎改进 Copilot 工作流

引擎根据 trace 中的损失提出一个机制假设，生成允许范围内的源码或配置补丁，再用冻结输入比较两个独立源码制品。通过可信回归检查和预注册评估后，它准备 PR 草稿，由人类评审和合并。相同机制用于 PR 评审、知识摄取及引擎自身。

默认关闭进化。每周最多生成一个候选，开发检查失败最多修复一次；所有工作流共用既有每周 20 美元预算。预算、样本或隔离不足会延期，CLI 退出码为 3；输入损坏等命令错误退出码为 1。不会自动提高预算。

## 开始使用

先从干净、已提交的 Copilot 源码检出运行。建议在该检出中创建专用环境，安装源码与仓库声明的可选依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,mcp,kb]'
```

源码制品只包含 `src`、`playbooks`、`adapters`、`skills`，不包含产品知识库、评估标签或账本。使用当前 Python 环境的固定依赖版本；依赖指纹变化会拒绝执行。

```bash
export IMPROVE_ENABLED=true
export IMPROVE_EVOLVE_ENABLED=true
export IMPROVE_EVOLVE_SOURCE_DIR="$PWD"
export IMPROVE_EVOLVE_DATA_DIR=/srv/copilot/evolution-data
export IMPROVE_LEDGER_DIR=/srv/copilot/improve-ledger
export TRACE_STORE_ROOT=/srv/copilot/traces
# 复用现有 provider 配置，显式固定两条 API 路由；比较实验还需固定判官。
export ECO_MODEL=YOUR_PINNED_GENERATOR_MODEL
export PERFORMANCE_MODEL=YOUR_PINNED_INVESTIGATOR_MODEL
export IMPROVE_JUDGE=api:YOUR_PINNED_JUDGE_MODEL

infermatrix-copilot improve workflows list
infermatrix-copilot improve workflows check --workflow pr-review.agent.review_diff
infermatrix-copilot improve evolve run --workflow pr-review.agent.review_diff
infermatrix-copilot improve evolve run --workflow kb-intake.draft
infermatrix-copilot improve evolve run --workflow workflow-improve.improve.forensics
infermatrix-copilot improve evolve run --workflow all --repo OWNER/REPO
infermatrix-copilot improve evolve list
infermatrix-copilot improve evolve show CANDIDATE_ID
```

`workflows check` 报告 trace、完整指纹、开发输入、新鲜留出样本、人工标注／策展金标、可信测试、成本估计及沙箱缺项。已具备结果适配器的工作流也可通过 `mechanical_readiness` 独立检查机械修复资格，不需要质量留出集。产生 trace 的未声明工作流仍被周度 lint 检查；比较质量需要额外接入契约。

本机 `max_user_namespaces=0`，因此检查会报告 `sandbox-unavailable`。隔离依赖 Linux user namespace 与 bubblewrap；恢复主机隔离能力后须重新检查。程序不会修改内核配置，不会回退到无沙箱执行。

## 冻结实验输入

每个工作流使用 `<IMPROVE_EVOLVE_DATA_DIR>/<workflow>/dataset.json`，输入 JSON 为该目录下的相对路径。输入文件的 SHA-256 和完整条目元数据共同形成快照版本。

```json
{
  "workflow": "kb-intake.draft",
  "items": [
    {
      "item": "OWNER/REPO#123",
      "split": "development",
      "input": "event-123.json",
      "sha256": "INPUT_FILE_SHA256"
    },
    {
      "item": "OWNER/REPO#124",
      "split": "holdout",
      "input": "event-124.json",
      "sha256": "INPUT_FILE_SHA256",
      "gold": {
        "entries": [{"gold_id": "rule-1", "path": "repos/demo/core/rules.md", "concern": "人工核实的完整规则契约"}]
      }
    }
  ]
}
```

输入不得携带 `labels`、`gold`、`scores`、`judgments` 或 `report` 字段。可信父进程持有留出标签和金标，只向隔离工作进程传入业务输入。生成器只看到开发样本、损失证据和允许修改的源码。晋级留出集被使用后记录到 `evolution/holdouts.json`，下一候选必须使用新样本；修改标签或输入会使已注册实验失效。

| 工作流 | 输入 JSON 内容 | 父进程验证 |
|---|---|---|
| PR 评审 | `repo`、`pr`、原始 `base_sha/head_sha`、完整 `base_files/head_files`、`diff`、`context_text`、`gate_report`、`knowledge_files` | 在临时仓库重建固定两个树，执行实际评审步骤；盲配对判官计算召回与精确率。原始 SHA 是快照身份，重建仓库的提交 SHA 用于本地源码工具 |
| 知识摄取 | `repo`、`repo_dir`、`event_id`、`generator_model`、`evidence`、`files` 知识快照、`release`、`today`、可选 `external_texts` | 工作进程仅起草 typed operations；父进程在内存树运行生产知识操作与质量门，金标覆盖只计通过的规则，不写生产知识库；`generator_model` 必须与可信 API 代理的 eco 模型一致 |
| 引擎归因 | `records`、`blobs`（引用到文本映射）、`concerns`、`cells` | 条目另存 `labels` 与 `label_source: human`；完整人工标注分母，缺失、弃答、分歧和无效证据均记错 |

在预注册前按 item 的固定排序选择达到功效要求的新鲜样本，避免把整个留出池都计入一周预算。每 item 固定三次成对运行；只有三对完整的 item 进入聚类统计。主要指标必须 `supported` 且达到最小效果；精确率、有效规则覆盖及无效规则数的显著退化会阻止晋级。成本也有保护指标。评分不采信工作进程返回的数字。隔离、源码或导入路径核验失败使实验无效。

默认最小效果为 0.05。功效计算可能要求几十个新鲜 item；在缺少历史成本时，保守估计可能超过 20 美元。应先收集真实调用成本并补齐样本，不能通过降低可信保护或自行提高预算跳过检查。声明可提供由维护者核实的 `cost_per_unit_usd` 估计，实际请求始终受共享预算限制。

## 历史 trace 与人工标注

当前仓库的元基准目录没有已提交的真实案例。工具不会生成或猜测人工标签。先人工策展真实 item 的金标，再导出完整历史单元：

```bash
infermatrix-copilot improve meta export --case incident-001 \
  --unit-id HISTORICAL_UNIT_ID --gold-file /srv/curated/item.gold.json \
  --meta-dir /srv/copilot/human-meta --trace-root /srv/copilot/traces

# 人工检查 trace 后写 labels.json，例如 {"gold-id": "S2"}；阶段定义见 forensics.STAGES。
infermatrix-copilot improve meta annotate --case incident-001 \
  --labels-file /srv/curated/labels.json --human-verified --split holdout \
  --meta-dir /srv/copilot/human-meta

export IMPROVE_META_DIR=/srv/copilot/human-meta
infermatrix-copilot improve workflows import-meta --data-dir /srv/copilot/evolution-data
```

开发集与留出集须由人工分别安排。未指定 split 的旧案例默认进入开发集；空标注不满足晋级条件。知识摄取及 PR 的输入 JSON 也需由维护者从固定事件、源码和知识快照导入，金标只写在父进程清单中。

## 工作流声明与机械修复

扩展声明位于 `src/infermatrix_copilot/improve/workflows/*.yaml`，保留既有工作单元、item、fingerprint、capture 与 outcome_adapter，新增 `experiment_driver` 和 `evolution`：允许的 `paths/settings`、可信 `tests`、主要 `metric/direction/min_effect`、保护 `guards`、共享源码 `dependencies`。候选改动共享运行时后，受影响工作流的测试合并执行并记在候选中。

首版 API 代理接受固定 eco/performance 两条模型路由；使用混合成员、harness lens 或其他专用评审模型的配置会报告代理驱动缺项，不能静默改成默认路由。并发评审请求经代理串行预算结算。

当前可信驱动为 `pr-review`、`kb-intake`、`meta` 和 `mechanical`。新增比较驱动需要维护者实现并审查父进程的快照、预测和评分契约，再通过声明选择；未知驱动不会回退成 PR 评审。

CI debug、rebase 和 issue 回答已声明机械改动范围。无结果适配器时，在 dataset.json 额外提供 `reproducer`（Python 测试文件相对路径）及 `reproducer_sha256`。该可信复现测试必须在基线返回 pytest 失败码 1，在候选返回 0，且工作流回归检查通过。产物明确写 `quality_claim: false`。CI debug 和 rebase 首版不运行比较质量驱动，不在生产仓库执行修改或推送。

评分、基准、预算、隔离、发布、控制器及权限源码受保护。引擎自身只能改归因、lint 和声明允许的模型配置。失败候选、每次尝试的补丁、源码制品和测试报告会保留。同一失败提案不再次自动生成；同一基线上的已失败补丁也不会以新提案重复执行。

## 周期续跑、发布和上线观察

`improve cycle`、`workflow-improve` playbook 和 `kb serve` 周度槽位共用协调器：lint → 已注册实验 → 取证 → 候选生成／验证／实验 → 草稿。阶段及每一对实验均落盘；重启跳过完成阶段，中断的付费调用不自动重发。每周最多一个新候选；有待评审候选的工作流直接返回已有候选。

候选目录在 `<ledger>/evolution/candidates/<id>/`，含 `candidate.json`、`incumbent/`、`arm/`、`candidate.patch`、`PR.md`、`bundle.json`；配对进度、判定、源码／依赖哈希、测试报告、失败原因和谱系都可检查。

请求发布：

```bash
export ALLOW_POST=true
export ALLOW_PUSH=true
export IMPROVE_PROPOSAL_REPO=OWNER/InferMatrixCopilot
export IMPROVE_EVOLVE_OUTBOX_DIR=/srv/copilot/evolution-outbox
infermatrix-copilot improve evolve run --workflow pr-review.agent.review_diff --post

# omni-maintainer，使用与候选基线相同且可信的源码仓库
omni-maintainer evolve --outbox /srv/copilot/evolution-outbox \
  --source /srv/repos/InferMatrixCopilot
```

新协议为 `evolve-outbox/1`，既有 `improve-outbox/1` 提案协议保留。maintainer 默认 `phase.evolution_prs_live=false`；只有维护者按仓库策略开启后才推送并创建草稿 PR。它核验实际补丁对应的源码树，拒绝过期主分支、受保护文件和哈希不符，重试复用同一候选分支／PR。进化 PR 禁止 arbiter 自主晋级，仍需人类 go。

PR 合并只标记 `merged`。生产 trace 出现候选源码树 SHA，且采用配置与指纹清单一致后，才标记 `deployed` 并记录账本部署基线。下一周期读取生产样本及已有可信结果；不足八个共同 item 或缺少结果时报告等待，不宣称上线收益。有显著退化则生成回滚建议，由人类决定执行。

## 验证范围

`test/test_evolution.py` 包括三个驱动的离线闭环（脚本化模型／工作进程）、可信 PR 与知识评分、完整归因分母、受保护改动、指纹造假、续跑、并发去重、预算拒绝、一次修复、机械复现及合并未部署。真实 OS 沙箱测试在主机不可用时明确 skip。maintainer 测试覆盖补丁实际应用、哈希、过期基线和发布去重。

离线闭环能检验协议与状态机；真实模型、真实人工基准及隔离执行的三个端到端验收，仍须在具备沙箱和评估数据的主机完成。
