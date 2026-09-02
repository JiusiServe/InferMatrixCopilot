---
title: "vLLM-Omni CI 规则"
created: 2026-08-23
updated: 2026-09-02
type: rule
tags: [vllm-omni, ci]
sources: ["PR #3422", "PR #5074", "PR #5310", "PR #5402", "PR #5524", "PR #5543", "PR #5670", "PR #5713", "PR #5780", "PR #5845", "PR #5872", "PR #6048", "PR #6096", "PR #6102", "PR #6202", "PR #6208", "PR #6273", "PR #6293", "PR #6339", "PR #6343"]
confidence: high
---

# vLLM-Omni CI 规则

只有 `OMNI-CI-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批源码 |
|---|---|---|
| 新模型、nightly、CUDA/NPU、硬件 marker、镜像升级 | `OMNI-CI-1a` | `.buildkite/**` → `pyproject.toml` markers → 目标 e2e/accuracy test |
| regression/guard、route census、middleware、mutation test | `OMNI-CI-1b` | 公开 app/handler → guard test；先证明旧实现会失败 |
| pre-commit、SPDX、shellcheck、stability marker | `OMNI-CI-2a` | `.pre-commit-config.yaml`、`.buildkite/**`、`tools/**` |
| xdist、共享 worker、下载 fixture、进程池 | `OMNI-CI-2b` | `tests/conftest.py`、`tests/helpers/**`、`tests/model_tests/**` |
| 重模型 cold start、共享 engine/server fixture、sleep/wake | `OMNI-CI-2c` | `tests/entrypoints/test_omni_sleep_mode.py`、OmniServer fixture scope/lock |
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

## OMNI-CI-2a — CI 工具、schema 和 hook 是可复现供应链

- 触发：修改 pre-commit/Buildkite schema、下载 lint 工具、SPDX/import 检查或 stability marker。
- 强制：固定工具版本并校验摘要；声明本地与 CI 强制 hook 矩阵；路径跨 Windows/POSIX
  归一化；源码头使用项目 SPDX 标识且覆盖 `.sh`；marker 参数 shell-quote 并有明确默认值。
- 禁止：下载浮动 `stable`；让 rebase 静默回退 hook/marker；未引用包含 `: ` 的 YAML command；
  用测试名后缀代替硬件 marker。
- 验收：当前 main schema/pre-commit、DCO 和 marker collection 通过；篡改摘要、Windows 路径、
  shell header 或非法 stability 参数分别被对应 gate 拒绝。 ^[PR #3422] ^[PR #6273]
  ^[PR #6293] ^[PR #6343]

## OMNI-CI-2b — 并行测试基础设施隔离任务失败和共享状态

- 触发：xdist、共享下载 fixture、长寿命 judge/transcriber worker 或进程池 retry。
- 强制：任务级异常后丢弃污染 worker；submit/result 串行，只有进程崩溃可 retry-once；传给
  xdist 的参数可序列化，依赖固定兼容 major；共享文件在读锁前显式检查存在，写入保持锁语义。
- 禁止：普通 task error 复用同一进程；为 pytest 生命周期不可达的竞态堆测试；把并行参数或
  活对象隐式跨进程传递。
- 验收：OOM、普通异常和 BrokenProcessPool 分别验证隔离/重试；online/offline xdist 均通过，
  并发 cache miss 只产生一个完整文件。 ^[PR #6208] ^[PR #6339]

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
  ^[PR #5402] ^[PR #5845]
