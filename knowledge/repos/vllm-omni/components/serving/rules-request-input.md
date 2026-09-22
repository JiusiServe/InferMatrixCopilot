---
title: "请求输入合同"
created: 2026-09-04
updated: 2026-09-22
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #3805", "PR #5374", "PR #5885", "PR #6598", vllm_omni/data_entry_keys.py, vllm_omni/engine/async_omni_engine.py, vllm_omni/entrypoints/openai/, vllm_omni/entrypoints/omni_base.py, vllm_omni/engine/orchestrator.py, vllm_omni/inputs/, tests/engine/test_async_omni_engine_input.py, tests/engine/test_orchestrator_error_handling.py, tests/entrypoints/test_omni_entrypoints.py, tests/entrypoints/openai_api/test_invalid_audio_speech.py, tests/entrypoints/openai_api/test_serving_speech.py, "PR #5181", "PR #6182", "PR #6963", "PR #4741", "PR #4167", "PR #7447", "PR #7459", "PR #7463", "PR #5691"]
confidence: high
---

# 请求输入合同

`SERV-4a`–`SERV-4q`：公开请求字段的校验、限界与 owner。触发条件与其余审查组见 [Serving 共享规则](rules.md) 的 Direct 代码快速入口。

## SERV-4a — 公开字段由 serving 显式拥有

- 触发：修改请求 allowlist、冲突字段集或兼容输入。
- 强制：逐项绑定真实 consumer，公开字段由 serving 边界显式声明。
- 禁止：从包含 tensor、KV 状态或运行时中间量的内部结构反射生成公开字段。
- 验收：加入一个内部同名字段反例，证明它不会被误算成公开 root 字段。

## SERV-4b — 多来源输入验证前不得合并

- 触发：请求同时支持 flattened、raw nested、声明字段、alias 或 canonical container。
- 强制：保留来源直到冲突检查结束；验证通过后若用字典展开构造并集，必须注明各映射
  已经不相交。
- 禁止：用 `or`、字典展开或 `update()` 决定重复值，制造未声明优先级。
- 验收：重复字段返回明确 4xx，不重叠字段全部到达最终 consumer。

## SERV-4c — 入口接受必须闭环到每个生产消费者

- 触发：新增请求字段或改变字段分流。
- 强制：对每条 dispatcher 追踪字段到 engine、pipeline、prompt 或 sampling 参数。
- 禁止：用 helper 返回值或 HTTP 成功代替传播证明。
- 验收：真实请求对象同时覆盖默认值和非默认值，并断言最终 consumer。

## SERV-4d — 同一请求合同错误跨 dispatcher 保持同一响应合同

- 触发：同一非法输入可进入 diffusion-only、multi-stage 或其他多个 dispatcher。
- 强制：使用一致的 status、错误类型和消息策略，并在公共边界转换一次。
- 禁止：一路本地映射为 4xx，另一路交给远处通用 `ValueError` 捕获。
- 验收：同一冲突输入经过每条受影响 dispatcher 时响应等价，且都在 engine/pipeline
  调用前失败。

## SERV-4e — 请求期弃用信号必须对 operator 可见

- 触发：serving 路径继续接收 deprecated 输入。
- 强制：使用项目 logger 的 `warning_once` 或明确限频策略。
- 禁止：使用仅写 stderr 且按调用点过滤的 `warnings.warn`。
- 验收：合法旧输入恰好记录一次警告；因冲突返回 4xx 的输入不记录兼容警告；用户响应
  合同与日志合同分别断言。

## SERV-4f — Serving 只编译当前 slice 拥有的请求语义

- 触发：同一 serving 字段存在 flattened、nested、canonical 或 legacy 来源。
- 强制：在 request mutation、preprocess 和 dispatcher 分支之前完成一次来源校验，并
  产出当前 slice 限定字段的 consumer view。
- 禁止：dispatcher 重读 raw request 或重新决定优先级；为了 request-extra
  normalization 把 topology、模型能力、逐 stage 参数或其他 owner 吸进完整 compiler。
- 验收：root control + nested extras 分别经过 pure/mixed dispatcher 到达 prompt、
  AR metadata 与 diffusion sampling consumer；registry 字段与 service control 重名时
  仍只有一个 owner。

## SERV-4g — 多来源合同编码前必须完成来源矩阵

- 触发：一个语义存在多个来源、dispatcher 或 stage scope。
- 强制：按 [source-consumer decision matrix](../../../../general/review/guides/review-execution-contract.md#source-consumer-decision-matrix)
  标明路由、重复拒绝、不适用和 defaults；兼容写法默认进入同一 consumer scope，只有
  矩阵声明不同语义时才能分流。规范化结果拆成多个 consumer view 时默认互不重叠，
  同一字段确需进入多个 view 时逐一命名最终 consumer。
- 禁止：矩阵缺失时声称实现或审查完成；由字段集合运算、输入写法或 dispatcher 末端
  defaults 隐式决定 scope。
- 验收：每个来源组合都有明确 decision 和生产路径证据；每个 consumer view 的重叠项
  都有显式最终 consumer，不存在接受后丢弃或末端重新读取 raw request。

## SERV-4h — 请求合同膨胀时停止逐评论修补

- 触发：生产 diff 超过预算上限 1.5 倍、出现第二个重叠语义 owner，或下一审查波次
  再次发现同一 owner 漏洞。
- 强制：执行 [架构重置验收](../../../../general/review/guides/code-taste.md#架构重置怎样验收)，
  重新确认唯一最终产物、删除清单和规模上限。
- 禁止：继续堆 helper、compatibility branch 或 reviewer-specific patch。
- 验收：恢复编码前 owner、consumer、删除项和 diff 预算都有可检查记录。

## SERV-4l — request-level LoRA 必须贯穿每种 stage-0 submission 形态

- 触发：修改 chat adapter 解析、`AsyncOmni.generate`、ordinary/streaming request submission、
  stage-0 input processing 或 LoRA request 类型。
- 强制：OpenAI chat `_maybe_get_adapters()` 得到的同一个 request-level `LoRARequest` 必须传入
  `AsyncOmni.generate`，再贯穿普通 `add_request_async`、streaming 首 chunk、每个
  `add_streaming_update_async` 与无 chunk/final marker，最终由
  `AsyncOmniEngine._build_add_request_message` 传给**非 diffusion stage 0** 的 vLLM input
  processor。`None` 同样原样传播，不能复用上一请求 adapter。
- 禁止：只修非流式提交；把单个 request-level LoRA 广播成每 stage adapter；绕过既有
  `resolve_sampling_params_list` 的 stage cardinality 校验；以 adapter 已加载证明 request 已选择
  它。该参数在 target 的 engine APIs 仍标作 `Any`，不是类型安全合同；评审明确要求收窄类型，
  后续应统一为 `LoRARequest | None` 而非继续扩散 `Any`。
- 验收：用 identity sentinel 分别覆盖普通 prompt、streaming 有 chunk、streaming 空输入/final
  marker 与 `None`；单 stage sampling 参数包成长度 1，多 stage 参数长度必须等于 stage 数。
  断言 stage-0 input processor 收到同一对象，并另外验证 downstream stage 的 LoRA 仍由对应
  `sampling_params_list[i].lora_request` 拥有，默认参数对象不被污染。GPU 验收必须先确认 adapter
  ID 已加载，再证明 deterministic token/logprob 与 base 不同；#5369 另报的 `AsyncOmni.add_lora`
  control-RPC 反序列化成 list 问题不在本修复范围。^[PR #5374]

## SERV-4m — API server 必须规范化 CLI 参数并同步 positional model

- 触发：修改 `vllm_omni.entrypoints.openai.api_server` 的 CLI parser、模型参数来源或直接运行入口。
- 强制：直接运行 API server 时复用 upstream `FlexibleArgumentParser`，使下划线参数与连字符参数保持一致的规范化行为；解析后若 `args.model_tag` 非空，必须将 `args.model` 同步为该值，以确保 positional model 不会退回 vLLM `ModelConfig` 的默认模型。
- 禁止：使用不支持 upstream flag normalization 的独立 argparse parser；仅在 `args.model` 缺失时反向填充 `model_tag`，导致 positional model 仍未传入实际 model consumer；把 `--omni` 的兼容占位参数解释为改变直接入口运行模式的开关。
- 验收：分别验证 positional model、`--model`、`--gpu_memory_utilization` 等下划线参数和连字符参数均可解析，并断言 `args.model` 与 `args.model_tag` 一致且服务加载请求模型，不会回退到默认 LLM。^[PR #3805]

engine 生命周期见 [engine 生命周期规则](rules-engine-lifecycle.md)；故障隔离见 [fault isolation 规则](rules-fault-isolation.md)。

## SERV-4n — Omni Chat Completions 的 prompt token details 必须保留零值与多模态计数

- 触发：修改 Omni Chat Completions 的 streaming/non-streaming usage 序列化、`prompt_tokens_details`、prefix-cache 统计或多模态 token 计数传播。
- 强制：启用 `enable_prompt_tokens_details` 时，streaming 与 non-streaming 路径都必须复用 upstream 的 prompt-token-details helper，传递 engine prompt 的 multimodal token counts，并保留 `cached_tokens` 为 `0` 的详情对象；未启用时不得为此执行额外计数。
- 禁止：用 truthiness 判断 `num_cached_tokens` 而丢弃零值；只在一种响应模式填充详情；丢弃 `multimodal_tokens` 或以不同逻辑分别构造两种 usage；将该响应合同混同为 Prometheus 指标合同。
- 验收：分别覆盖 streaming 与 non-streaming、`cached_tokens=0` 及非零值、image/audio 多模态计数和详情开关关闭场景，断言响应字段一致、计数准确且关闭时不产生详情。^[PR #5181]

## SERV-4o — pipeline sampling constraints 必须在 caller 参数上重建并优先

- 触发：修改 `OmniBase.resolve_sampling_params_list()`、stage runtime config、pipeline `sampling_constraints`，或让 caller 提供单/多 stage sampling params。
- 强制：从每个 runtime stage config 取得约束并与同 stage caller params 合并；pipeline-required key 覆盖 caller 冲突值，其他 caller fields 保留。对 mapping 复制合并；对 dataclass/msgspec sampling object 以合并值重建，使 constructor/post-init 重新计算 stop-token 等 derived state，且 caller/default object 保持不变。
- 禁止：caller 提供 params 时整包替换 pipeline constraints；只从 dataclass 而不是实际 OmegaConf runtime config 读取；对已构造 `SamplingParams` setattr/copy 后跳过 derived-state 更新，或静默以 caller 值赢得 pipeline-required field。
- 验收：真实 stage config conversion 覆盖单与多 stage、normal caller field、pipeline-required `detokenize`/stop token conflict、derived stop-token state 及 caller immutability；默认 params 与无约束 control 保持既有行为。^[PR #6182]

## SERV-4p — 可序列化整数必须在协议层限界且 dispatch 保底

- 触发：公开 OpenAI 请求模型新增/修改整数参数，或请求会跨 stage 以 msgpack 传输的 sampling、extra 或嵌套参数。
- 强制：能在协议模型明确归属的整数必须以有符号 64 位范围校验；计数/尺寸/steps/token fields 保留既有正数或非负下界，seed 可使用完整 `[-2**63, 2**63-1]` 范围。协议拒绝应保留 Pydantic 的字段定位 validation 4xx。所有 stage dispatch 边界仍须将 payload 的 `OverflowError` 转为仅该 request 的非 fatal 400，并经共享 cleanup abort 全部 stage/CFG 状态，orchestrator 继续服务。
- 禁止：只靠 protocol allowlist 防御嵌套或 extra 参数；把 overflow 作为 engine-wide fatal；捕获无关异常来掩盖程序错误；为统一范围而丢失原有业务下界。
- 验收：覆盖明确字段的越界 validation（含 speech token/seed 边界）和 mock dispatch 序列化 overflow；后者断言 400、request state 已清理、thread 仍存活。每个修改的公开整数字段须覆盖合法边界与非法一侧。^[PR #6598]
- 边界与未合入建议：目标只捕获 `OverflowError`，不证明其他序列化失败的可恢复性。PR merge 后仍有两个未 resolve review threads：三个 protocol 文件重复定义 int64 constants，且负 TTS seed 的用户可见放宽未写入 PR body；前者是去重建议，后者可由 merged code/tests 与提交历史确认，但两者都不是本提交新增的 shared-constant 或 release-note 合同。

## SERV-4q — Stage-0 prompt transform 必须保留 downstream 原始视图并闭合临时 artifact 生命周期

- 触发：pipeline 用 `prompt_transform_func` 为 Stage 0 重写 prompt/media，同时 downstream stage 仍需原始请求，或 transform 创建 request-scoped 临时目录。
- 强制：transform 只操作 Stage-0 copy；原始 prompt 保留给 downstream，并在 transform 前后保持同一 global request ID。只把已处理的 metadata 合并回原始视图，先移除 transform-owned stale keys。临时目录只通过内部 `REQUEST_ARTIFACT_DIRS_KEY` 交给 request state；preprocess、companion build、enqueue 前失败立即回收，admit 后由 orchestrator 在所有 terminal cleanup 路径回收，且内部 key 不得进入 stage payload。
- 禁止：把 transformed prompt 当作 downstream 原始媒体、让旧 prepared descriptor 跨请求复用、在 ownership 已交给 orchestrator 后由 frontend 提前删除，或让异常路径泄漏转码目录。
- 验收：覆盖 transform replacement/copy、request ID 与 metadata merge、成功 terminal/abort、preprocess/companion/enqueue 异常以及无 artifact control；断言 downstream 看见原始媒体+允许的 processed meta，目录恰好由当前 owner 回收，内部 key 未传输。^[PR #5885]

## SERV-4r — video 参考图必须在 RGB 转换前执行像素上限并映射解码器炸弹

- 触发：修改 `/v1/videos` 的 `image_reference` / `input_reference(s)`、MiniMax H3 multipart 图片上传，或 `video_api_utils._decode_image_bytes` / `_validate_image_pixel_limit`。
- 强制：`Image.open` 后、`convert("RGB")` 前按 header 尺寸检查 `width * height`；当 `VLLM_MAX_IMAGE_PIXELS > 0` 且超出时拒绝。`=0` 禁用检查，恰等于上限放行。Pillow `DecompressionBombError` 必须映射为专用像素上限 client error（HTTP 400），不得落入泛化 “not a valid image” 后再当 video 重试。H3 multipart 与共享 decode helper 共用同一合同。
- 禁止：先全量 decode/convert 再检像素；把 decoder bomb 误判为可 video-fallback 的无效图；用 500 或静默接受放大资源占用。
- 验收：覆盖超限在 convert 前失败、disabled/inclusive 边界、bomb→专用 400、以及 H3 multipart 字段拒绝。^[PR #6963]

## SERV-4r2 — `/v1/audio/generate` 必须在协议层拒绝空 prompt 与越界采样字段

- 触发：修改 `OpenAICreateAudioGenerateRequest`、audio generate invalid-param 可靠性测试，或该入口的 prompt/采样字段限界。
- 强制：`input` 以 field validator 拒绝空串与纯空白；`audio_length` 要求 `gt=0`；`guidance_scale` 限界 `ge=0, le=1000`；`num_inference_steps` 限界 `ge=1, le=1000`。非法值必须在 entrypoint Pydantic 校验失败，不得拖到 engine 超时或 HTTP 200。
- 禁止：依赖 engine-level 检查代替协议拒绝；把越界 steps/guidance 留在 `_INT64_MAX` 一类无业务上界；用 skip mark 掩盖未接线的 invalid-param case。
- 验收：空/空白 input、负/零 `audio_length`、负/过大 guidance、零/负/过大 steps 均返回字段定位的 4xx，并与 invalid-param 测试期望一致。^[PR #4741]

## SERV-4r3 — `vllm serve --omni` 必须在校验期要求显式 model

- 触发：修改 `OmniServeCommand.validate`、`--omni` 启动路径、`model`/`model_tag`/`explicit_keys`，或部署 YAML 与 checkpoint 来源关系。
- 强制：`--omni` 下 model 只能来自非空 positional `model_tag`，或出现在 `explicit_keys` 中的非空 `--model`。`--deploy-config` / stage YAML 只携带 per-stage engine args，checkpoint 始终由 `args.model` 注入，不得凭 YAML 存在判定“已提供 model”。空/空白 model 视为未提供，并在 validate 期以明确 `ValueError` 失败。
- 禁止：依赖 vLLM `ModelConfig` 默认 `Qwen/Qwen3-0.6B` 进入 Omni/diffusion 路由；把默认模型缺失伪装成深层 diffusion-registry `Model class … not found`；让仅 `--deploy-config` 或空 `--model "$MODEL"` 绕过守卫。
- 验收：`["serve","--omni"]`、仅 deploy-config、空/空白 positional/`--model` 均 raise “requires an explicit model”；positional、`--model`、以及显式 model+deploy-config 不得触发该守卫。^[PR #4167]

## SERV-4r4 — 图片 generations 与 edits 的 `output_compression` 必须同一闭环

- 触发：修改 `/v1/images/generations` 或 edits 的协议字段、handler 到 `encode_image_base64_with_compression` 的转发。
- 强制：`ImageGenerationRequest` 声明 `output_compression`（0–100，默认 100）并原样传入 encoder；PNG 映射为 compress_level（100→0，1→9），jpeg/webp 映射为 quality。缺省字节合同与 edits 一致。
- 禁止：只在 edits/`Form` 接受该字段而 generations 静默丢弃；用 HTTP 200 或非默认 format 冒充 compression 已生效。
- 验收：L1 断言 PNG 100/1 与等价 compress_level 同大小且 1 更小，JPEG 高低 compression 体积方向正确；handler 用非默认值断言 encoder kwargs。^[PR #7447]

## SERV-4s — 内存中的 image `file` 响应必须按固定块异步产出

- 触发：修改 `ImageGenerationResponse.stream_response`、`response_format=file`，或把已物化 PNG/ZIP 交给 Starlette `StreamingResponse`。
- 强制：对已在内存中的单图/ZIP 使用异步迭代器按固定块（如 64 KiB）`memoryview` 切片产出；保留既有 headers/`Content-Length` 与完整 body 字节。
- 禁止：把 `io.BytesIO` 直接交给 `StreamingResponse`（按行/`0x0A` 切分且同步 iterable 会触发 per-fragment threadpool）；为“流式”再无意义地按换行拆二进制。
- 验收：构造含多处 `0x0A` 的 PNG/ZIP，断言 ASGI body 哈希不变、非空 frame 数约为 `ceil(size/chunk)` 而非 newline 次数。^[PR #7459]

## SERV-4r5 — pipeline 要求的 `stop_token_ids` 必须与 caller/deploy 停止集相加去重

- 触发：修改 `merge_sampling_constraints`、`OmniBase._apply_sampling_constraints`、pipeline `sampling_constraints.stop_token_ids`，或 deploy `default_sampling_params.stop_token_ids`。
- 强制：标量约束仍由 pipeline 覆盖同名 caller/deploy 字段；惟 `stop_token_ids` 例外——先取 caller/deploy 列表，再追加 pipeline 要求的 ID，并以 `dict.fromkeys` 保序去重。legacy `yaml_extras` 与 structured config、以及 request 期重建 `SamplingParams`，必须共用同一 merge helper，且不 mutate 调用方对象。
- 禁止：用整表 `constraints` 覆盖把 caller 自定义 stop 抹掉；只在 YAML merge 或只在 request apply 一侧实现相加；或让模型必需 terminator（如 MiniCPM-o TTS 边界）依赖重复 YAML/环境变量拷贝。
- 验收：覆盖 deploy 已有 stop + pipeline 新增 stop 的并集、caller mapping/dataclass/msgspec 重建、immutability，以及至少一条真实 pipeline 的 Stage-0 必需 stop 进入全部 shipping deploy。^[PR #7463]

## SERV-4i2 — multipart artifact 在 I/O 前验合同、在所有终态释放

- 触发：公开请求接收一个或多个 `UploadFile`、URL media，或把输入物化后交给后台任务。
- 强制：在 read/download/persist/decode 前完成 dispatcher、模型 capability 与
  source/task matrix 校验；流式执行 count、per-file 和 aggregate byte 上限，超限返回
  413；只清理由当前请求创建的 artifact，并保留输入顺序直到最终 consumer 完成。
- 禁止：把无限 multipart 先复制到临时目录再校验；让非法组合进入 engine 后变成 sync
  500 或 async failed job；只在成功路径或 audio 分支 cleanup。
- 验收：sync/async 都覆盖冲突 400、超限中途 413、setup 失败、generation 失败、timeout、
  cancellation、missing-job/early-return 与成功；无效请求未调用持久化或 engine，所有已创建
  路径在每个终态消失，用户提供的非 owned 路径不被删除。MiniMax H3 的当前矩阵见
  [MiniMax H3 media 规则](../../models/minimax-h3/rules-media.md)。 ^[PR #5691]
