---
title: "Serving 规则"
created: 2026-07-20
updated: 2026-09-02
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #3576", "PR #4718", "PR #4834", "PR #4905", "PR #4912", "PR #5085", "PR #5157", "PR #5670", "PR #5682", "PR #5713", "PR #5732", "PR #5746", "PR #5752", "PR #6138", "PR #6202", "claude-workflow-starter-private@09dca46", "zuiho-kai/claude-workflow-starter@c217fc6", vllm_omni/entrypoints/async_omni.py, vllm_omni/entrypoints/openai/diffusion_request_utils.py, vllm_omni/entrypoints/openai/serving_speech.py, vllm_omni/entrypoints/openai/serving_video.py, vllm_omni/entrypoints/openai/video_api_utils.py, vllm_omni/entrypoints/openai/tts_adapters/, vllm_omni/engine/orchestrator.py, vllm_omni/engine/cfg_companion_tracker.py, vllm_omni/metrics/prometheus.py, tests/entrypoints/openai_api/test_audex_serving_guards.py, tests/entrypoints/openai_api/test_omni_sleep_wakeup.py, tests/entrypoints/openai_api/test_tts_detection.py, tests/entrypoints/openai_api/test_video_api_utils.py, tests/entrypoints/openai_api/test_video_server.py, tests/tools/test_check_tts_adapter.py, tools/pre_commit/check_tts_adapter.py]
confidence: high
---

# Serving 规则

只有 `SERV-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

- **SERV-0a — PR 描述先选代码地图。** Direct review 先按 title/body 声明的协议、请求字段或服务能力命中下表，再用 pinned changed files 校验真实 dispatcher 和范围；描述不能作为 finding 证据。
- **SERV-0b — 复用同一份 serving 证据。** 第一次 Codex review 打开命中函数后，把 request 对象、caller 搜索、测试和 findings 追加到同一份证据包；不得让专项重新扫描整个 serving 树。

| PR 描述在做什么 | 精确规则组 | 第一批 live 源码 |
|---|---|---|
| `extra_body`、flattened/nested/canonical/legacy 输入、alias、`negative_prompt`、diffusion request extras | `request-contract`：`SERV-4a`–`4h` | `vllm_omni/entrypoints/openai/diffusion_request_utils.py::{normalize_diffusion_request_args,apply_normalized_diffusion_request_extra_args}` → `serving_chat.py::{OmniOpenAIServingChat._preprocess_chat,OmniOpenAIServingChat.generate_diffusion_images}` |
| batched chat、fan-out/fan-in、sub-request ID、choice collapse、whole-batch error | `batch-chat-contract`：`SERV-4i`–`4k` | `api_server.py::create_batch_chat_completion` → `batch_serving.py::OmniOpenAIServingChatBatch` → ordinary chat completion children |
| `chat_template_kwargs`、raw HTTP/SDK `extra_body`、text/audio modalities、choices、空音频 | `chat-multimodal-contract`：`SERV-4c` + 命中模型规则 | upstream `ChatCompletionRequest` → `serving_chat.py::{OmniOpenAIServingChat._preprocess_chat,OmniOpenAIServingChat.chat_completion_full_generator,OmniOpenAIServingChat._create_text_choice,OmniOpenAIServingChat._create_audio_choice}` |
| endpoint restriction、route/app-state guard、capability、公开 400 | `endpoint-capability`：`SERV-4c`, `SERV-4d`, `SERV-5d` | endpoint policy → `api_server.py::build_app` assembled app → public handler |
| sleep/wake、partial stage/tag、idempotency、ACK、generation admission | `engine-lifecycle`：`SERV-5a`, `SERV-5b` | `entrypoints/async_omni.py::{AsyncOmni.sleep,AsyncOmni.wake_up,AsyncOmni.generate}` → `worker/base.py::{handle_sleep_task,handle_wake_task}` / `diffusion/worker/diffusion_worker.py` |
| serving class/factory 重构、optional adapter、diffusion/no-TTS 实例、warmup | `engine-lifecycle`：`SERV-5c` | `entrypoints/openai/serving_speech.py` 的所有 factory/`__new__` 路径 → `warmup`、voice upload/list、speech request caller |
| TTS model detection、`stage_keys`/`model_archs`、adapter priority/topology、legacy migration | `engine-lifecycle`：`SERV-5e` | `tts_adapters/__init__.py::{iter_tts_detectors,detect_tts_model_type,all_tts_stage_keys,tts_entry_stage_archs}` → `serving_speech.py::_find_tts_stage` |
| SSE/streaming speech、audio format、PCM/WAV、speed、首 chunk 前校验 | `streaming-format`：`SERV-1a`, `SERV-1b` | `vllm_omni/entrypoints/openai/protocol/audio.py::{OpenAICreateSpeechRequest.validate_streaming_constraints,StreamingSpeechSessionConfig.validate_streaming_constraints}` → `serving_speech.py::{OmniOpenAIServingSpeech._validate_speech_streaming_request,OmniOpenAIServingSpeech.create_speech}` |
| video reference 解码、mixed media、frame conversion/mux、bounded memory | `media-ingress`：`SERV-1c`–`1e` | `entrypoints/openai/video_api_utils.py` decode/coerce/encode helpers → video server callers |
| `ref_audio`、x-vector/ICL、content identity、artifact cache/readiness | `artifact-readiness`：`SERV-3a`–`3c` | `serving_speech.py` reference resolve/decode/cache → adapter speaker cache → prefix salt |
| Prometheus、waiting/running gauge、replica stats、throttle、collector lifecycle | `metrics-lifecycle`：`SERV-2a`, `SERV-2b` | `vllm_omni/entrypoints/omni_base.py::{OmniBase._log_summary_and_cleanup,OmniBase._process_stage_metrics_message}` → `vllm_omni/metrics/prometheus.py::{OmniPrometheusMetrics.__init__,set_running,set_waiting}` |

| 审查组 | 什么时候触发 | 规则 ID |
|---|---|---|
| `core` | 每次 serving 审查 | `SERV-4c` |
| `streaming-format` | SSE、audio streaming、format/default/capability | `SERV-1a`, `SERV-1b` |
| `media-ingress` | video reference、decoder registry/backend、mixed capability、bounded upload/conversion | `SERV-1c`–`1e` |
| `metrics-lifecycle` | metrics、gauge、replica、collector | `SERV-2a`, `SERV-2b` |
| `artifact-readiness` | artifact/content cache、capability、ready/mark/discard | `SERV-3a`, `SERV-3b`, `SERV-3c` |
| `chat-multimodal-contract` | chat template kwargs、SDK flatten、text/audio response shape | `SERV-4c` + 命中模型规则 |
| `endpoint-capability` | endpoint restriction、route/app-state guard、公开 400 | `SERV-4c`, `SERV-4d`, `SERV-5d` |
| `engine-lifecycle` | sleep/wake、partial stage/tag、ACK、generation admission、factory 状态矩阵、TTS adapter detection | `SERV-5a`, `SERV-5b`, `SERV-5c`, `SERV-5e` |
| `full-duplex` | duplex opt-in、stage prewarm/fence、async-chunk、CFG companion lifecycle | `SERV-6a`–`SERV-6c` |
| `request-contract` | 请求字段、来源、冲突、dispatcher、consumer view | `SERV-4a`, `SERV-4b`, `SERV-4c`, `SERV-4d`, `SERV-4e`, `SERV-4f`, `SERV-4g`, `SERV-4h` |
| `batch-chat-contract` | frontend fan-out、identity、choice cardinality、error/cancellation | `SERV-4i`, `SERV-4j`, `SERV-4k` |
| `author-routing` | 只供 Direct reviewer 导航，不作为 finding 规则 | `SERV-0a`, `SERV-0b` |

## SERV-1a — 所有可预判错误在第一个 streaming chunk 前返回

- 触发：SSE/streaming 接口新增 format、audio、output modality 或 extra-body 参数。
- 强制：在 streaming/non-streaming 分叉以及发送首个 chunk 前完成合同校验，非法请求
  返回结构化 4xx。
- 禁止：先发送文本成功 chunk，再在 audio/encoder 分支发现参数非法并静默结束；客户
  端会看到 HTTP 成功但缺失后半段输出。
- 验收：坏格式在两种模式都得到相同 4xx；测试证明坏请求没有产生任何 SSE chunk，
  合法请求仍按协议完成。 ^[PR #4718]

## SERV-1b — 支持格式、默认值和 backend capability 只有一个来源

- 触发：protocol enum、validator、encoder/backend 分别维护 format/default 列表。
- 强制：protocol、校验器和执行层引用同一 canonical 常量，并以实际 backend capability
  为上限。
- 禁止：把 backend 不支持的格式列为合法值，再靠中途 fallback；不同文件各复制列表。
- 验收：每个公开格式都有 encoder smoke；移除格式只改 canonical owner，协议和校验测试
  同步反映。 ^[PR #4718]

## SERV-1c — media decoder 参数只在真实入口可达时对外声明

- 触发：替换 video/image reference decoder、接入 loader registry、新增 backend/fps/
  frame-selection 参数或改变坏媒体错误。
- 强制：只有请求/配置入口能把值传到 loader 时才声明参数可配；否则在最近
  loader 调用处固定实际值。frame sampling 只消费真正传入的 target metadata；decoder
  返回零帧必须继续映射为 `InvalidInputReferenceError`，不能因共享 loader 只记 warning
  就返回空 `VideoFrames`。
- 禁止：不得留下没有 caller 传入的 backend/fps 形参或死分支；不得因 registry 存在
  多 backend 就宣称 vLLM-Omni 已支持运行时选择；不得丢失替换前的非空帧 fail-safe。
- 验收：同一合成视频分别断言 first-N 与 last-N 顺序、数量和 fps；覆盖非法
  `keep`、非正 `max_frames`、无效字节与 loader 零帧，且真实 Qwen multimodal/video
  请求仍通过公开入口。 ^[PR #5085]

## SERV-1d — mixed media 必须 capability-gated，request 错误在解码前限界

- 触发：共享 video serving 接受 mixed image/video/audio、typed URL/data URL 或 multipart upload。
- 强制：unknown model 默认无 mixed capability；只有 model metadata 明示支持才允许 image+video。
  multipart 大小/格式等可在字节边界判定的约束必须 bounded-read 并在解码前拒绝；pipeline 的
  request-facing validation 使用可跨 worker 保留 client metadata 的错误类型，统一映射为 400。
- 禁止：删除旧互斥 guard 后让所有 diffusion 模型继承 mixed input；用 unbounded `read()` 后
  再检查；让 plain `ValueError` 穿过 stage worker 变成 500。
- 验收：支持模型的 mixed request 成功，unknown/不支持模型在 engine 前返回 400；multipart
  oversize/bad format 与 pipeline count/shape 错误保持同一 client-error 合同。typed URL/data URL
  是否同样 bounded 必须单独证明；本 pin 的 helper 仍完整读取。模型专有 allowlist、temp-file
  与 input matrix 见 [MiniMax H3 rules](../../models/minimax-h3/rules.md)。 ^[PR #5752]

## SERV-1e — 长视频转换只保留必要的全视频 buffer，并逐帧保持旧语义

- 触发：修改 video output 的 normalize、float→uint8、RGBA strip、mux 或 fragmented encode。
- 强制：预分配最终 contiguous uint8 video，逐帧 clip/scale/round 写入，禁止先 `np.stack`
  全量 float frames 再产生全量转换临时量；这只消除额外副本，原 normalized float frames、最终
  uint8 buffer 及上游 device→host 分配仍存在，不能称为 O(1) memory。
- 强制：所有 frame shape 相同；只有 rank-3 HWC 且 C=4 才去 alpha，二维 width=4 灰度不能
  截断。mixed float dtype 先用 `np.result_type` 得到 common dtype，再逐帧计算，以保持 legacy
  stack 的 promotion/rounding/checksum；不得原地改输入。当前 uint8 fast branch 因 normalization
  先转 float32 而实际上不可达，不能拿它作为性能或语义证明。
- 验收：回归测试禁止 float path 调用 `np.stack`，并覆盖 input immutability、RGBA、width-4
  grayscale、mixed float16/float32 与 exact uint8 output。性能证据必须分开报告 conversion 和
  未改动的 MP4 encode：PR #5732 的可复现实验仅绑定 209×1344×768 float32 RGB、24 FPS、
  ultrafast、fresh process、3 次 median/RSS 10 ms；conversion 1201.15→529.47 ms、conversion+MP4
  1808.96→1235.26 ms、peak RSS 8.874→4.141 GiB、above-resident 5.393→0.660 GiB，两个 hashes
  相同。PR body 的 362-frame 与 4×MI300X E2E 是另一组观察，不能混合或泛化。^[PR #5732]

## SERV-2a — 指标节流和 gauge 按 scheduler/stage/replica owner 隔离

- 触发：orchestrator 聚合多 stage/replica stats，或新增全局 throttle/gauge。
- 强制：节流状态按实际 producer owner 隔离；request 状态 cleanup 后再计算 waiting 等
  gauge。
- 禁止：用一个全局时间戳让先上报的 replica 抑制其他 replica；在 pop/cleanup 前发布
  最终 gauge。
- 验收：同一窗口内两个 replica 都能上报；单请求完成并清理后 waiting=0。 ^[PR #3576]

## SERV-2b — collector 重建只保护本项目 family

- 触发：同进程重建 engine、注册 Prometheus collectors 或调整 unregister 行为。
- 强制：只保护需要跨实例保留的 `vllm:omni_*` family，并保留 upstream collector 的
  正常 unregister/cleanup。
- 禁止：把 upstream unregister 整体置空，导致重复 timeseries 注册。
- 验收：同进程连续创建/销毁两次 engine，无 duplicate-timeseries 错误且 Omni family
  仍可采集。 ^[PR #3576]

## 缓存 readiness 与失败隔离

### SERV-3a — readiness 必须表达 artifact 能力而非仅表达 identity

- 触发：serving 层按 URI/key 缓存预处理 artifact，并在后续请求剥离原始输入。
- 强制：readiness key 或 capability predicate 必须包含 consumer 真正需要的 mode/字段；
  只有 artifact 已具备全部必需字段时，才能进入 artifact-only 路径。
- 禁止：因为 `artifact_key` 相同就跨模式复用；原始输入已剥离后再让 worker 尝试补算
  缺失字段。
- 验收：覆盖“能力不足 artifact → 更强请求”与“能力超集 artifact → 较弱请求”，前者
  保留原始输入并重新计算，后者是否复用必须作为明确性能取舍。Qwen3-TTS 的方向性
  合同见 [Qwen3-TTS 规则](../../models/qwen3-tts/rules.md)。 ^[PR #5157]

### SERV-3b — readiness 状态迁移与错误存活性一起验证

- 触发：修改 artifact ready/track/mark/discard、失败清理或 eviction。
- 强制：所有状态入口使用同一 key/capability 合同；请求级 prompt/build 错误不得杀死
  engine，后续健康请求仍应成功。
- 禁止：只改 ready 查询而遗漏 mark/discard；只测同模式 cache hit，不测跨模式顺序和
  counterfactual failure。
- 验收：单测枚举状态迁移；E2E 复现原始坏顺序、证明修复后存活，并在回退修复代码时
  重新出现目标错误，避免测试空跑。 ^[PR #5157]

### SERV-3c — 内容身份必须原子贯穿全部缓存层

- 触发：本地/inline reference audio 或其他 locator 同时经过 decode、speaker/code 与 prefix cache。
- 强制：先通过 allowed-local-media gate，再规范解析 URI/stat；本地身份至少含 size 与
  `st_mtime_ns`。decoded payload 与 identity 一次计算、一起返回，并把同一身份贯穿每层 cache key
  和 prefix salt；named voice 加 inline ref 按真实分支区分。
- 禁止：raw locator 充当内容 salt；授权前 stat；两次独立 decode/stat；用 client-controlled
  locator 建无界共享 side table；把完整 base64/路径写日志。
- 验收：同长度覆盖、并发改写、named+inline、speaker cache 和 prefix hit 均不复用旧内容；
  非法路径不 stat，日志只含截断值且命中真实 logger hierarchy。 ^[PR #5670]

## 请求输入合同

### SERV-4a — 公开字段由 serving 显式拥有

- 触发：修改请求 allowlist、冲突字段集或兼容输入。
- 强制：逐项绑定真实 consumer，公开字段由 serving 边界显式声明。
- 禁止：从包含 tensor、KV 状态或运行时中间量的内部结构反射生成公开字段。
- 验收：加入一个内部同名字段反例，证明它不会被误算成公开 root 字段。

### SERV-4b — 多来源输入验证前不得合并

- 触发：请求同时支持 flattened、raw nested、声明字段、alias 或 canonical container。
- 强制：保留来源直到冲突检查结束；验证通过后若用字典展开构造并集，必须注明各映射
  已经不相交。
- 禁止：用 `or`、字典展开或 `update()` 决定重复值，制造未声明优先级。
- 验收：重复字段返回明确 4xx，不重叠字段全部到达最终 consumer。

### SERV-4c — 入口接受必须闭环到每个生产消费者

- 触发：新增请求字段或改变字段分流。
- 强制：对每条 dispatcher 追踪字段到 engine、pipeline、prompt 或 sampling 参数。
- 禁止：用 helper 返回值或 HTTP 成功代替传播证明。
- 验收：真实请求对象同时覆盖默认值和非默认值，并断言最终 consumer。

### SERV-4d — 同一请求合同错误跨 dispatcher 保持同一响应合同

- 触发：同一非法输入可进入 diffusion-only、multi-stage 或其他多个 dispatcher。
- 强制：使用一致的 status、错误类型和消息策略，并在公共边界转换一次。
- 禁止：一路本地映射为 4xx，另一路交给远处通用 `ValueError` 捕获。
- 验收：同一冲突输入经过每条受影响 dispatcher 时响应等价，且都在 engine/pipeline
  调用前失败。

### SERV-4e — 请求期弃用信号必须对 operator 可见

- 触发：serving 路径继续接收 deprecated 输入。
- 强制：使用项目 logger 的 `warning_once` 或明确限频策略。
- 禁止：使用仅写 stderr 且按调用点过滤的 `warnings.warn`。
- 验收：合法旧输入恰好记录一次警告；因冲突返回 4xx 的输入不记录兼容警告；用户响应
  合同与日志合同分别断言。

### SERV-4f — Serving 只编译当前 slice 拥有的请求语义

- 触发：同一 serving 字段存在 flattened、nested、canonical 或 legacy 来源。
- 强制：在 request mutation、preprocess 和 dispatcher 分支之前完成一次来源校验，并
  产出当前 slice 限定字段的 consumer view。
- 禁止：dispatcher 重读 raw request 或重新决定优先级；为了 request-extra
  normalization 把 topology、模型能力、逐 stage 参数或其他 owner 吸进完整 compiler。
- 验收：root control + nested extras 分别经过 pure/mixed dispatcher 到达 prompt、
  AR metadata 与 diffusion sampling consumer；registry 字段与 service control 重名时
  仍只有一个 owner。

### SERV-4g — 多来源合同编码前必须完成来源矩阵

- 触发：一个语义存在多个来源、dispatcher 或 stage scope。
- 强制：按 [source-consumer decision matrix](../../../../general/review/guides/review-execution-contract.md#source-consumer-decision-matrix)
  标明路由、重复拒绝、不适用和 defaults；兼容写法默认进入同一 consumer scope，只有
  矩阵声明不同语义时才能分流。规范化结果拆成多个 consumer view 时默认互不重叠，
  同一字段确需进入多个 view 时逐一命名最终 consumer。
- 禁止：矩阵缺失时声称实现或审查完成；由字段集合运算、输入写法或 dispatcher 末端
  defaults 隐式决定 scope。
- 验收：每个来源组合都有明确 decision 和生产路径证据；每个 consumer view 的重叠项
  都有显式最终 consumer，不存在接受后丢弃或末端重新读取 raw request。

### SERV-4h — 请求合同膨胀时停止逐评论修补

- 触发：生产 diff 超过预算上限 1.5 倍、出现第二个重叠语义 owner，或下一审查波次
  再次发现同一 owner 漏洞。
- 强制：执行 [架构重置验收](../../../../general/review/guides/code-taste.md#架构重置怎样验收)，
  重新确认唯一最终产物、删除清单和规模上限。
- 禁止：继续堆 helper、compatibility branch 或 reviewer-specific patch。
- 验收：恢复编码前 owner、consumer、删除项和 diff 预算都有可检查记录。

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
- 边界：VoxCPM2 talker architecture 是高优先级权威匹配；Ming flash 的 `ming_tts` legacy
  stage 先于 Ming dense 的 architecture fallback；CoVo 的通用 `fused_thinker_talker` 还需
  architecture 确认；Audex omni 还需同部署的 `audex_code2wav`。纯 diffusion 的
  `for_diffusion()` 直接绕过 adapter detection，当前 `DiffusionTTSAdapter` 没有生产 subclass。
- 验收：冻结旧 ladder 作为 oracle，覆盖 in-tree pipeline stage、adapter 声明 architecture、
  stage 集合等价、entry-arch 范围、无歧义/稳定顺序和 topology guard。`LegacyDetector` 只能缩减；
  AST ratchet 的 branch/legacy budget 也只能下降，但 table dispatch 是已固定的漏检形态，不能把
  pre-commit 通过解释为不可绕过。`omnivoice_generator` 未被 pipeline 发出，是保留兼容事实而非
  可达性证据。^[PR #5682]
- adapter 提取保持共享 dispatcher 单一：Ming Flash 的 `validate()` 原样拒绝空 input、过长/非
  字符串 instructions、`task_type`/`language`/`x_vector_only_mode`/
  `initial_codec_chunk_frames`、`ref_audio`/`ref_text` 和非正 `max_new_tokens`；`build()` 继续委托
  server 的 `_build_ming_flash_omni_prompt()`，并返回空 `tts_params` 与固定 model type。公开校验
  和 generation preparation 都必须经 `resolve_adapter()`，不要把同一分支加回
  `serving_speech.py`。#5746 仍保留同名、priority 50 的 legacy detector，所以当前只是**执行
  adapter 提取**：检测仍由 legacy 条目先命中，随后以相同 model-type 名解析到 adapter；清理
  detector 时必须先用 detection union/oracle 证明 `ming_tts` 对 Ming dense architecture 的优先级
  不变。当前 target 还违反 `test_tts_detection.py::test_legacy_detectors_have_no_adapter` 的全局
  不变量（legacy 名必须 `resolve_adapter(...) is None`）；只删除旧的
  `test_ming_flash_omni_not_migrated` 不能修复它。验收必须移除该同名 legacy 条目并让 adapter
  自身保留所需 priority，或显式重定义并成套更新 union 不变量测试。^[PR #5746]
- 证据：CPU oracle/ratchet suite 支撑检测等价；L20X VoxCPM2 只证明 architecture path 到达
  warmup，随后因基线同样复现的 vLLM skew 退出，未证明成功 speech endpoint/audio E2E。

## Full-duplex 与 CFG companion 生命周期

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
