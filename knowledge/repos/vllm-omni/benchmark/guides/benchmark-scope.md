# vLLM-Omni Benchmark 口径

## 5. Benchmark 必须先定口径：探索 / smoke / sweep 三段不能混跑

**2026-06-01 HunyuanImage3 AR benchmark 反例**：目标是比较 latest main 与 PR #3938 fused rotary 对 HunyuanImage3 AR 的性能影响。#3767 的 benchmark overlay 可以作为测量工具，但被测版本应该是：

- baseline：`origin/main` + #3767 最小 metrics overlay
- candidate：`origin/main` + PR #3938 commits + 同一份 metrics overlay

用户随后明确“去掉 DiT”，这时 benchmark 口径已经从 full `/v1/images/edits` pipeline 变成 AR-only。正确结论只能来自 AR-only 路径，例如 `/v1/chat/completions` streaming 或 offline AR engine；不能继续用 `/v1/images/edits`，因为这个 endpoint 在当前实现里需要 diffusion stage，AR-only deploy 下会在进入目标模型前失败。

这一轮的问题不是单个参数，而是没有把三种阶段分开：

| 阶段 | 目的 | 允许结论 | 禁止行为 |
| --- | --- | --- | --- |
| Endpoint / CLI 探索 | 找到当前代码支持的参数、endpoint、request schema | “这条路径可启动 / 不可启动，原因是 X” | 生成性能数据 |
| 单请求 smoke | 确认请求进入目标路径并返回第一个 streaming chunk / final output | “AR-only online serving 可用，TTFC/TPOT parser 可采样” | 跑 concurrency sweep |
| 正式 benchmark sweep | 对同一 workload 跑 main vs candidate | “在此口径下 mean/p95/p99 和 speedup 是 X” | 中途改 endpoint、prompt、image、seed、template |

### Benchmark 口径矩阵

任何性能报告前先填这张矩阵；没填或没跑完对应阶段，不准出性能表：

```markdown
| ID | Purpose | Version | Path | Endpoint / API | Input Source | Requests | Concurrency | Metrics | Allowed Conclusion |
| --- | --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| S0 | startup smoke | main | AR-only | /v1/chat/completions | fixed prompt + fixed image | 1 | 1 | health + first chunk | serving path usable |
| B1 | perf sweep | main/pr3938 | AR-only | /v1/chat/completions | same fixed prompt + image | 10/16 | 1,2,4 | TTFC/TPOT/e2e | AR-only online serving speedup |
```

必填约束：

- Path 必须写清 `AR-only` / `DiT-only` / `full AR+DiT`。
- Endpoint 必须和 Path 匹配。AR-only 不用 `/v1/images/edits`；full image editing 才用 `/v1/images/edits`。
- 如果没有 dataset，只能写固定 prompt + 固定 image 的 microbenchmark，不能叫 dataset benchmark。
- 如果只跑 smoke，结果只能叫 smoke，不写 speedup。
- 如果模型服务没 health、server PID 已退出、或第一条 request 没有目标 chunk，不能进入 sweep。

### AR-only HunyuanImage3 口径

AR-only 的主要指标是：

- `TTFC`：client POST 到首个 streamed text/content delta。
- `TPOT`：相邻 streamed token/chunk 的平均间隔，必须写明是 client-side chunk 口径还是 server-side token 口径。
- `e2e latency`：请求完整结束耗时，只用于辅助判断。
- 如果 endpoint 是 chat completions，`stage_0_gen_ms` 只有在服务端真实输出该字段时才能报告；没有就不要用 client 口径冒充。

固定输入推荐写明：

- prompt 来源：用户指定 / 官方 demo / 自定义 smoke。
- image 来源：本地文件路径或官方 demo URL，记录 hash/size。
- generation params：`temperature`、`top_p`、`top_k`、`max_tokens`、stop token、bot_task / template。
- deploy：GPU mapping、TP、`max_num_seqs`、venv、checkpoint snapshot。

### 一句话规则

Benchmark 不是“脚本跑起来就开始计时”。先证明 endpoint 和参数属于当前目标路径，再用一个请求证明 parser 能采到目标指标，最后才跑 sweep；任一阶段失败，报告失败原因，不许把失败等待时间或前置 4xx/argparse 错误包装成性能结果。

### Full IT2I benchmark 后必须区分“跑通”和“指标采到”

**2026-06-01 HunyuanImage3 PR #3938 full it2i benchmark 反例 / 修正**：用户最后明确要求 4 卡空闲直接跑 full it2i benchmark。正确执行方式是回到 full `/v1/images/edits` pipeline，使用同一模型 snapshot、同一 prompt/image 生成策略、同一 `origin/main + #3767 overlay` 与 `origin/main + PR #3938 + #3767 overlay`，并跑 concurrency `1,2,4`。

这轮最终跑通并保存了结果：

```text
out_dir=<REMOTE_WORK_ROOT>/hy3_ar_bench_20260601_it2i_full
main=1fa8efde445c64e3a3b5256231f0e08703490853
pr3938=8ca9e072f3784d4c6244cb32982d4e1a7bccc4bb
endpoint=/v1/images/edits
task=it2i
num_prompts=10
warmup=1
steps=8
concurrency=1,2,4
deploy_connector=shared_memory_connector
```

但这次又暴露了两个容易把结果说错的点：

1. **默认 deploy connector 是口径变量**：`hunyuan_image_3_moe.yaml` 默认 `rdma_connector` / `MooncakeTransferEngineConnector`，这台 venv/机器没有 Mooncake，full pipeline 在 DiT KV receive 阶段报 `Mooncake not available`。改用同 YAML 中已有的 `shared_memory_connector` 后可以跑通。这个改动没有改 repo，但必须写进 benchmark 口径；否则别人会误以为结果代表默认 RDMA/Mooncake 配置。
2. **`--stream-ar` 不等于采到 AR TTFC/TPOT**：最终 JSON 里所有 run 都是 `ttfc_count=0`、`tpot_count=0`，即 endpoint 没有吐 `ar_delta` 计时 chunk。可以报告 `stage_0_gen_ms`，不能报告 AR TTFC / AR TPOT。

这轮可引用的结论只能是：

- full it2i 在 shared-memory connector 口径下，main 与 PR #3938 都 10/10 成功。
- `stage_0_gen_ms` 是主要 AR-stage server-side 指标。
- PR #3938 在 c1 基本持平，但 c2/c4 回退；不能说有稳定性能提升。
- AR TTFC / TPOT unavailable，原因是 `ttfc_count=0` / `tpot_count=0`。

**新增 availability gate**：

| 指标 | 必须满足 | 不满足时怎么写 |
| --- | --- | --- |
| AR TTFC | `ttfc_count > 0` 或逐条 SSE 出现 `ar_delta` 首包时间 | `unavailable: no ar_delta chunks` |
| AR TPOT | `tpot_count > 0` 且 final chunk 有 token/time metrics | `unavailable: no AR token timing` |
| stage_0_gen_ms | JSON 中 `stage_0_gen_ms_count == completed_requests` | 只报告部分样本，不能算全量 p95/p99 |
| full pipeline result | `completed_requests == num_prompts` 且 `failed_requests == 0` | 先归类失败，不能写 speedup |
| connector 口径 | main/candidate 使用同一 connector/deploy patch | connector 不同则结果不可比 |

**报告模板**：

```markdown
Config caveat:
- Connector: <rdma/mooncake/shared_memory>; if patched, say "temporary deploy patch applied equally to both versions".
- Streaming metrics: `ttfc_count=<n>`, `tpot_count=<n>`; if zero, TTFC/TPOT unavailable.
- Dataset: random / fixed prompt+image / official fixture; do not call random synthetic prompts an official dataset.
```

**一句话规则**：benchmark 跑通只说明 workload 可完成；每个指标还要独立证明采样存在。`--stream-ar` 是请求参数，不是 TTFC/TPOT 证据；connector patch 是实验条件，不是实现细节。

### Benchmark scope lock：测量补丁不是被测 PR，禁止自造 candidate

**2026-06-02 HunyuanImage3 AR benchmark 反例 / 修正**：用户原始需求是“跑远程 main 版本的 HunyuanImage3 AR 部分性能极限，然后用 benchmark PR #3767”。这里的正确解释是：

- 被测版本：远程最新 `origin/main`
- 测量补丁：PR #3767 的最小 benchmark / streaming metrics overlay
- 被测路径：HunyuanImage3 AR-only
- 有效指标：AR 阶段耗时 / 吞吐 / 必要时 operator topN；full it2i 指标只能作为 full pipeline 结果，不能回填成 AR 极限

错误路线是把“相关 PR”脑补成 PR #3938 fused rotary 性能候选，随后做出 `main vs pr3938` full it2i 表。这张表即使数据来自真实 JSON，也不回答用户原始问题，因为 PR #3938 从未被用户指定为本轮被测对象，full `/v1/images/edits` 也不是“去掉 DiT”后的 AR-only 口径。

开跑前必须写 scope lock 四元组；没有这四行，不准启动 benchmark：

```markdown
Benchmark Scope Lock
- Version under test: <origin/main | explicit candidate>
- Measurement patch/tooling: <PR #3767 overlay | none | other>
- Execution path: <AR-only | DiT-only | full AR+DiT>
- Valid metrics: <stage_0_gen_ms | TTFC | TPOT | op topN | e2e>
```

### 允许加入 candidate PR 的条件

candidate PR 只能来自三种来源：

1. 用户明确说“对比 PR #xxxx”。
2. 已确认 plan 明确列出 “baseline / candidate”，且用户没有后续改 scope。
3. 用户问“找相关性能 PR”，并要求先调研候选；调研结论必须先返回，不得直接把候选加入 benchmark。

禁止来源：

- PR 标题看起来像性能优化。
- 之前上下文里出现过某个 PR。
- benchmark 脚本或 overlay PR 中提到某个模型/指标。
- “为了让表格完整”补一个 candidate。

### 用户改 scope 后旧 plan 失效

用户说“去掉 DiT”时，旧 full pipeline plan 立即失效；用户说“跑 main 版本”时，旧 `main vs candidate` comparison 立即失效。此时必须重新写四元组，并把旧结果标记为 `invalid for current request`，不能继续沿旧 endpoint / old candidate / old metric 表达。

### 结果命名规则

输出目录、summary 标题、表格列名必须反映真实 scope：

- `main_plus_3767_aronly_tp4`：main + #3767 overlay，AR-only TP4。
- `main_pr3938_full_it2i_shared_memory`：main vs PR3938，full it2i，shared-memory connector。
- 禁止把第二种结果简称成 “AR 极限”。

**一句话规则**：benchmark PR 是尺子，不是自动成为被测对象；candidate PR 是用户需求，不是 agent 推断。先锁四元组，再启动任何远端长跑。
