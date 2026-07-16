# Model Adaptation PR Guardrails

**触发**：新模型、新 pipeline、新 backend、已有模型新增 T2V/I2V/S2V/V2V 等 public path、PR 需要写性能提升、docs/recipe/supported model/perf config 任何一个公开入口发生变化。

**硬规则**：开发前先按 [canonical mini spec](../../../../framework/planning/guides/mini-spec.md) 写最小模板；本页只补模型 / checkpoint / pipeline 适配 appendix。sub-agent review 只能兜底，不能替代开发前 gate。能跑通 unit test 不等于 public entrypoint 可用，不等于 PR body 可以写性能结论。声明 PR clean 前必须跑 full diff review；关闭已知 finding 不等于全量 review 干净。

## 1. Model adaptation mini-spec appendix

先完成 [mini_spec.md](../../../../framework/planning/guides/mini-spec.md) 的 canonical template；涉及新模型 / checkpoint / pipeline 时，再追加这张短矩阵，允许很短，但不能空：

```text
Mini spec
- Goal:
- Checkpoint layout:
  - runnable model id:
  - raw/upstream model id:
  - required files/subfolders:
- Public entrypoints:
  - offline T2V:
  - offline I2V:
  - serving T2V:
  - serving I2V:
  - perf config:
- Request fields:
  - ingress:
  - default semantics:
  - owner:
  - consumers:
  - failure policy:
- Path parity:
  - normal path:
  - variant paths:
  - shared helper or intentional split:
- Validation tiers:
  - unit:
  - public smoke:
  - formal perf:
- PR evidence:
  - latest-head:
  - historical:
  - pending:
- Non-goals:
```

写不出 mini spec，不准开始实现。五行能讲清就写五行；五行讲不清，就说明这不是简单改动。

## 2. Checkpoint layout gate

新模型 public model id 写进 docs/examples/recipes/perf config 前，必须先验证 checkpoint 目录结构。

至少检查：

- `model_index.json`
- pipeline loader 需要的 subfolder configs，例如 `transformer/config.json`、`vae/config.json`、`scheduler/scheduler_config.json`、`tokenizer/`、`text_encoder/`
- 当前 pipeline loader 是否支持 single-file/raw safetensors
- official repo 和 community Diffusers-format repo 是否是同一种布局

规则：

- `supported_models.md`、offline examples、recipes、perf config 只能把**当前 loader 可直接加载**的 checkpoint 写成 runnable model id。
- upstream raw checkpoint 只能写在 References / Notes，不能写进 runnable command 或 default route。
- 从相邻版本继承经验必须重新验证。`LTX-2` official 是 Diffusers layout，不代表 `LTX-2.3` official 也是。

## 3. Public entrypoint matrix

新增或公开某个模型能力时，必须按 public path 列清楚命令和必填字段：

| Path | 必须证明 |
| --- | --- |
| offline T2V | model id、class auto-select、sampling params、output handling |
| offline I2V | image/multimodal key、single/multi image policy、latents path |
| serving T2V | `/v1/videos` 或 `/sync` form fields、model id、required params |
| serving I2V | `input_reference` / `image_reference` 到 `multi_modal_data["image"]` 到 pipeline consumer |
| perf config | workload、model id、mode、runner actually supports it |

docs 里不能把 T2V curl 放在 I2V server command 后面冒充 I2V 验证。I2V recipe 必须带 reference input；如果 live serving smoke 没跑，PR body 必须明确写 pending。

public API bad path 要区分层级：

- endpoint 做了 structured 4xx：可以写 "request is rejected"
- 只有 pipeline 内部 `ValueError`：只能写 "pipeline requires X"，不要暗示 public API 已有 clean rejection

## 4. Request parsing and path parity

新增第二条执行路径时，request parsing 默认不能复制。

常见第二路径：

- T2V vs I2V
- image input vs provided latents
- packed vs unpacked latents
- direct args vs prompt dict / `additional_information`
- offline vs serving
- normal forward vs step/graph/cache path

规则：

- 两条路径解析同一套请求语义时，必须共用 owner helper。
- helper 返回值按 consumer 拆名，不能把用户原始值、scheduler 默认、decode 默认、system prompt 默认混成一个变量。
- 测试必须覆盖非默认字段，不能只测默认 smoke。

precomputed prompt fields 是 all-or-none batch contract：

- `prompt_embeds`
- `negative_prompt_embeds`
- `prompt_attention_mask` / `attention_mask`
- `negative_prompt_attention_mask` / `negative_attention_mask`

只要 batch 里任一 prompt 提供该字段，所有 prompt 都必须提供。否则要 fail fast，并带 missing index；禁止让 `torch.stack([... None ...])` 这类低级错误泄漏出来。

不要用 Python `or` 合并 tensor 字段；tensor truthiness 会晚炸或语义错误。先显式判断 `is None`。

## 5. Validation tiers and PR body wording

PR body 必须把证据分三层，不准混写；细节见 [pr_body_model_evidence](../../git/guides/pr-body-model-evidence.md)、[pr_body_provenance](../../git/guides/pr-body-provenance.md)、[pr_body_privacy](../../git/guides/pr-body-privacy.md)。

```text
Latest-head validation:
- 当前 PR head 的命令、结果、版本

Historical reference:
- 旧 checkout / artifact / benchmark，只能作为背景，必须写 checkout

Pending:
- 需要远端 GPU、model cache、serving smoke、formal perf 的项
```

性能结论只来自 formal sweep。单请求 smoke、endpoint 探索、unit tests、shape-clean 都不能写成 speedup。

公开 PR body / comment 只写 reviewer-facing 可复现证据；本地/远端内部路径、host/user/cache/venv 探针、个人机器 blocker 只进私有验证 artifact，不进公开正文。新模型 PR 里的 `strict load`、stub smoke、real checkpoint validation 必须分层，不能互相冒充。

## 6. Public docs performance numbers

recipes / docs 不能发布没有 provenance 的 latency、VRAM、warmup 秒数。

允许：

- "run latest-head serving smoke or DFX benchmark before publishing latency/VRAM"
- "96GB-class GPU recommended for validation" 这类非测量指导
- 带 commit/env/workload 的历史表，并明确 historical

不允许：

- 从历史笔记搬 `~110s`、`~62GB` 进 public recipe
- PR body 说 formal sweep pending，但 recipe 表格像 validated configurations
- perf config 只覆盖小 workload，却在 docs 写另一个大 workload 的正式结果

## 7. Full diff review gate

新模型适配 PR 通常会同时改 pipeline、测试、recipe、perf config、registry/docs。用户要求全量 review、项目级 review、看有没有废话/重复/垃圾修改，或准备 push/更新 PR body 前，必须先跑 full diff review gate。

先生成 diff 证据：

```powershell
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --numstat origin/main...HEAD
```

然后按新增行数从大到小审：

1. Pipeline / model 文件：每个新增 helper、request parser、default、denoise/step 函数都要追到 T2V forward、I2V forward、offline entrypoint、serving entrypoint、tests。只测 helper 返回值不算 public path 通过。
2. Tests：确认测试覆盖的是公开行为 owner，不只是内部 helper；prompt embeds、latents、image tensor、non-default fps/frame_count/num_outputs 等都要走到 consumer。
3. Recipe/docs/perf config：model id 必须是当前 loader 可加载的 Diffusers layout；workload、frame size/count、mode、compile/eager、性能数字和 config 必须一一对应。

Garbage pass 必须专门查：

- T2V/I2V request parsing 是否复制，后续字段是否会漂移。
- tensor-like 字段是否用了 Python `or` / truthiness fallback。
- docs 是否把 raw/upstream checkpoint 写成 runnable checkpoint。
- perf config 只覆盖小 workload，却在 recipe 里暗示大 workload 已验证。
- unit-only 验证是否被写成 public entrypoint smoke。
- 已修 finding 的同类模式是否横向漏扫。

输出必须写：

```text
DIFF REVIEW BASE: <base>...<head>
TOP FILES REVIEWED: <files>
AUDITS RUN: diff-census, semantic-trace, garbage-pass, reviewer-lens-1..4
```

如果只检查了之前 reviewer/sub-agent 提过的问题，只能写 `known findings closed`，不能写 `full PR reviewed`、`clean` 或 `no remaining P1/P2 for the PR`。

## 8. Interactive reviewer loop

普通 "review 一下" sub-agent 容易直接给结论，不能逼出不明白的问题。复杂模型适配需要 loop protocol。

使用这个协议：

```text
You are a fresh low-context interactive reviewer.
Do not finish in one pass.

Hard protocol:
1. First response MUST be `QUESTIONS ROUND 1`.
2. Ask 3-6 concrete questions. Each question includes:
   - file:line evidence
   - what you do not understand
   - what answer would change your review result
3. Stop after questions and wait.
4. After answers, validate against code, then either:
   - ask `QUESTIONS ROUND N`, or
   - say `READY_FOR_FINDINGS`
5. Do not output final findings until main agent sends `FINALIZE_REVIEW`.
6. Final output is P0/P1/P2 findings or no blocking findings plus residual risks.
```

主 agent 操作规则：

- 不要长等到 completed 后才看。短轮询，看到 QUESTIONS 就答。
- 答案不能只解释设计，要给它可验证的 file/line/command。
- 对它指出的 "没有证据" 默认当真，先补证据或改 wording。
- 它说 `READY_FOR_FINDINGS` 后再发 `FINALIZE_REVIEW`。

## 9. Pre-push checklist

新模型适配 PR push 前必须逐项打勾：

- [ ] mini spec 写过
- [ ] runnable checkpoint layout 已验证
- [ ] official raw vs Diffusers-format checkpoint 已区分
- [ ] supported model / examples / recipes / perf config 的 model id 一致且可加载
- [ ] T2V/I2V public commands 都有正确必填字段
- [ ] request parsing 共享 helper 或明确 intentional split
- [ ] batched optional tensor fields all-or-none fail-fast
- [ ] non-default field tests 覆盖 fps/frame_rate、num_outputs_per_prompt、prompt dict fallback、latents/image path、decode fields
- [ ] PR body 分 latest-head / historical / pending
- [ ] public docs 没有无 provenance latency/VRAM 数字
- [ ] full diff review gate 跑过，并区分 known findings closed vs full PR reviewed
- [ ] 至少跑过 module owner + omni project owner review
- [ ] 对复杂 PR 跑过 interactive reviewer loop
