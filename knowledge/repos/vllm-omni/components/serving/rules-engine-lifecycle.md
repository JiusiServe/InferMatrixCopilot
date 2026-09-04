---
title: "Serving engine 生命周期规则"
created: 2026-09-03
updated: 2026-09-05
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #4834", "PR #4905", "PR #4912", "PR #5221", "Issue #4855", "PR #5277", "PR #5682", "PR #5713", "PR #5746", "PR #5843", "PR #5957", "PR #6008", "PR #6084", "PR #6138", "PR #6202", vllm_omni/engine/async_omni_engine.py, vllm_omni/engine/membership_controller.py, vllm_omni/engine/messages.py, vllm_omni/engine/orchestrator.py, vllm_omni/engine/stage_pool.py, vllm_omni/entrypoints/async_omni.py, vllm_omni/entrypoints/openai/api_server.py, tests/engine/test_membership_controller.py, tests/engine/test_orchestrator_event_driven.py, "PR #6121", "PR #6214", "vllm_omni/engine/stage_runtime.py", "PR #5676", "PR #6525", "Issue #6435", "PR #5491", "PR #6033", "PR #5272", "PR #6186", "PR #6241", "vllm_omni/entrypoints/openai/tts_adapters/moss_tts.py", "PR #6346", "PR #6581", tests/entrypoints/test_omni_sleep_mode.py, "PR #4092", vllm_omni/worker/base.py, "PR #6564", tests/engine/test_orchestrator.py, tests/entrypoints/openai_api/test_qwen3_omni_realtime_websocket.py, "PR #6189", tests/entrypoints/test_async_omni_diffusion_config.py, "PR #6367", vllm_omni/outputs/output_processor.py, tests/engine/test_async_omni_engine_abort_ack.py, tests/entrypoints/test_async_omni_pause_sleep_routing.py]
confidence: high
---

# Serving engine 生命周期规则

本页收纳 `SERV-5a`–`SERV-5e`、`SERV-5g`–`SERV-5r`、`SERV-6a`–`SERV-6f`、
`SERV-8a` 与 `SERV-9a`。触发条件与其余审查组见
[Serving 共享规则](rules.md) 的 Direct 代码快速入口；请求输入侧的合同留在该页，
故障隔离见 [fault isolation 规则](rules-fault-isolation.md)。

## Engine 生命周期合同

### SERV-5r — default diffusion stage 必须保留并按显式性合并 model extras

- 触发：修改 `AsyncOmniEngine` default diffusion stage fallback、promoted top-level model option、
  `stage_overrides` 或 local/unregistered Diffusers checkpoint 启动。
- 强制：先保留 caller `extras`，只有 explicit non-`None` top-level promoted option 才覆盖同名 extra，
  其余键保持 caller value 或 builtin default；stage-0 `extras` override 必须合并进 default fallback 的
  输入。registered stage 保持既有 complete override mapping，不得因修复 fallback 改写其语义。
- 禁止：以 builtin default 覆盖 caller-only extra；让 unregistered/local checkpoint 忽略 stage-0 extras；
  只修 registered config 路径或只断言 helper dict 而不覆盖 fallback resolution。
- 验收：覆盖 caller-only extras、explicit top-level precedence、stage-0 extras 在 default fallback 的
  end-to-end resolution，以及 registered path 不回归。^[PR #6189]

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

### SERV-5j — TTS adapter 必须承载模型专属请求合同与采样覆盖

- 触发：speech endpoint 接入没有 speaker/reference-audio 的 text-to-music 模型，或模型的必填字段、采样控制和普通 TTS 合同不同。
- 强制：注册 adapter 并由 adapter metadata 完成 detection；adapter 负责 `validate()`、prompt/token-id 构造和 `apply_sampling_overrides()`，明确 `input` lyrics、`instructions` caption、固定 sampling、长度上限及被拒绝的 TTS 字段，shared serving 只负责公共 dispatch。
- 禁止：在 `serving_speech.py` 增加 model-type 分支；静默忽略 `voice`、reference audio、temperature 或 `stream` 等不支持字段；把无 speaker 模型套用普通 TTS 的 voice 或 temperature 语义。
- 验收：通过真实 adapter detection 和 `/v1/audio/speech` 请求覆盖缺失/空 lyrics、缺失/空 caption、unsupported fields、长度边界、tokenizer 校验与非流式输出，并断言送入 engine 的实际 prompt、sampling 参数和 model type。 ^[PR #6186]

### SERV-5k — stage request 的 min_tokens 必须受剩余上下文约束

- 触发：orchestrator 用 `SamplingParams` 构造 stage request，且 prompt 已占用部分 `max_model_len`。
- 强制：clone 参数后计算 `remaining=max_model_len-len(prompt_token_ids)`；`max_tokens is None` 时设为 `remaining`，并将 `min_tokens` 限制为 `max(0, remaining)`，不得改写调用方对象。
- 禁止：只在 `max_tokens=None` 时处理 `min_tokens`；让 `check_stop` 因过大的最小 token 数永远早退；用静默 fallback 掩盖上下文已满。
- 验收：覆盖剩余 46、50、0 token 的请求，断言最终 request 参数、原始参数不变，并回归普通 stage 的默认 max-token 行为。 ^[PR #6346]

### SERV-5l — TTS 静态能力与运行时 voice 必须分属 owner

- 触发：TTS serving 提取或迁移 built-in speakers、precomputed profiles、supported languages、codec frame rate，或修改 voice upload/list/delete 与 embedding 校验。
- 强制：adapter 初始化时一次性加载 `TTSCapabilities` 快照；静态模型能力归 adapter，`supported_speakers` 与 `supported_languages` 使用 `frozenset`，`precomputed_speakers` 保存 profile metadata，server 只拥有 `uploaded_speakers`，可用 speakers 由两者并集派生且上传集合独立维护。
- 禁止：让 server 保存或修改静态能力；把上传 voice 合并进 built-in speaker 集合后在删除时 `discard`，或把 frozen dataclass 误解为内部 profile mapping 的深层不可变；在共享 serving 中恢复 model-type capability 分支。
- 验收：构造相关 adapter，断言能力在初始化后进入 snapshot、集合类型正确且内置/预计算/上传 voice 的并集完整；删除与 built-in 同名的上传 voice 后内置 voice 仍存在，并验证无 adapter 的 diffusion 路径不会触发 adapter 属性错误或专属维度校验。^[PR #6138]

### SERV-5m — AR lifecycle 控制必须先封锁 admission，并以 backend 完成信号收尾

- 触发：修改 `AsyncOmni` 的 pause/resume、sleep/wake 或 abort，或改变
  `StagePool.collective_rpc` 到 AR EngineCore / diffusion worker 的控制面路由。
- 强制：在 sleep drain/offload 前设置 frontend admission gate；AR stage 经 orchestrator
  路由到 EngineCore 的 `pause_scheduler`、`resume_scheduler`、`sleep`、`wake_up`，diffusion
  stage 继续走 worker sleep/wake RPC。`wake_up()` 不得替 AR/mixed engine 解除 admission，只有
  `resume_generation()` 可以解除；已 paused 时的定向 pause 和 cache clear 仍须执行。stage ID
  必须先校验范围。只允许这四个已知 EngineCore helper 使用 `*_async` fast path，并保持 caller
  timeout；其余 RPC 仍走 collective path。需要 frontend cleanup 的 abort 必须关联 result，等待
  orchestrator 完成 stage abort、binding release 和 request cleanup 后才移除 frontend state，失败或
  timeout 必须保留 state 并传播。
- 强制：sleep 先关闭 admission，再等待所有 in-flight `_admitting` submissions drained 后才 offload；P0
  先 reset MM cache，stage tag 保留 per-stage scope。wake 不重新开启 AR admission，仍只由
  `resume_generation()` 解除。AR abort 必须把 cumulative terminal-prefix token 由 output processor
  传至 stage pool/orchestrator 并 ACK 回 async queue；先物理 abort，再 commit output/request state，且
  state 延迟到 generator 消费后清理。只移除最后一个 child，只有最后 terminal output 收敛；control RPC
  exceptions 必须传播。diffusion abort 路径未因本 PR 改写。
- 禁止：以单一 frontend flag 代替 AR scheduler 控制；在 sleep RPC 后才阻止 `generate()`；让
  wake 隐式 resume；因已 paused 跳过不同 stage scope 或 cache reset；将任意同名 `*_async` helper
  绕过 collective timeout；在 abort ack 前 pop request state，或将 abort failure 当成功。
- 验收：覆盖 AR-only、diffusion-only 和 mixed stage 路由；sleep 进行时 generation 等待，AR
  sleep → wake 后仍需显式 resume，跨 AR+diffusion 的 sleep/wake E2E 必须在 post-wake
  `generate()` 前显式调用 `resume_generation()`，而 diffusion-only sleep → wake 可恢复 admission；重复/定向
  pause 仍调用 scheduler 与 cache clear，非法 stage ID 产生明确错误，fast path 仅命中四个方法且
  timeout 生效；abort success 后才清理 frontend state，orchestrator error 与 timeout 时 state 保留。
  本 PR 的测试/PR body 没有独立 GPU performance 或全量 diffusion-abort evidence。^[PR #6084] ^[PR #6581] ^[PR #6367]

### SERV-5n — remote replica attach/detach 必须按本次 membership generation 判定

- 触发：修改 `MembershipController` 的 register、watcher snapshot、unregister、shutdown 或 remote client factory。
- 强制：以 `(stage_id, replica_id)` 分别记录 attaching/attached，重复 register 在 attach 完成前后都只保留一个 client。每次 watcher snapshot 单调递增 generation；controller 创建的地址只有在本次 attach 开始后真实观察到 `UP`，才可因后续消失触发 detach；未跟踪的 static client 继续按相邻 snapshot 的 `UP -> absent` 清理。factory 返回后若 shutdown 已开始，或地址校验/`StagePool.add_client` 失败，必须关闭尚未接管的 client；正常 detach 同步清理 membership bookkeeping、pool client、受影响请求和 client 资源。
- 禁止：让 attach 前的 stale `UP` snapshot 立即删除刚注册 client；并发重复创建同一 replica；shutdown 后继续接受 register 或挂入 late client；把“曾在任意 generation 出现”当作当前 attachment 已确认。
- 已知边界：`asyncio.to_thread` 中正在执行的 factory 不能随外层 task cancellation 一起停止；若 membership task 被直接取消，thread 后来返回的 client 仍可能失去 cleanup owner。该低严重度泄漏在 PR 中明确延期，现有 shutdown/late-result 回归不能证明 cancellation 路径已关闭。
- 验收：覆盖 register storm、register 前后 stale/fresh `UP`、attach 中 watcher churn、untracked disappearance、invalid stage/address、`add_client` 异常、shutdown-before/during/after factory、detach 后重新注册和受影响 request error；另以专门用例保留或修复上述 cancellation leak。^[PR #5277]

### SERV-5o — wake 的设备同步只在 device-owning worker 执行

- 触发：修改 `AsyncOmni` 的 wake RPC、worker `handle_wake_task()`，或为 sleep/wake
  增加 platform/CUDA 同步。
- 强制：`AsyncOmni` 只 dispatch wake RPC、等待 ACK 并更新 frontend 状态；实际 device
  同步留在执行 wake 的 worker 路径。这样 proxy 或 HTTP-server-only 的 `AsyncOmni` 不会因
  wake bookkeeping 初始化 CUDA context。
- 禁止：在 `AsyncOmni` 的 wake completion 路径重新导入 platform 或调用全局
  `synchronize()`；不能以收到 ACK 代替 worker 已完成其设备同步的合同。
- 验收：用不拥有 CUDA device 的 proxy/frontend 实例经过 diffusion wake RPC，断言
  frontend 不创建 CUDA context；另断言 worker `handle_wake_task()` 在返回成功 ACK 前仍完成
  同步。PR #4092 只声称既有测试通过，未提供可复现命令或该 proxy 回归；其要求 inline
  guard/comment 的 review thread 在合并时仍未 resolve，故这条验收尚未被该 PR 证明。^[PR #4092]

### SERV-5p — streaming final stage 的 raw terminal 必须闭合一次 output lifecycle

- 触发：`async_chunk` streaming/realtime 的 final output stage 收到 raw `finish_reason`，或修改
  orchestrator raw/processed poll、terminal routing、request cleanup。
- 强制：只把非 segment 的 session-level raw terminal 计入 final-output-stage completion；同一 poll
  必须先路由 processed outputs。若所有 final output stages 已完成、仍存在 request state、且没有
  processed terminal 完成 cleanup，则使用既有 terminal-empty output helper 发出一个 `finished=True`
  的最终 `OutputMessage`，然后走普通 request/CFG-parent cleanup。full-duplex session 不适用这个
  fallback。
- 禁止：仅记录 raw completion 而让 Realtime generator 永远等不到 terminal message；在 processed
  data 前发送 fallback；为普通 segment stop 或非-final stage 合成 terminal；用超时伪造完成，或在
  已 cleanup 后再发第二个 terminal。
- 验收：CPU 覆盖 raw-terminal-only、data-then-raw-terminal、processed-terminal-plus-raw-terminal
  三种同 poll 形状，分别断言完成、数据先于 terminal、exactly once 和 request state 清理；Qwen3-Omni
  Realtime async-chunk 长音频 E2E 断言 `response.audio.done` 到达且音频有效。^[PR #6564]

### SERV-5q — 事件驱动编排只能改变唤醒机制并保持双路径合同

- 触发：修改 `VLLM_OMNI_EVENT_DRIVEN_ORCH`、orchestrator output loop、stage reader/poller、或 `AsyncOmni` final-output drain。
- 强制：默认关闭时保留 legacy 1 ms poll loop；开启时每个 live LLM replica 的 reader 直接 await `get_output_async()`，再进入单一串行 dispatch，使 routing、output ordering、terminal cleanup、scheduler stats 与 per-replica `EngineDeadError` isolation 同 legacy path。reader 必须每 0.5 s 按 live membership 与 client object reconcile，client swap、eviction 或新注册不得遗失输出或留下 task。diffusion 维持 `get_diffusion_output_nowait()` poller，metrics-only sentinel 在 route 前吸收。final-output drain 使用同一 flag 的 queue blocking read，engine 缺少该方法时回退 legacy drain；1 s timeout 只用于 orchestrator liveness check，shutdown 必须关闭其 executor/queue 资源。
- 禁止：把 "event-driven" 外推为所有 stage 均无 polling；从一个 loop 删除 metrics、raw-terminal 或 fault-isolation handling；在 busy queue 下只在 timeout reconcile，或让 reader failure 重启为重复 eviction；把两种 loop 的 orch-monitor iteration counts/`loop_active_pct` 直接比较。
- 验收：以 flag guard 重跑 legacy LLM/diffusion, async-chunk, abort, shutdown, multi-replica, scheduler-stat 和 dead-replica parity scenarios；另测 accepted/unrecognized flag values、default legacy selection、client swap 后 reader reconcile、blocking drain 的 queued/late message、timeout/liveness 与 executor shutdown。性能测试另绑定同一 current-head build、硬件、workload、warmup 与多次 A/B；PR #5221 的 H20 数字在 fault-isolation rebuild 前测得，不能作为 current-head performance proof。两条文档 review 要求已进入最终代码，但对应 thread 合并时仍为 unresolved。^[PR #5221] ^[Issue #4855]

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

### SERV-6f — 必需 CFG companion 的构造与 admission 必须原子完成

- 触发：engine 为 CFG 请求展开 companion，且 guidance 是模型必需能力，或 companion 需要经过 input processor 才能获得完整 Omni request metadata。
- 强制：先构造并处理全部 companions，再把 parent 和 companions 一起入队；处理后用 `upgrade_to_omni_request` 恢复 `additional_information`/`global_request_id` 等 Omni 字段；任一构造或处理失败都向调用方传播并保持队列无变化，非 CFG expansion 返回空列表并保留普通 admission。
- 禁止：先 enqueue parent 再吞掉 companion 异常；只入队一侧、让 companion 丢失 external/global request identity，或在 Scheduler 建立后才安装 CFG pairing gate。
- 验收：分别模拟 prompt expansion、input processing 和 tokenizer 失败，断言 parent/companion 均未入队；成功路径断言两者 metadata、ID suffix、sampling params 和 pair identity 完整；无 companion 的普通请求仍正常 admission。 ^[PR #6186]

### SERV-8a — 本地 stage launch 必须临时应用 runtime.env

- 触发：修改 `StageRuntime` 的本地 LLM/diffusion replica launch、`runtime_cfg.env`、stage device scope 或 launch lock。
- 强制：本地 LLM launch 必须在现有串行 launch lock 内进入 `stage_runtime_env(stage_id, runtime_cfg)`；diffusion launch 必须将其与 device scope 组合，并保持 `runtime.devices` 作为有效设备选择。scope 只覆盖子进程构造/launch，退出时恢复父进程原值，并删除此前不存在的 key。
- 禁止：只解析或记录 `runtime.env` 却不应用到本地 launch；把 stage 环境永久污染到父进程；用 runtime env scope 替代 diffusion device scope；将该本地 scope 推广到 remote replica 或 headless worker launcher。
- 验收：CPU/mock 回归分别覆盖 LLM 和 diffusion launch 看到 stage 值、父环境已有值恢复、原先未设置的 key 在异常后被清理，以及 diffusion launch 同时看到 stage device 值；确认 LLM launch lock 仍覆盖进程创建。^[PR #6214]

### SERV-9a — client diffusion batch width 不得覆盖 scheduler admission capacity

- 触发：diffusion stage 初始化或 replica launch 接收客户端 `batch_size`，或修改其 engine config、scheduler capacity 与 stage startup 路径。
- 强制：`initialize_diffusion_stage` 和 `launch_diffusion_stage_replica` 只将 `batch_size` 转发给 `StageDiffusionClient`；`build_diffusion_config()` 解析出的 `od_config.max_num_seqs` 必须保持 CLI `--max-num-seqs` 或 stage YAML 的值。两条启动路径和 single-stage 路径都不得把 client `diffusion_batch_size` 映射为 scheduler capacity。
- 禁止：在 shared init path 写入 `od_config.max_num_seqs = batch_size`，或用 `max(CLI, batch_size)` 合并两个独立旋钮；也不得从 `max_num_seqs > 1` 推断具体 pipeline 自动支持 request batching，兼容 admission 仍受 `DIFF-6a` 约束。
- 验收：分别 mock `initialize_diffusion_stage` 和 `launch_diffusion_stage_replica`，断言 config 的 `max_num_seqs` 保留 CLI/YAML 的 `1`、`8` 或 `None`，而 client 仍收到 `batch_size`；回归 single-stage 初始化。Wan request-level batching 必须显式设置 `--max-num-seqs N` 或 YAML；Qwen-Image step-execution 的并发 scheduler capacity 不得被默认 `diffusion_batch_size=1` 降为 1。^[PR #5676] ^[PR #6525] ^[Issue #6435]
