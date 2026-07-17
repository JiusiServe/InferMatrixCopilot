# vLLM-Omni PR Review Pilot Benchmark Seed v0.1

状态：`PROVISIONAL_BENCHMARK_SEED`


> **Promotion update (2026-07-17):** A loadable frozen Dev pilot now exists at
> `eval/data/pr_review/benchmarks/pr-review-pilot-v0.1.0-dev/`. PR #3094 was promoted from this seed;
> the remaining original seed PRs stay provisional. The frozen pilot also migrates PRs #4810, #4834,
> #4816 and #4825 from `eval/legacy/dataset/`.

这不是可直接用于正式排名的冻结 Benchmark，而是依据公开 GitHub PR、Review comment、Review 前后 commit 证据构建的 Pilot 候选数据包。

当前已完成：

- 筛选 5 个 Buggy PR 候选；
- 提取 9 个候选 GT Finding；
- 记录 Review 前 head commit（3 个为完整 SHA，2 个为 GitHub 页面给出的 review commit/短 SHA）；
- 记录历史 Review、问题位置、后续修复线索；
- 给出初始 Severity、Category、merge-blocking 建议；
- 明确每一项距离正式冻结还缺少的步骤。

正式冻结前必须补齐：

1. 通过 GitHub API/Git 仓库解析每项精确 `base_sha`；
2. 校验完整 `head_sha`，并生成完整 PR diff、base/head 只读快照；
3. 使用 3 个独立 Judge 配置 × 2 次位置交换执行 GT Validity Jury；
4. 对分歧项执行第二轮增强 Jury；
5. 完成 GT 去重、accepted locations 和证据范围冻结；
6. 至少加入 2 个经过三 Reviewer Agent + Clean Certification Jury 的 Auto-certified Clean PR；
7. 生成符合 `eval.pr_review.benchmark.schema` 的正式 item、manifest hash 和 Benchmark 版本。

因此，本数据包适合作为 `benchmark build` 的输入种子和人工不可参与条件下的自动 Jury 候选队列，不应直接用于给 Agent 计分。



候选 PR

| PR    | 候选 GT | 主要问题                                                     |
| ----- | ------- | ------------------------------------------------------------ |
| #3094 | 2       | 默认编码从 PNG 意外变成 JPEG；`size=None` 导致响应模型校验失败 |
| #2360 | 1       | 只检查最后一维，可能把二维 RoPE 张量传给要求展开形状的算子   |
| #1720 | 2       | 非 TTS 路径引用未初始化的 `ph_len`；依赖 Prometheus 私有属性 |
| #3100 | 3       | argparse 语法错误；写入不可写模型路径；不安全的 `torch.load` |
| #3053 | 2       | 重复方法覆盖导致初始化 `TypeError`；MXFP4 helper 参数兼容问题 |
