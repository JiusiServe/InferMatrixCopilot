---
title: "vLLM-Omni CI 规则"
created: 2026-08-23
updated: 2026-09-04
type: rule
tags: [vllm-omni, ci]
sources: ["PR #3422", "PR #5074", "PR #5255", "PR #5310", "PR #5402", "PR #5524", "PR #5543", "PR #5670", "PR #5713", "PR #5780", "PR #5823", "PR #5836", "PR #5957", "PR #5976", docker/Dockerfile.ci, docker/Dockerfile.xpu, .buildkite/intel/scripts/run-xpu-test.sh, .buildkite/cuda/test-merge.yml, .buildkite/cuda/test-ready.yml, "PR #5845", "PR #5872", "PR #6008", "PR #6048", "PR #6056", "PR #6096", "PR #6102", "PR #6202", "PR #6208", "PR #6273", "PR #6293", "PR #6311", "PR #6339", "PR #6343", "PR #6468", "PR #6523", .buildkite/common/scripts/run_cov_split.sh, .buildkite/common/scripts/upload_pipeline.py, .buildkite/cuda/test-nightly.yml, .buildkite/cuda/test-weekly.yml, .buildkite/npu/test-npu-nightly.yml, .pre-commit-config.yaml, tests/helpers/clean.py, tests/helpers/client.py, tests/helpers/mark.py, tests/helpers/runtime.py, tests/helpers/stage_config.py, tests/buildkite/test_upload_pipeline.py, tests/dfx/perf/scripts/run_benchmark.py, tests/dfx/perf/tests/test_minicpmo_4_5.json, tests/dfx/perf/tests/test_minicpmo_4_5_duplex_seed_tts.json, tests/dfx/stability/, tests/e2e/accuracy/minicpmo_4_5/test_minicpmo_4_5.py, tests/e2e/online_serving/helpers/minicpmo_4_5_duplex.py, tests/e2e/online_serving/test_flux_kontext_expansion.py, tests/e2e/online_serving/test_minicpmo_4_5.py, tests/e2e/online_serving/test_minicpmo_4_5_duplex.py, tests/e2e/online_serving/test_minicpmo_4_5_expansion.py, tests/model_tests/diffusion/diff_model_builders.py, tests/model_tests/diffusion/model_settings.py, tests/model_tests/diffusion/test_alignment.py, tools/nightly/run_nightly_jobs.sh, tools/pre_commit/check_tts_adapter.py, tests/tools/test_check_tts_adapter.py]
confidence: high
---

# vLLM-Omni CI 规则

只有 `OMNI-CI-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| 新模型、nightly、CUDA/NPU、硬件 marker、镜像升级 | `OMNI-CI-1a` | `.buildkite/**` → `pyproject.toml` markers → 目标 e2e/accuracy test |
| regression/guard、route census、middleware、mutation test | `OMNI-CI-1b` | 公开 app/handler → guard test；先证明旧实现会失败 |
| `NIGHTLY`/`WEEKLY`/`NON_CRITICAL`、L1/L4/L5、coverage、scheduled bootstrap | `OMNI-CI-1c` | `upload_pipeline.py` → bootstrap YAML → ready/merge/nightly/weekly YAML → coverage helper |
| pre-commit、SPDX、shellcheck、stability marker | `OMNI-CI-2a` | `.pre-commit-config.yaml`、`.buildkite/**`、`tools/**` |
| xdist、共享 worker、helper 拆分/启动回滚、下载 fixture、进程池 | `OMNI-CI-2b` | `tests/conftest.py`、`tests/helpers/{client,clean,runtime,stage_config}.py`、`tests/model_tests/**` |
| 重模型 cold start、共享 engine/server fixture、sleep/wake | `OMNI-CI-2c` | `tests/entrypoints/test_omni_sleep_mode.py`、OmniServer fixture scope/lock |
| diffusion tiny builder、model settings、alignment exclusion、重模型 OOM | `OMNI-CI-2d` | `tests/model_tests/diffusion/{diff_model_builders,model_settings,test_alignment}.py` → common offline tests |
| perf baseline、hardware label、DFX result artifact、assert-baseline | `OMNI-CI-3a` | `tests/dfx/conftest.py`、`tests/dfx/perf/scripts/run_benchmark.py`、`run_diffusion_benchmark.py`、`tests/dfx/perf/tests/**` |

## OMNI-CI-1a — 硬件 lane 必须真实收集并执行目标路径

- 触发：增加模型、硬件路径、nightly/ready/merge lane，或升级运行时/镜像。
- 强制：资源数、pytest marker、pipeline 路由和共享 stage registry 同步；必需依赖、模型初始化
  或 collection 失败必须让 job 失败，并证明目标测试数大于零且原失败在对应硬件消失。默认
  `prepend` import mode 下，whole-tree collection 遇到同名叶子目录时，所有中间父目录必须用
  `__init__.py` 保持规范限定包名，不能让不同子树都退化成同一个顶层包。
- 禁止：初始化失败后 skip-green；用 CPU 静态检查代替 CUDA/NPU 执行；只改模型目录而漏掉
  共享 registry/路由；把临时硬件硬编码留到合并。marker 名不等于实际硬件：某目录只有
  `core_model and cpu` lane 时，GPU-dependent case 也应使用该 lane selector，再用 CUDA
  availability skipif 作硬件门；标成无人选择的 `cuda` 会得到零 collection。
- 验收：当前 head 按真实 lane 的 whole-tree/marker scope 记录硬件、依赖版本、collection 数和
  执行结果，而非只收目标测试文件；同名叶子包必须解析为不同规范名（如
  `tests.e2e.accuracy.minimax_h3` 与 `tests.diffusion.models.minimax_h3`）。注入缺
  `__init__.py`、缺依赖、坏 registry 或错误 marker 时 lane 必须红。 ^[PR #3422]
  ^[PR #5310] ^[PR #5524] ^[PR #5543] ^[PR #5780]
  ^[PR #5872] ^[PR #6048] ^[PR #6096] ^[PR #6102]

MiniCPM-o online suite 的具体矩阵必须从 server args 读取：core 只跑 async chunk，expansion
分别跑 sync/async，duplex 又有自己的共享 server fixture。marker 与 parametrization 只能证明
collection 意图；没有实际 runtime 结果时，不能证明目标硬件行为。模型专属 fixture 合同见
[MCPMO-5b](../models/minicpm-o-4-5/rules.md#mcpmo-5b-online-serving-ci-必须显式区分-chunk-模式与-duplex-fixture-语义)。^[PR #6056]

## OMNI-CI-1b — 回归 fence 必须锚定可观察合同且非空转

- 触发：新增 bug regression、API guard、route census 或 middleware fence。
- 强制：从 assembled app/公开 handler 观察行为，只改变目标变量；必需 state 不仅检查存在，
  还要检查非 `None`。测试须在旧实现或代表性 mutation 上失败，在修复后通过。mock engine
  自己抛出的异常只能证明 route 不吞异常；真实 backend 状态与 HTTP mapping 必须另由 live
  server 触发生产操作验证，不能把 mock-authored type/message 当成 backend contract。
- 禁止：绑定可搬迁私有符号或单个 router；用恒真类型断言、错误参数的提前失败、宽泛
  `>=400`、不同文本或长度冒充目标分支证据。
- 验收：mutation 分别置空 wiring、移除目标 route/method、绕过 inner middleware，fence 均失败；
  route census 覆盖应用实际暴露的 HEAD/OPTIONS 和依赖 state key。异常路径分别用 CPU mock
  证明 route propagation，并用 live assembled app 触发真实 backend condition、核对结构化
  status/body 与失败后的 state。 ^[PR #3422] ^[PR #5074] ^[PR #5670] ^[PR #5713] ^[PR #6202]

## OMNI-CI-1c — scheduled lane 与 coverage owner 必须按完整 gate 矩阵验证

- 触发：修改 Buildkite bootstrap 的 branch/env/PR-label 条件、L1/L4/L5 workload 归属、
  `--e2e` 上传、coverage helper，或 docs/skip-mark-only 的 scheduled escape hatch。
- 强制：`main + NIGHTLY=1` 只拥有 L4 nightly；`main + WEEKLY=1` 上传 L5 weekly，且为
  CUDA ready/merge 加 `--e2e` 跑完整 L2/L3 E2E 与 per-mode coverage；
  `main + NON_CRITICAL=1` 只上传 weekly 的 non-critical E2E group。普通 main merge 与
  非 main PR labels 必须继续走各自 gate，NPU scheduled nightly 不隐式上传 ready。
  docs-only/skip-mark-only diff 可以跳过默认 CI，但不能吞掉这些 main scheduled lane。
- coverage 所有权：CUDA/AMD ready/merge 的 L1 pytest 不附带 `--cov`；weekly CPU job 对
  `tests/ -m 'core_model and cpu'` 生成合并报告。`run_cov_split.sh` 只在
  `WEEKLY=1 && BUILDKITE_BRANCH=main` 拆分 offline/online coverage 与 artifact；其他调用
  必须保持一次 combined pytest、无 coverage。为 whole-tree collection 移动测试或延迟导入
  example 时，仍须保持原 marker 与测试语义。
- 禁止：把 `nightly-test` label 当 weekly CPU coverage gate；让 `NIGHTLY=1` 顺带占用
  L2/L3；用 pipeline 已上传推断嵌套 group 一定执行；通过 `pytest --collect-only | grep ...`
  枚举文件却不传播 collection 失败或不检查结果非空。PR #6311 合并时 weekly TTS 循环仍有
  这个 fail-green 缺口，不能把该 lane 的绿色结果当作完整 TTS collection 证据。
- 验收：对 docs-only、CI-level-only、普通 main、三种 schedule env、CUDA/NPU 与每个 PR label
  逐项渲染 bootstrap，并断言 child upload、`--e2e` 和 group-level `if`；coverage helper 分别
  验证 weekly-main 拆分上传与其他环境 combined/no-cov。任何动态 collection 都要让 import
  error、零 selection 和单文件失败使 job 红。^[PR #6311]

## OMNI-CI-2a — CI 工具、schema 和 hook 是可复现供应链

- 触发：修改 pre-commit/Buildkite schema、下载 lint 工具、SPDX/import 检查或 stability marker。
- 强制：固定工具版本并校验摘要；声明本地与 CI 强制 hook 矩阵；路径跨 Windows/POSIX
  归一化；源码头使用项目 SPDX 标识且覆盖 `.sh`；marker 参数 shell-quote 并有明确默认值。
- 禁止：下载浮动 `stable`；让 rebase 静默回退 hook/marker；未引用包含 `: ` 的 YAML command；
  用测试名后缀代替硬件 marker。
- 验收：当前 main schema/pre-commit、DCO 和 marker collection 通过；篡改摘要、Windows 路径、
  shell header 或非法 stability 参数分别被对应 gate 拒绝。 ^[PR #3422] ^[PR #6273]
  ^[PR #6293] ^[PR #6343]
- pre-commit ratchet 不能把债务下降当成 hook 失败：`actual > budget` 才返回 1，
  相等静默通过，
  `actual < budget` 必须返回 0 并打印收紧上限的 reminder。passing hook 需 `verbose: true`
  才能让提示可见；hook 的 `files` 还必须包含 checker 自身，使 budget 修改也会
  触发审计。下降后未及时收紧会留出 slack，被检测分支只要不超旧上限就可
  回增；直接提高 budget 也只会通过并打印 slack notice，所以“上限只能下降”仍由
  reviewer 审核。手写 repo-wide constant 还使 verdict 受 merge order 影响，不是
  merge-base-relative 合同。
  现有 unit test 另外直接断言 count 等于 budget，所以下降但未改 constant 时 hook 会通过，
  而该 test 若被收集仍会失败；两者应统一为同一非递增语义。^[PR #6008]

## OMNI-CI-2b — 并行测试基础设施隔离任务失败和共享状态

- 触发：xdist、共享下载 fixture、长寿命 judge/transcriber worker、进程池 retry，或 spawned `torch.distributed` process group。
- 强制：任务级异常后丢弃污染 worker；submit/result 串行，只有进程崩溃可 retry-once；传给
  xdist 的参数可序列化，依赖固定兼容 major；共享文件在读锁前显式检查存在，写入保持锁语义。spawned `torch.distributed` 必须为每个 group 传入新鲜 `file://` rendezvous URL，不能先释放 TCP port 再把其数字交给子进程；`get_open_port` 只用于真实 TCP service。
- 共享 helper 的边界必须清晰：请求 client 从 `tests/helpers/client.py`、环境/设备清理由
  `clean.py`、server/runner 生命周期由 `runtime.py` 提供；pytest plugin `conftest.py` 只注册
  fixture，调用方不得依赖它的隐式或 star-import re-export。`__init__` 或 `__enter__` 的启动失败
  不会调用 `__exit__`，所以必须立即回滚已启动的 stage 子进程、关闭已打开的日志 FD 并清除临时
  日志；只有显式 `VLLM_OMNI_KEEP_LOG` 调试选择可保留日志文件。测试 deploy helper 只接受新
  schema 的顶层 `stages`；不得静默回退 `stage_args`，缺失时 consumer error 必须指出配置文件。
- 禁止：普通 task error 复用同一进程；为 pytest 生命周期不可达的竞态堆测试；把并行参数或
  活对象隐式跨进程传递；把 file rendezvous 套用于 Mooncake/RDMA 等真实监听服务。
- 验收：OOM、普通异常和 BrokenProcessPool 分别验证隔离/重试；online/offline xdist 均通过，
  并发 cache miss 只产生一个完整文件；spawned Gloo/NCCL group 使用独立 file rendezvous，真实 TCP service 仍使用 port helper。 ^[PR #6208] ^[PR #6339] ^[PR #6468] ^[PR #6523]

## OMNI-CI-2c — 昂贵 engine fixture 复用必须恢复状态并隔离拓扑

- 触发：为减少 checkpoint cold start，把 function-scoped engine/server 提升到 class/module
  scope，或合并 sleep/wake 等重模型 case。
- 强制：不兼容 topology 使用不同 class-scoped fixture，保证同一时刻只有一个 heavy engine；
  module 前后各做一次 device cleanup；每个 case 在 `finally` 将共享 engine wake/reset 到可用
  状态。不可逆的 level-2 sleep case 放在独立 module-scoped server 的最后，结束后只 teardown。
- 禁止：共享 engine 后依赖测试顺序留下的 sleep/tag/cache 状态；在 module-scoped
  `omni_server` 持有 fixture lock 时再创建 function-scoped server，造成锁等待或 GPU 争用；
  为省 cold start 删除 topology、TP 或 post-wake generation 的独立覆盖。
- 验收：分别覆盖 LLM、diffusion 与 multi-stage topology；每个可恢复 case 后下一 case 从 awake
  开始；level-2 terminal case 之后不再复用 server；统计目标 lane 确实只初始化预期数量的
  engine，且 cleanup 后无 worker/device state 遗留。^[PR #5713]

## OMNI-CI-2d — diffusion tiny builder 必须替代资源缩减而不是能力缩减

- 触发：重模型 online E2E 因显存 OOM 迁移到 tiny-model framework，或修改
  `DIFFUSION_TEST_SETTINGS` / `EXCLUDED_MODELS`。
- 强制：builder 从真实 pipeline/config 构造缩小 checkpoint，按组件分别收缩 encoder/DiT；
  attention head dim 改变时同比缩放 `axes_dims_rope`，并保留 architecture 要求的轴数与总维度。
  settings 必须列出真实 supported tasks 和每个 acceleration group；只有 builder/settings 已接通
  common tests 后，才从 alignment exclusion 删除模型。
- 禁止：为消除 OOM 直接删除 TP/CFG/cache/offload coverage；把 online suite 从双卡 parallel cases
  缩为单卡 base 后仍声称 online lane 覆盖这些组合；从 tiny checkpoint 通过外推 full checkpoint
  显存、数值质量或吞吐。
- 验收：alignment 双向断言 registry 中每个非排除 pipeline 有 settings，且 settings 不指向排除项；
  common offline suite 对每个 task 跑 base，并逐组执行声明的 acceleration。Flux Kontext 当前 tiny
  contract 是 text-to-image + image-to-image，附加 TP+CPU offload、CFG+CPU offload、以及
  TP+CPU offload+Cache-DiT；online expansion 只保留单 L4 base smoke，parallel coverage 的所有权迁到
  common offline suite，不代表 full-model OOM 已被修复。tiny builder 从收缩后的真实组件配置初始化
  random BF16 weights，只证明 construction、routing 与 control-flow，不证明真实 checkpoint 加载、
  输出质量、显存或吞吐。^[PR #5823]

## OMNI-CI-2e — release rebase 的 image、容器资源与实际辅助负载必须成套对齐

- 触发：升级 vLLM/torch base image，或新版本在 startup 增加资源检查、编译缓存与 warmup 行为。
- 强制：正式 release 直接使用同版本 base image 的自洽依赖集；只有目标是未发布 SHA 时才恢复
  wheel 重装及其 torch/CUDA/NumPy ABI 修复。容器显式满足新 startup check（共享内存等），硬件数
  同时计入测试辅助模型：主模型占卡时，Whisper 等 grader 需要 spare accelerator 才能避免 CPU 超时。
- 禁止：在 release image 上保留补偿旧 image 的依赖手术；用 Docker 默认 `/dev/shm`；只按被测模型
  卡数配置 lane 而忽略 grader；把部分 nightly green 当全部兼容问题已关闭。
- 验收：image tag 与目标 release 一致；startup 通过共享内存 preflight；目标 lane 证明实际 grader
  device；每个残余失败独立记录，尤其数值/质量回归不能由 API 兼容测试替代。^[PR #5976]

## OMNI-CI-3a — DFX baseline artifact 与性能回归 gate 是两个合同

- 触发：修改 perf JSON 的 `baseline`、硬件 label/marker、benchmark result schema，或恢复性能阈值断言。
- 强制：baseline 只接受 `{hardware: {metric: threshold}}` 的硬件嵌套结构；顶层 hardware 必须是
  `pyproject.toml` 中带 `[hardware-resource]` 标签的 pytest marker，每个 bucket 非空。metric 名可
  自定义，值只能是单点 scalar 或与 `request_rate` / `max_concurrency` 顺序严格对齐的 list。
  runner 在每个 sweep step 写 result 前按 `sweep_index` 将所有 hardware bucket 的 list 收窄为
  当前 scalar，scalar 原样保留；结果仍保留所有 bucket，留给下游 consumer 选择实际硬件。
- 禁止：把 result 中存在 baseline 描述成 active regression gate；从执行 marker 推断同名阈值
  bucket 存在；使用 flat metric map、以 concurrency 为键的 metric dict、未知/alias-only hardware
  label，或让 baseline list 与 sweep 顺序脱节。`_RUNTIME_DEVICE_ALIASES` 只服务 result filename
  与运行时身份，不扩展 baseline allowlist；runtime 也不自动选择 baseline bucket。
- 验收：当前 CI 仍只用 `completed == num_prompt(s)` gate 请求完成数；baseline artifact 是描述性
  元数据而非阈值断言。单测须覆盖 omni/diffusion sweep 的逐步收窄、所有 hardware bucket 保留、
  自定义 metric/scalar，以及 flat、未知 label、dict value、缺 index、越界失败。若重新引入性能
  gate，必须有显式 consumer、hardware bucket 选择、metric directionality 与失败测试。
  当前实现没有 upfront list-length 校验：短 list 到被访问的 index 才失败，多余值静默不用；若
  QPS 与 concurrency 同时配置，同一 list 会按两个独立 loop 的位置复用。因此配置 review 必须
  人工核对 mode、list 长度和顺序。`[hardware-resource]` 也只代表 baseline key 可解析，不代表
  `hardware_marks()` 能调度该资源：当前 H200/B200 尚未进入 CUDA resource 分支。另有四个
  Hunyuan 配置只保留 H200 baseline，却仍标记 H100/A3 执行，当前因无阈值断言而被掩盖。
  runtime alias 匹配还应保持最长 token 优先；目标 pin 中 `B200` 早于 `GB200`，会把 GB200 名称
  归一化成 B200，修复前不可把 filename label 当精确设备证据。
  MiniCPM-o 4.5 的 nightly perf 是这个边界的具体实例：最终 simplex/duplex 配置都是单卡 H100，
  runner 命令没有阈值开关；simplex 只 gate 完成请求数，duplex 另要求每 session 恰好四个音频
  response。配置里的 H100 baseline 因此只是结果 artifact，既不能证明回归阈值，也不能外推到
  A3；PR 文本中的“双卡”描述也不能覆盖最终 lane/YAML 的单卡事实。^[PR #5524]
  ready perf 复用同一合同：Seed-TTS English、`openai-chat-omni`、text+audio、关闭 thinking 并启用
  TTS template，sweep 是 `(concurrency,num_prompts)=(1,10),(4,40)`。CUDA lane 分配 `h100_1`；NPU
  lane 分配 `a3_npu_2`，但 JSON hardware mark 声明每 case `num_cards: 1`，资源 allocation 不等于
  模型 stage 用卡数。两边都直接调用 runner、没有 `--assert-baseline`，所以仍只 gate
  `completed == num_prompts`；H100 metrics bucket 在 A3 run 中也只是 artifact，不能构成 A3 threshold。
  ^[PR #6079]
- ready 的 `source_file_dependencies` 只列 perf JSON、MiniCPM deploy/model/stage processor；shared
  `run_benchmark.py`/DFX conftest 由 nightly 覆盖，故不触发这个高成本 model job。functional
  offline/online/duplex jobs 不可因 perf job 存在而删除：perf 只发 Seed-TTS text prompt，不覆盖 offline、
  non-stream text content assertion 或 image/video/audio multimodal ingestion。若要降成本，应收窄各自
  workload，而不是声称 perf 是 functional superset。^[PR #6079]
  ^[PR #5402] ^[PR #5845]

- Qwen3-Omni Async Chunk 的一个 perf JSON 可以承载多个 top-level case；`mark` 是按 case
  附着的，CI 即使使用 `--test-config-file` 也必须用硬件和 scheduling marker 过滤。CUDA nightly
  选择 `H100 and full_model and not slow`，weekly 选择 `H100 and slow`；A3/NPU 保持独立
  `npu` 选择。不要把没有 A3 实测值的 H100 baseline 留在 A3-only case：该 case 在重新测量前
  只能 collect/run，不能伪装成 A3 阈值。减少 workload 后同样必须移除失效 baseline，待重新测量。
  清理单例 E2E 前要按输入/输出合同检查 suite-level owner：本轮 default text+audio perf 与
  streaming audio-only 由 multi-replica suite 保留，Async Chunk text-only 仍保留；不支持的
  chat output `audio.format`（如 `aac`）则迁至 weekly invalid-parameter HTTP case，断言 400 和
  supported-format 提示。纯文本五并发的 reduced-token 配置独立覆盖 batching，不能因删除相邻
  audio-only case 而丢失。^[PR #6570]

## OMNI-CI-3b — patched upstream benchmark 必须保持参数与 output subtype 兼容

- 触发：upstream `benchmarks/serve.py` 增参，或 Omni 聚合字段只存在于扩展 output subtype。
- 强制：patched copy 逐版本同步公开参数及控制流；background probe 从独立的最小请求生成，主 workload
  完成后显式停止。Omni-only duplex metrics 用 tolerant attribute reads 聚合，plain-vLLM output 缺字段
  等价于空集合，不能抹掉已经成功的主结果。
- 禁止：以“看似无关”删除 upstream 新参数；把 probe 混入 throughput/latency 主样本；直接读取扩展字段
  导致普通 backend 的结果整体 fallback 成 completed=0。
- 验收：签名/控制流与 pinned upstream 对照；probe rate 0 与正值覆盖启动/停止；plain 与 Omni output
  混合列表都保留完成数，只有存在时才写 duplex metrics。^[PR #5976]

## OMNI-CI-3c — XPU release image 从同版 upstream target 构建

- 触发：升级 XPU vLLM/torch/Inductor 镜像，或为 compiler 故障改变 model/stage eager gate。
- 强制：从精确 release tag 的 upstream `Dockerfile.xpu` 构建 `vllm-openai` target 后再叠 Omni；torch、oneCCL、
  triton-xpu 成套 pin。v0.27 使用 triton-xpu 3.7.2并保留 upstream oneCCL。
- 强制：新 API 未支持时用平台 gate 保留 eager。PyTorch 2.13 XPU Dynamo 的 duplicate-handler
  workaround 只覆盖 Qwen2.5 Thinker/Talker 和 Qwen3 shared code predictor，不得扩展成全局
  XPU eager。
- 禁止：用旧 Omni base target 冒充新版 upstream、卸掉 oneCCL 只补 triton，或以 CUDA
  通过外推 XPU。
- 验收：核对 image provenance、XPU import/startup，以及这三条路径 compile 未被调用而
  其他模型保留原能力。^[PR #5957]
