# vLLM-Omni 硬门禁

只在当前任务明确属于 `vllm-project/vllm-omni` 时应用本页。先遵守根目录 `CLAUDE.md` 的通用 P0，再执行这里的仓库专属门禁。其他仓库不得继承本页的模型、远端、测试、PR 或身份假设。

## 1. 开工

1. 确认真实 vLLM-Omni checkout、分支和目标 worktree。主基准 checkout 默认只读，业务修改使用专用 worktree。
2. 写代码前读 [code taste](../../framework/review/guides/code-taste.md)。
3. 新模型、新 pipeline、新 public entrypoint 或性能 claim 先读 [mini spec](../../framework/planning/guides/mini-spec.md)；涉及模型或 checkpoint 再读 [model adaptation guardrails](review/guides/model-adaptation-guardrails.md)。
4. bug、crash 或行为异常先检查下面的场景触发器；直接匹配时按链接进入 owner。没有直接匹配时才进入 [vLLM-Omni 调试入口](debug/_index.md)，再通过仓库主题、`components/_index.md` 或 `models/_index.md` 确认 owner；不能停在通用规则，也不能先猜 incident 路径。
5. benchmark、profiling、GPU、serving 或远端验证先读 [benchmark 入口](benchmark/_index.md) 和 [远端入口](remote/_index.md)。只有规则明确提示、出现高度相似错误或用户要求历史复盘时才查错题。
6. 当前机器地址、worktree、venv、cache、容器和账号只从 ignored `local/` 获取，并用本轮 live 命令验证。

## 2. 场景触发器

| 用户提到 | 必读 | 硬约束 |
|---|---|---|
| profiling、trace、Perfetto、Nsight、算子或时序 | [profiling 状态机](benchmark/guides/ar-graph-profiling.md) 和 [benchmark incidents](benchmark/incidents/_index.md) | 默认交付 trace artifact 和质量摘要；benchmark stats 不能冒充 trace |
| graph mode、`enforce_eager=false` | 同上 | trace、目标请求和 server 日志必须证明来自同一轮 graph run |
| e2e、QPS、latency 或性能对比 | [benchmark scope](benchmark/guides/benchmark-scope.md) 和 [evidence gate](benchmark/guides/evidence-gate.md) | 先固定完整 metric contract，再跑正式 sweep |
| config、deploy、pipeline 或 CLI cleanup | [配置审计](dev/guides/config-audit-plain-language.md) | 沿入口、默认值、多层加工和新老路径查所有权 |
| stage config、并行度、设备映射或 worker 启动 | [Model Executor 规则](components/model-executor/rules.md) | 展开最终配置，并在 worker 前验证并行 world size 和可见设备 |
| runner `_preprocess` 生产的逐请求 phase metadata，例如 `_omni_prompt_len`、`_omni_num_computed_tokens`、`_omni_is_prefill`，或由它们决定的 preprocess/MTP 路由 | [Model Executor 规则](components/model-executor/rules.md#runner-到模型的预处理合同) | 先查共享 worker runner 的 producer 和路由，再查具体模型 consumer |
| 模型适配、checkpoint 或 HF 对齐 | [model guardrails](review/guides/model-adaptation-guardrails.md) 和对应模型入口 | plumbing 绿灯不等于语义正确 |
| PR review 或 reviewer follow-up | [review 入口](review/_index.md) 和 [Git/PR 入口](git/_index.md) | 绑定当前 head、diff、live review thread 和真实代码路径 |

## 3. 代码和模型

- Algorithm 决策前先查 upstream 主入口，包括 `modeling_*`、`generation_*`、tokenizer、scheduler、denoising loop、special token、attention mask 和 KV 路径。
- Crash 或 `AttributeError` 不是停止点；必须追到错误类型为什么进入当前路径。
- 仓库场景触发器未直接命中 owner 时，仓库专有 bug 必须完成第二次路由：从 [debug 入口](debug/_index.md) 进入仓库主题，再通过 [组件职责地图](components/_index.md) 或 [模型列表](models/_index.md) 找真实 owner。owner 已有 `rules.md` 时必须读取；没有时以 live 源码为准，复盘确认规则具有复用价值后再补，不为单次 issue 预建目录。
- 新模型的 `0 missing / 0 unexpected`、shape smoke、无 NaN/Inf 和 mock 权重只证明 plumbing；必须补 semantic parity matrix。
- L2 只覆盖 CPU/mock 功能且不能触发真实 stage、device 或 GPU 初始化；真实权重、精度、性能和 profiling 属于 L4。
- 新参数必须有单一 owner、公开 contract 和对应测试；禁止用 `dict.get(...) or fallback`、`hasattr`、随手 `getattr(default)` 或 `generator=None` 掩盖新旧路径不一致。
- 用户可见的 API、CLI、日志、文档或输出变更，必须按 [用户可见验收](../../framework/docs/guides/user-visible-acceptance.md) 跑真实路径。

## 4. CI、测试和性能证据

- 修改测试至少实跑目标测试文件或目标函数；`compileall`、`ruff` 和 `git diff --check` 不能替代语义验证。
- Python 最后一次改动后运行 touched files 的 `ruff check` 和格式检查，提交前按仓库现有 pre-commit 入口复核。
- benchmark 开跑前写 scope lock：代码 commit、模型 snapshot、pipeline/class、请求入口、分辨率、帧数/fps、steps、并发/请求数、warmup、seed、guidance、compile/eager、GPU 和指标公式。
- 对齐其他 PR 或框架时，PR body 只是摘要；必须核对实际 config、runner/client、请求 payload、结果 JSON 和 server log。
- 异常数字先审请求链路：`config -> runner -> dataset -> request object -> payload -> server log`。禁止先加 `ignore-first`、settle 或放宽 baseline 掩盖字段未传递。
- L4 baseline 更新前先枚举完整同组 config；性能数字只能来自对应 perf runner/result JSON，functional smoke 或 accuracy 不能替代 perf baseline。
- 性能结果必须标成 `strict apples-to-apples`、`workload-aligned only` 或 `smoke only`。不满足 strict 时不能解释为框架性能差异。
- profiling 只有真实请求完成、trace 导出、artifact 来源一致且资源释放都可证明时才算完成。`ttfc_count=0`、`tpot_count=0` 等缺失指标必须写 unavailable。

## 5. 远端、容器和 GPU

- 远端 key 使用完整 `user@host:port`。先验证 repo、worktree、venv、版本、环境变量和模型 snapshot，再运行 pytest、serve、generate 或 benchmark。
- 共享机器上他人 repo、venv 和 cache 默认只读；需要修改时使用本轮自己的 clone/worktree、venv、cache 和 run directory。
- GPU 或大模型任务启动前记录 `pwd`、磁盘、GPU、`CUDA_VISIBLE_DEVICES`、HF/XDG cache 环境和目标 snapshot 是否存在。
- Hugging Face 加载使用验证过的本地绝对 snapshot，并启用 offline 模式；cache miss、需要下载或需要写他人 cache 时停止。
- SGLang diffusion 任务先跑 diffusion detection preflight，并记录 `sglang`、`torch`、cache、`PYTHONPATH` 和 GPU 环境；判定失败不进入正式运行。
- 安装、下载、编译、serve、generate、pytest 和 sweep 必须在远端自身带 timeout/watchdog、状态文件和日志，不能只依赖本地工具超时。
- 启动服务先验证 CLI，随后同时监控 health、PID 和错误日志；单请求 smoke 通过前不进入 sweep。
- 清理只针对本轮 PGID、run directory 和能够证明归属的进程；禁止宽泛 `pkill -f python`。大目录优先同盘移动到本轮 trash，再异步删除。
- 详细规则见 [live environment](../../framework/remote/guides/live-environment.md)、[HF offline](../../framework/remote/guides/hf-offline-mandatory.md) 和 [remote validation gates](benchmark/guides/remote-validation-gates.md)。

## 6. Git、PR 和公开证据

- 业务修改只在专用 worktree 完成；写入前确认 Git root、branch 和与目标 PR 的关系。
- vLLM-Omni commit 使用 DCO sign-off。提交和 push 前重读本节及 [Git/PR 入口](git/_index.md)。
- PR 前检查相对目标分支的 commit 列表和 diff，避免把历史实验、其他任务或临时 artifact 带入。
- PR body 先定证据合同：小修复写真实最小回归；性能 PR 绑定当前 head、最终 config、正式 result JSON 和 server log；reviewer follow-up 只回答当前仍成立的 thread。
- PR 的测试计划和结果只写语义测试、端到端、远端实测或 CI；lint、compile、diff hygiene 不能充当行为证据。
- 多个候选 PR 必须选唯一 merge vehicle。integration PR 确认后，窄 PR 只作历史参考并及时关闭 superseded 状态。
- 提交 PR 前运行仓库提供的 scope gate；触碰 tests、examples、entrypoints、model executor 或 diffusion 时逐文件说明 owner、必要性和测试绑定。
- 推送前确认 PR head owner、目标 remote 和当前 GitHub/SSH 身份。TaffyOfficial 拥有的分支只使用本机 `local/` 中登记并已验证的 Taffy SSH remote；不得回退到默认 HTTPS 身份或自造分支名。

## 7. 相关入口

- [review](review/_index.md)
- [CI](ci/_index.md)
- [docs 和 RFC](docs/_index.md)
- [debug](debug/_index.md)
- [dev 和配置](dev/_index.md)
- [Git 和 PR](git/_index.md)
- [benchmark 和 profiling](benchmark/_index.md)
- [remote](remote/_index.md)
- [components](components/_index.md)
- [models](models/_index.md)
