---
title: "Serving engine 生命周期规则"
created: 2026-09-03
updated: 2026-09-04
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #4834", "PR #4905", "PR #4912", "PR #5682", "PR #5713", "PR #5746", "PR #5843", "PR #5957", "PR #6008", "PR #6138", "PR #6202", vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/openai/api_server.py, "PR #6121", "PR #6214", "vllm_omni/engine/stage_runtime.py", "PR #5676", "PR #5491", "PR #6033", "PR #5272"]
confidence: high
---

# Serving engine 生命周期规则

`SERV-5a`–`SERV-5e` 与 `SERV-6a`–`SERV-6d`。触发条件与其余审查组见
[Serving 共享规则](rules.md) 的 Direct 代码快速入口；请求输入侧的合同留在该页，
故障隔离见 [fault isolation 规则](rules-fault-isolation.md)。

## Engine 生命周期合同

### SERV-5a — sleep/wake 状态必须保留 stage 和 tag 作用域

- 触发：sleep/wake 接受 `stage_ids`、resource tags 或 partial wake。
- 强制：状态 key 与公开操作的 stage/tag 作用域一致；只有全部必需 stage/tag 已 warm
  才放行 generation。
- 禁止：用一个全局 tag set 表示多 stage 状态；唤醒一个 stage 后清掉其他 stage 的
  sleeping 状态或把后续定向 wake 当成 already warm。
- 验收：sleep 两个 stage、只 wake 一个时 generation 仍拒绝，随后 wake 另一个才放行。
  ^[PR #4834]

### SERV-5b — 只有成功 ACK 和真实 backend capability 才能转为 warm

- 触发：worker ACK 可返回 error，或不同 backend 对 level-2 restore 能力不同。
- 强制：逐目标确认成功 ACK 后再清状态；level-2 能力按 backend/stage 表达。
- 禁止：错误 ACK 也清 tag；用 engine 全局禁令误伤已经支持 restore 的 diffusion worker。
- 验收：失败 ACK 保留 sleeping 状态；支持 level-2 的 diffusion 路径仍能
  sleep → wake → generate，不支持的 stage 在调用 worker 前明确拒绝。
  assembled app 对不支持的 level-2 wake 保留 sleeping state，并把既有
  `NotImplementedError` 映射为 OpenAI-style structured HTTP 501；bare route mock 只证明
  exception propagation，不能代替这条 live contract。^[PR #4834] ^[PR #4905]
  ^[PR #4912] ^[PR #5713]

### SERV-5c — 共享服务类重构必须闭合全部构造状态

- 触发：移动 model-specific capability 到 adapter、增加 factory/`__new__` 快路径，或让同一
  serving class 同时承载普通、无对应 stage、diffusion-only 等实例。
- 强制：列出每个生产构造入口及其必有/可选属性；所有公共 caller 通过统一 accessor 或显式
  `None` 状态访问 optional capability，startup warmup 与 request route 使用同一状态合同。
- 禁止：只测试目标 adapter 的正常构造；在 factory 实例上直接读取未初始化属性；用旧的
  model-type early return 掩盖无 adapter 状态。
- 验收：至少覆盖普通 adapter、无 adapter 和 bypass-`__init__` factory 三类实例，并实际调用
  startup warmup、voice list/upload 与对应 request route；每条路径保持重构前的成功或结构化
  错误合同，不得出现 `AttributeError`。 ^[PR #6138]

### SERV-5d — 应用 wiring guard 检查可用性而非属性名

- 触发：assembled app 的 route/middleware 依赖 `app.state` handler 或 factory wiring。
- 强制：mandatory state 同时检查属性存在且非 `None`；guard 测试通过 assembled app/公开 handler
  观察行为，并覆盖应用实际暴露的方法和 middleware inner-app 调用。
- 禁止：`hasattr` 接受显式 `None`；测试绑定可搬迁私有 symbol/单 router；用恒真断言证明 wiring。
- 验收：把 handler 置空、移除 route/method、绕过 inner app 三类 mutation 均使 guard 失败；
  正常 app 的 HEAD/OPTIONS census 与必需 state key 完整。 ^[PR #6202]

### SERV-5e — TTS detection 从 adapter metadata 的有序并集派生

- 触发：增加/迁移 TTS adapter，修改 `stage_keys`、`model_archs`、stage discovery、检测顺序
  或 speech-capable deployment topology。
- 强制：adapter 与显式 `LEGACY_TTS_DETECTORS` 构成完整 detector 并集；按
  `(detect_priority, name)` 确定性排序，等优先级 detector 不得重叠。stage-key 候选、仅靠
  architecture 定位的 AR entry stage、最终 model type 都从该并集派生；非集合规则覆写
  `matches()`，拓扑能力覆写 `stage_serves_speech()`，不要回填 `serving_speech.py` 分支。
- 边界：VoxCPM2 talker architecture 是高优先级权威匹配；Ming flash adapter 的 `ming_tts`
  stage-key 以默认 priority 100 先于 Ming dense 的 architecture fallback priority 200；CoVo 的通用 `fused_thinker_talker` 还需
  architecture 确认；Audex omni 还需同部署的 `audex_code2wav`。纯 diffusion 的
  `for_diffusion()` 直接绕过 adapter detection，当前 `DiffusionTTSAdapter` 没有生产 subclass。
- 验收：冻结旧 ladder 作为 oracle，覆盖 in-tree pipeline stage、adapter 声明 architecture、
  stage 集合等价、entry-arch 范围、无歧义/稳定顺序和 topology guard。`LegacyDetector` 只能缩减；
  AST ratchet 中超过 branch/legacy budget 失败，等于上限静默通过，少于上限则通过
  并显示收紧 reminder；下降本身不能让该 pre-commit hook 红灯，但未同步更新的 exact-equality
  pytest 仍会失败。在人工调低 constant 前存在可回增 slack，table dispatch 也是已固定的漏检形态，
  不能把 pre-commit 通过解释为不可绕过。
  `omnivoice_generator` 未被 pipeline 发出，是保留兼容事实而非
  可达性证据。^[PR #5682]
- adapter 提取保持共享 dispatcher 单一：Ming Flash 的 `validate()` 原样拒绝空 input、过长/非
  字符串 instructions、`task_type`/`language`/`x_vector_only_mode`/
  `initial_codec_chunk_frames`、`ref_audio`/`ref_text` 和非正 `max_new_tokens`；`build()` 继续委托
  server 的 `_build_ming_flash_omni_prompt()`，并返回空 `tts_params` 与固定 model type。公开校验
  和 generation preparation 都必须经 `resolve_adapter()`，不要把同一分支加回
  `serving_speech.py`。`LEGACY_TTS_DETECTORS` 当前为空，branch/legacy AST ratchet 是 27/0；
  Ming Flash 只由 adapter 的 `ming_tts` stage key 检测，且 legacy 名不得同时注册 adapter。
  验收仍须证明 `ming_tts` stage key 与 Ming dense architecture fallback 的消歧不变。
  ^[PR #5746] ^[PR #5843] ^[PR #6008]
- 证据：CPU oracle/ratchet suite 支撑检测等价；L20X VoxCPM2 只证明 architecture path 到达
  warmup，随后因基线同样复现的 vLLM skew 退出，未证明成功 speech endpoint/audio E2E。

## Full-duplex 与 CFG companion 生命周期

### SERV-5g — pure-diffusion TTS 必须在 AR adapter 解析前短路

- 触发：speech serving 同时支持普通 AR TTS 与 pure-diffusion TTS，且 diffusion factory 通过 `for_diffusion()`/`__new__` 绕过常规 `__init__`，发生 adapter 解析或 native speed handling 变更。
- 强制：在读取 adapter 或 `_adapter` 状态前先检查在两种构造路径上都可用的 `_diffusion_mode`；pure-diffusion 路径必须直接返回 `None` 并保持专用 speech 编码路径，普通 AR 实例继续通过 `resolve_adapter()` 使用既有 adapter-native speed 行为。
- 禁止：在 diffusion 实例上无条件解析 AR-stage TTS adapter、读取仅由 `__init__` 设置的 `_adapter`，或把 pure-diffusion 请求重新路由到 AR adapter 路径；只覆盖普通构造器而不覆盖 bypass-`__init__` factory。
- 验收：用 `OmniOpenAIServingSpeech.for_diffusion()` 构造实例，提交公开 `create_speech()` 请求并断言成功的 `200`/`audio/wav` 响应；以 mock 断言 diffusion speed 请求返回原值且 `resolve_adapter()` 未被调用，同时验证普通 AR 实例仍解析并使用其 adapter，所有路径不得出现 `AttributeError`。^[PR #6121]

### SERV-5h — 自定义 AR-Diffusion engine 与 worker-local session lifecycle 必须保持一致

- 触发：默认 stage 构造路径接入自定义 diffusion engine backend，或新增 worker-local AR session 的 reset/close lifecycle RPC 与副本限制。
- 强制：`load_and_resolve_stage_configs()` 在没有 deploy config 时也必须保留显式 `engine_backend`；runner 选择由选中的 engine/platform owner 负责，不重复注入 `diffusion_model_runner_cls`。session reset、close 和失败清理由选定 stage 的 collective RPC 到达实际 worker，并在所有 worker 支持后才确认成功；在 session-affine routing 尚未实现前，AR stage 必须保持单副本。
- 禁止：丢弃 `engine_backend` 使 AR 请求静默回退普通 `DiffusionEngine`；通过默认 stage 额外注入 runner class 覆盖 engine-owned 选择；只修改客户端状态而不调用 worker lifecycle；以 request-ID 级 affinity 或 round-robin 路由承载 worker-local session；将清理失败当作已关闭并允许立即复用 session ID。
- 验收：从真实 default-stage fallback 测试显式断言 `engine_backend` 进入最终 `engine_args`；用选定 stage ID 验证 reset/close RPC、unsupported worker 结果和失败重试；用两副本配置确认初始化前拒绝或证明持续 session affinity，并回归普通 diffusion engine 的既有 runner 选择。^[PR #5491]

### SERV-5i — TTS 模型专属采样覆盖必须归 adapter 所有

- 触发：新增或迁移 TTS 模型专属 sampling 参数、`max_new_tokens`、动态 token 限制、stop token 或 Audex CFG/TTA 参数。
- 强制：在已注册 adapter 的 `apply_sampling_overrides(sampling_params_list, request, prompt, request_id)` 中实现模型行为；`serving_speech` 仅负责合并 `extra_params`、调用 adapter override，再处理 `seed`。通用 `max_new_tokens` 必须通过共享 helper 深拷贝参数，模型特例保留各自的动态 token、CFG/TTA、stop-token 与 `+1` 语义；最终 detector 必须能解析到注册 adapter。
- 禁止：把新的 model-type 分支或采样 mutation 加回 `serving_speech.py`；让 adapter 直接污染 engine 的共享默认 sampling 参数；保留没有 adapter 支撑的 legacy detector，或用只验证 dispatch 到达的测试替代最终 `SamplingParams` 结果断言。
- 验收：覆盖 adapter registry/detection 无歧义、`extra_params -> apply_sampling_overrides -> seed` 顺序、无与有 `max_new_tokens`、CosyVoice3/GLM-TTS 动态边界、Ming stop token、Audex request-id/CFG/TTA 以及共享默认参数不变；测试必须检查传给 engine 的实际 sampling 参数。 ^[PR #5272]

### SERV-6a — full-duplex 首次 stage submit 必须预热 async-chunk topology

- 触发：full-duplex stage port、双工会话、async-chunk 或 stage fence 发生变化。
- 强制：stage-0 的首次 `submit_initial` 在 async-chunk 开启时预热后续 stage 的
  runtime/pool；每个 stage 保留自己的 fence、submit timestamp 和 request state。
- 禁止：等到 duplex audio/control 事件真正抵达才首次启动下游 stage；用一个全局 fence
  表示多 stage readiness；prewarm 失败后仍发布 generation-ready。
- 验收：覆盖首次 stage-0 submit、后续 stage submit、重复 update 和 prewarm failure；
  CPU/mock 测试必须证明 request state 与 stage pool 生命周期一致。

### SERV-6b — CFG companion 输出要非破坏性聚合并在所有 teardown 路径清理

- 触发：CFG companion、deferred parent、streaming terminal update、abort、stage error
  或 replica loss。
- 强制：parent re-submit 前 companion outputs 可重复读取；parent 只在全部 companion
  完成后释放；companion error/abort 必须给 deferred parent 发送结构化错误，并由统一
  cleanup 路径清理 parent、companion、tracker 和 stage-pool binding。
- 禁止：用 destructive `pop` 让第二次 terminal update 丢 companion；只清 parent 不清
  companion；companion 永久等待时静默挂起 parent。
- 验收：覆盖正常全量完成、重复读取、companion error、parent abort、companion abort
  和 replica loss，断言没有遗留 tracker state 或未完成的 deferred parent。

### SERV-6c — duplex capability gate 必须区分未启用与配置失败

- 触发：`session_mode=duplex`、`/v1/realtime?duplex=true`、runtime extension 或
  duplex deploy configuration 发生变化。
- 强制：入口只在明确的 duplex opt-in 下建立 handler；能力检查必须保留结构化配置
  错误与“不支持该模式”的区别，session、request、stage fence、lease 和 ordered
  mailbox 的生命周期必须在 disconnect、abort、expiry 与 replica loss 时一起终止。
- 禁止：把所有 config-load exception 折叠成 `duplex unavailable`；用普通 streaming
  handler 冒充持久 session；用全局 fence 或无界 pending input 替代 per-session bound。
- 验收：覆盖未 opt-in、有效 opt-in、malformed config、stale fence、lease expiry、
  disconnect 和 terminal response ordering；控制消息中的 dataclass/enum/tensor 必须
  在发送前变成 JSON-safe 值。

请求到 engine 的边界见 [Serving architecture](architecture.md)；公开协议通用检查见
[review contracts](../../../../general/review/guides/reviewer-lens-contracts.md)。

### SERV-6d — tokenizer-free 与 native speed 由 adapter capability 闭环

- 触发：stage 0 跳过 tokenizer，或 TTS adapter 声明 native speed control。
- 强制：token-only renderer 仅接受 token IDs/prompt embeddings，chat messages 明确失败。HTTP raw、SSE 与
  non-streaming 由 adapter 校验 native speed，encoder speed 固定 1；generic model 拒绝 `speed != 1`，
  WebSocket 在 parity 完成前固定 speed=1。
- 禁止：模型 duration scaling 后再次 resample，或以 HTTP 支持外推 WebSocket parity。
- 验收：覆盖 token/chat/embed、native/generic、三种 HTTP 输出与 WebSocket。落后后端只用显式
  capability/version shim 并保留 eager fallback，不能让 CUDA 新参数成为全平台前提。^[PR #5957]

### SERV-6e — async-chunk prewarm 失败必须保持 request-scoped 并停止 duplex bookkeeping

- 触发：async-chunk duplex 的 stage-0 首次提交需要 downstream prewarm，尤其是缺少 `prompt_token_ids` 或某个 downstream prewarm 提交失败时。
- 强制：prewarm 失败必须发送 request-scoped、non-fatal 的 `ErrorMessage`（400、`BadRequestError`），完成 abort cleanup 并关闭 duplex session；调用方收到失败结果后立即停止，不得继续写 fence、submit timestamp 或重新注册 running counter。
- 禁止：用 `fatal=True` 将单请求输入错误升级为 engine-wide failure；cleanup 已移除 request state 后仍返回成功或继续 duplex bookkeeping；让一个 request 的 prewarm 失败拖垮同批其他请求。
- 验收：覆盖缺失 `prompt_token_ids`、downstream submit 失败和 duplex submit fall-through，断言错误只归属目标 request、engine/thread 仍存活、下游未被错误预热，且无 fence、时间戳、counter 或 session 残留。^[PR #6033]

### SERV-8a — 本地 stage launch 必须临时应用 runtime.env

- 触发：修改 `StageRuntime` 的本地 LLM/diffusion replica launch、`runtime_cfg.env`、stage device scope 或 launch lock。
- 强制：本地 LLM launch 必须在现有串行 launch lock 内进入 `stage_runtime_env(stage_id, runtime_cfg)`；diffusion launch 必须将其与 device scope 组合，并保持 `runtime.devices` 作为有效设备选择。scope 只覆盖子进程构造/launch，退出时恢复父进程原值，并删除此前不存在的 key。
- 禁止：只解析或记录 `runtime.env` 却不应用到本地 launch；把 stage 环境永久污染到父进程；用 runtime env scope 替代 diffusion device scope；将该本地 scope 推广到 remote replica 或 headless worker launcher。
- 验收：CPU/mock 回归分别覆盖 LLM 和 diffusion launch 看到 stage 值、父环境已有值恢复、原先未设置的 key 在异常后被清理，以及 diffusion launch 同时看到 stage device 值；确认 LLM launch lock 仍覆盖进程创建。^[PR #6214]

### SERV-9a — diffusion stage batch size 必须落到 engine admission capacity

- 触发：diffusion stage 初始化或 replica launch 接收客户端 `batch_size`，或修改其 engine config、scheduler capacity 与 stage startup 路径。
- 强制：`initialize_diffusion_stage` 和 `launch_diffusion_stage_replica` 在 `build_diffusion_config` 之后、创建 diffusion client/proc manager 之前，都必须将 `od_config.max_num_seqs` 设置为请求的 `batch_size`；direct、parallel 和 single-stage 路径必须使用同一 capacity 语义。
- 禁止：只把 `batch_size` 传给 client 而保留 config 默认值；只修一个 startup 路径；从 `max_num_seqs > 1` 推断具体 pipeline 已支持 request batching，或绕过 `DIFF-6a` 的条件兼容 admission。
- 验收：分别 mock `initialize_diffusion_stage` 与 `launch_diffusion_stage_replica`，断言构造出的 `od_config.max_num_seqs` 等于客户端 batch size，并回归 single-stage 初始化；随后以 scheduler 和 Wan2.2 pipeline 测试证明该 capacity 只开放物理槽位，兼容 key、请求隔离和输出拆分仍有效。^[PR #5676]
