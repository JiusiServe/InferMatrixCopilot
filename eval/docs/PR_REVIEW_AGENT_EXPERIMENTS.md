# PR Review 三组 Agent 对照实验运行说明

## 1. 当前结论

PR Review Benchmark、只读 Snapshot、Agent 输出契约、裁决、指标和报告代码已经存在，但原代码只有一个最小的 `AgentAdapter` 协议和 `module:object` 插件入口，没有可以直接代表待测对象的实现。

本次补齐后，可以直接运行以下三组候选 Review：

| 实验组 | 实际执行路径 | 外部 `vllm-omni-review` Skill |
|---|---|---|
| Copilot | 真实 `agent.review_diff` Step | 不注入 |
| Copilot + Skill | 真实 `agent.review_diff` Step | 作为额外 Review Guidance 注入 |
| Skill Only | 通用 LLM Tool Loop | 作为唯一任务 Skill 注入 |

这里的“Copilot 自身”保留当前 Copilot 的 Repo Profile、内置 Skills、Knowledge、Adaptive Review Depth 和 Ensemble；“Skill Only”不使用这些 Copilot 能力。

## 2. 公平性约束

三组实验共享：

- 相同 Benchmark Item 和固定 `base_sha` / `head_sha`；
- 相同 PR 标题、描述、commit、changed files 和 frozen diff；
- 相同模型；
- 相同只读工具：`read_file`、`list_dir`、`grep`、`git_readonly`；
- 相同严格输出格式；
- 相同 Judge 和 Rubric。

评测期间不会使用实时 GitHub 状态、网络、测试执行、GPU 或发评论能力。Copilot 的线上 GitHub 工具只在评测调用中被替换，正常产品运行不受影响。

## 3. 外部 Skill 冻结

实际仓库路径为：

```text
skills/vllm-omni-review/SKILL.md
```

评测资源固定在：

```text
eval/resources/skills/vllm-omni-review/
├── SKILL.md
└── SOURCE.yaml
```

冻结版本：

- Repository：`hsliuustc0106/vllm-omni-skills`
- Commit：`a66fe5bd7fb753ee566fc9133d02cbb6b40521ad`
- Git blob：`c7820bb3afdc54dd2bef8b972022fbd72c19ae42`
- SHA-256：`f985a1383bbff2e6ce46c77c28017e05887dd2acc2dfce5e94df1af3e4b19469`

本轮实验严格按“仅使用根 `SKILL.md`”处理，不额外注入其 `references/` 文件。

## 4. 运行前提

```bash
python -m pip install -e '.[dev]'
export ANTHROPIC_API_KEY=...
# 使用兼容端点时设置：
export ANTHROPIC_BASE_URL=...
```

还需要一个本地 `vllm-project/vllm-omni` Git 仓库，其中包含 Benchmark 固定的所有 commit。评测过程不联网拉取 commit。

## 5. Smoke 实验

每组运行一次：

```bash
python eval/scripts/pr_review/run_three_arms.py \
  --repository-source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review
```

只运行一个 Benchmark Item：

```bash
python eval/scripts/pr_review/run_three_arms.py \
  --repository-source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review \
  --benchmark-id pr-review-vllm-omni-3094
```

## 6. Formal 实验

每组独立运行三次：

```bash
python eval/scripts/pr_review/run_three_arms.py \
  --formal \
  --repository-source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review-formal
```

## 7. 完整测评与 Judge

不提供 Judge 时，脚本只完成 Candidate Review 生成和资源记录。这可以检查原始输出，但不能得到完整的 Valid Finding Precision、Finding Matching 和最终 Recall。

提供独立 Judge 插件后，脚本会继续执行三组统一裁决和评分：

```bash
python eval/scripts/pr_review/run_three_arms.py \
  --formal \
  --repository-source /path/to/vllm-omni \
  --repository-cache ~/.cache/omni-copilot/repos \
  --output runs/pr-review-formal \
  --judge my_eval_plugins:judge_a \
  --judge my_eval_plugins:judge_b \
  --judge my_eval_plugins:judge_c
```

评分阶段把所有实验组和重复运行放进同一个 Campaign。任何实验组在 Auto-certified Clean PR 上发现经 Judge 确认的 `VALID_NEW` 问题时，该 PR 会对所有实验组统一失效，避免比较偏差。

## 8. 尚未内置的外部能力

- 实际模型凭据和兼容端点；
- 独立 JudgeBackend 的模型配置；
- OS / Container 级网络隔离；
- 包含 Benchmark commit 的本地 vLLM-Omni 仓库。

这些属于部署与凭据边界，不应在仓库内硬编码。
