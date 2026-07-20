---
title: "性能与精度证据"
created: 2026-07-10
updated: 2026-07-20
type: guide
tags: [vllm-omni, benchmark]
sources: ["PR #5052"]
---

# 性能与精度证据

## 4. 性能 / 精度验证必须先定义口径：official e2e 结论不能用 smoke 数据代替

**触发条件**：
- 用户要求“跑精度测试 / 性能收益 / 和官方输入一样 / 贴输出图”。
- 一个功能有多条可运行路径，例如 DiT-only、AR-to-DiT、单请求 accuracy、双请求 grouped batch。
- 想把临时脚本结果写进 PR / issue / final answer。

**强制流程**：
1. 先填 Evidence Matrix，再跑或汇报结果。
2. 跑完后把每行的 result / artifact / metric 补齐。
3. PR / issue / final answer 只能引用矩阵里 `allowed conclusion` 覆盖得到的结论。
4. 没有矩阵的性能 / 精度 / 图片结果，不能进入 PR 主结论。

**Evidence Matrix 模板**：

```markdown
| ID | Purpose | Input Source | Path | Requests | Batch Knobs | Timing Scope | Metrics / Artifacts | Allowed Conclusion |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- |
| E1 | function smoke | temporary prompt | DiT-only | 2 | max_num_seqs=2, diffusion_batch_size=2 | N/A | logs only | variable prompt lengths can be grouped |
| E2 | official accuracy | official fixture | AR-to-DiT | 1 | DiT max_num_seqs=2 | N/A | CLIP/SSIM/PSNR + image | step-wise path preserves official accuracy |
| E3 | official perf | official fixture | AR-to-DiT | 2 | baseline 1/1 vs grouped 2/2 | omni.generate only, model init excluded | elapsed / throughput / GPU stats | official two-request e2e speedup |
```

每行必须包含：
- purpose：功能 smoke / official accuracy / full e2e / performance comparison。
- input source：官方 fixture、用户指定输入，还是临时 prompt。
- path：DiT-only / AR-to-DiT / request-mode / step-wise。
- request count：单请求、双请求、多请求。
- batch knobs：`max_num_seqs`、`diffusion_batch_size`、stage batch size。
- timing scope：是否排除模型初始化。
- metrics / artifacts：指标、图片、日志证据在哪里。
- allowed conclusion：这条结果最多能证明什么。

**PR Test Plan 规范**：
- Test Plan 必须按 Evidence Matrix 的 ID 拆小节。
- Test Result 必须沿用同一组 ID，避免结果和计划错位。
- Smoke 的图片默认不贴；除非用户明确要看 smoke 输出。
- Performance table 只能出现在 official / user-specified input 的 performance row 下。

**PR Test Result 规范**：
- 表格标题必须带输入口径，例如 `Official IT2I performance comparison`，不要只写 `Performance`。
- 精度表必须写 reference，例如 `against tests/e2e/accuracy/assets/hunyuan_image_ref.png`。
- 速度表必须写 `model initialization excluded/included`。
- 如果同一 PR 同时有 smoke 和 official e2e，smoke 放在最后，且标题写 `Compatibility smoke`。

**硬规则**：
1. 先写测试矩阵，再跑或汇报结果。
2. official accuracy / official performance 只能用官方 fixture 或用户指定输入。临时 prompt 只能标为 smoke。
3. 性能对比必须单变量：
   - baseline 与 grouped 使用同一输入、同一请求数、同一 seed / steps / guidance / AR 配置。
   - 只改变目标 batching knobs。
   - elapsed 的计时范围一致。
4. 图片证据必须匹配结论：
   - 质量 / 精度图用 official 或用户指定输入。
   - 功能 smoke 图如果质量差，不贴；用日志证明 grouping 即可。
5. 如果发现结果来源错了，不能用注释补救；必须撤掉旧表，重跑正确口径并替换。

**2026-05-21 HunyuanImage3 DiT grouped batching 反例**：

我先把 DiT-only 英文 prompt 的性能表写成 PR 主性能结论：

```text
DiT-only smoke: 51.118s -> 47.426s, speedup=1.078x
```

用户要求官方提示词后才发现这不是 official IT2I full pipeline 口径。重新用官方 IT2I prompt + Tencent demo input images + 两个 request + 同样 seed/steps/guidance 跑 baseline/grouped，结果变成：

```text
Official IT2I e2e: 188.042s -> 182.690s, speedup=1.029x
```

这两组数据都真实，但能支撑的结论不同。前者只能证明 DiT-only grouped path 在临时 prompt 上能跑且有收益；后者才是官方输入 full IT2I grouped batching 的性能证据。

**正确模板**：

```markdown
### Performance Comparison

Input: <official fixture / user input>
Requests: <N>
Timing scope: `omni.generate(...)` only; model init excluded.
Only changed knobs: <baseline knobs> vs <grouped knobs>.

| Mode | max_num_seqs | diffusion_batch_size | Elapsed | Throughput |
| --- | ---: | ---: | ---: | ---: |
```

**自检问题**：
- 这组数字来自哪个脚本？
- 这组输入是不是用户要求的“官方输入”？
- request 数和 batch knobs 是否与结论一致？
- 这是 DiT-only 还是 full AR-to-DiT？
- 表格标题有没有把 smoke 写成 e2e？

## Benchmark 程序本身也必须验收

性能脚本能打印数字，不等于数字和 PASS/FAIL 判定可信。新增或修改 benchmark 时，
先用小型确定性输入验收测量器，再投入昂贵环境。^[PR #5052]

- **计时边界**：warmup、compile、首次连接和模型初始化必须位于正式 wall-clock 起点
  之前；若目标就是 cold-start，必须单独命名指标，不能混进 steady-state throughput。
- **分位数**：小样本使用 nearest-rank 或成熟统计实现。`int(q*n)-1` 会把两样本 p90
  错算成最小值；测试至少覆盖 1、2 和奇偶样本数。
- **失败语义**：零成功、请求异常或隔离校验失败必须非零退出。打印错误后返回 0 会让
  CI 和外层脚本把坏数据归档成成功结果。
- **隔离证据**：replica/data-parallel 请求使用不同输入和 seed，各自与单副本 baseline
  对齐，并要求完整 key-set equality。相同 prompt/seed/hash 只能证明结果相同，不能
  证明请求没有串线；结果是 baseline 真子集也不能通过。
- **结果完整性**：报告请求总数、成功数、失败数、结果 key 集和统计样本数；任何一项
  与计划矩阵不一致都先失败，不计算漂亮的 percentile。

最小验收应故意注入一次请求失败、一个缺失结果 key、两样本 p90 和一次 timed warmup，
证明脚本分别拒绝前三者并把 warmup 排除在正式窗口外。完整 grouped/replica 语义还要
结合 [dynamic batching validation](dynamic-batching-validation.md) 和
[evidence gate](evidence-gate.md)。
