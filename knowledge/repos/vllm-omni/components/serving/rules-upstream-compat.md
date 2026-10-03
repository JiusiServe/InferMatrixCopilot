---
title: "Serving upstream 兼容规则"
created: 2026-09-02
updated: 2026-09-22
type: rule
tags: [vllm-omni, components, serving]
sources: ["PR #5976", "PR #5957", vllm_omni/engine/stage_engine_startup.py, vllm_omni/entrypoints/openai/api_server.py, vllm_omni/entrypoints/utils.py, vllm_omni/request.py, tests/engine/test_stage_engine_startup_cache_env.py, tests/config/test_endpoint_policy.py, "PR #5036", "PR #6642", "PR #6773", "PR #6707", vllm_omni/config/endpoint_policy.py, "PR #6051", "PR #7426", "PR #5647"]
confidence: high
---

# Serving upstream 兼容规则

## SERV-7a — upstream launcher 生命周期兼容必须保持模式检测语义

- 触发：upstream launcher、renderer warmup 或 shutdown 读取的 engine-client 属性变化。
- 强制：pure-diffusion client 只在 launcher-facing `vllm_config.shutdown_timeout` 上提供最小 adapter，
  其余属性透明转发，内部 `get_vllm_config()` 仍返回 `None`；chat template warmup 调用 upstream 当前
  owner `online_renderer`。多 replica spawn 时 replica 0 复用默认 compile cache，后续 replica 在持锁
  的 spawn env 中获得 stage/replica 唯一 `VLLM_CACHE_ROOT`，离开 scope 必须恢复环境。
- 禁止：让 adapter 改变 pure-diffusion detection；调用已删除的 serving-chat warmup；所有 replica
  共写 AOT cache，或永久污染父进程环境。
- 验收：pure diffusion 正常 shutdown 且 detection 不变；renderer 恰好 warmup；cache-env 测试覆盖
  replica 0、多个 stage/replica、嵌套恢复和异常恢复。^[PR #5976]

## SERV-7b — 加速器镜像落后一版时兼容层必须按能力探测

- 触发：CUDA 主线升级 vLLM 后，XPU/NPU 等镜像仍使用前一版 renderer、tool parser
  import 或 request layout。
- 强制：可选 renderer warmup 用属性能力探测；Mistral tool-call parser 只在新 import 不存在时
  回退旧路径；`OmniRequest` 仅为缺失的 `num_stale_output_tokens` 提供零初值，
  不覆写新版 owner 已有的值。
- 禁止：用 platform name 猜测 API；为兼容旧版跳过新版必需初始化；将临时 shim 宣称为
  长期 public API。
- 验收：新/旧 renderer、两条 Mistral import 和有/无 stale counter 的 request layout 都能初始化，
  且新版既有 counter 原值不变。^[PR #5957]

## SERV-7c — 对象存储 URI 必须在 serving 入口绕过预下载

- 触发：修改 `omni_snapshot_download()` 或入口侧模型解析，使其处理 Run:AI 对象存储 URI、HF repo id 和本地模型路径。
- 强制：使用上游 `is_runai_obj_uri` 作为唯一对象存储判断，在 Hugging Face/ModelScope 预下载前原样返回对象存储 URI；本地路径与普通 HF repo id 保持既有分支，并将后续配置读取交给配置层的本地物化逻辑。
- 禁止：维护与 vLLM streamer 分离的本地 scheme allowlist；将对象存储 URI 当作 HF repo id 下载；让 bucket 或组织路径段参与模型名称匹配。
- 验收：参数化 mock 测试覆盖 `s3://`、`gs://` 及上游支持的 `az://`，断言 HF 下载未调用且返回值未改变；同时覆盖本地路径、HF repo id 和欺骗性 bucket/组织段匹配，确认入口语义没有回归。resolved HF cache snapshot 的 repo-name recovery 已随 #6642 的 revert 不再是当前合同。^[PR #5036] ^[PR #6642]

## SERV-7d — error-response import 必须遵循各 caller 的已验证 owner

- 触发：pinned vLLM 移动 `create_error_response`，或 endpoint policy / API server 增加直接 caller。
- 强制：`endpoint_policy.py` 直接从 pinned owner
  `vllm.entrypoints.serve.exception_handling.error_response` 导入 `create_error_response`，不设 fallback；
  `api_server.py` 则先从 package root `vllm.entrypoints.serve` 导入，只在 `ImportError` 时回退
  `vllm.entrypoints.serve.utils.error_response`。这是两个 caller 各自的 source-authoritative 合同，
  不要求共享 fallback 顺序。
- 禁止：把 endpoint-policy 的直接模块 import 改回 package-root fallback；捕获任意 `Exception` 伪装
  成兼容；或以这两个 import 成功声称跨版本 API/JSON parity。
- 验收：在此 pinned revision，直接导入 relocated module，并运行
  `tests/config/test_endpoint_policy.py`；API-server 路径仍仅为其 `ImportError` fallback 的静态合同。
  PR 描述报告该 suite `4 passed`，批准 review 的边界是 static review、merge tree 与 CI，且明确未执行
  untrusted fork code；因此不能扩展为完整 vLLM 版本兼容或端到端声明。^[PR #6707, merged 2026-09-02]

## SERV-7f — OpenPI `nd` 标记必须同时接受 vLLM-native 与 msgpack-numpy 的 `kind`

- 触发：修改 `entrypoints/openpi/connection.py` 的 `_decode_vllm_numpy_marker` / `_unpack_numpy`，或 OpenPI/DreamZero 观测 payload 解码。
- 强制：`kind` 仍为区分 array marker 与普通 mapping 的必填字段。plain ndarray 的 `kind` 接受 `""`（msgpack-numpy 包）或 dtype kind 字符（vLLM-native）；二者任一匹配即通过。`kind == "V"`（structured）必须在调用 `np.dtype(type)` 之前拒绝，因该方言的 `type` 是 descriptor list。outbound 仍发 openpi-client 标记。
- 禁止：要求 `kind == dtype.kind` 而拒绝空 kind；对 structured marker 让 `np.dtype` 抛出不透明 `TypeError`；把 msgpack-numpy **标量**（可省略 `kind`）误当成必须解码的 ndarray marker。
- 验收：分别覆盖 vLLM-native `kind`、手写 `kind=b""`、真实 `msgpack_numpy.packb` 观测 round-trip、structured `kind=V` 拒绝，以及无 `kind` 的用户 dict 原样保留。^[PR #6051]

## SERV-7e — realtime/video-stream 音频事件必须使用 `response.output_audio.*`

- 触发：修改 realtime WebSocket、video stream serving、示例客户端或协议文档中的音频 delta/done 事件名。
- 强制：服务端发出的增量与终态音频事件类型必须是 `response.output_audio.delta` / `response.output_audio.done`（及配套 transcript 命名），与已迁移的 OpenAI realtime 合同一致；示例与测试断言同一集合。
- 禁止：在任一生产发送路径残留 legacy `response.audio.delta` / `response.audio.done`；只改文档/示例而漏改 `realtime_connection` 或 `serving_video_stream`/`video_stream_base`。
- 验收：duplex/realtime/video-stream 测试收集到的音频事件类型集合等于 `response.output_audio.*`，且不接受仅 legacy 名作为成功合同。^[PR #7426]

## SERV-7g — 公开 serve 入口退役必须在所有 producer 上 fail closed

- 触发：删除或改名 serve CLI option、wrapper/chart key 或公开配置文件入口。
- 强制：parser、headless builder、脚本、chart、测试和公开 serving 文档在同一批迁移到
  canonical replacement；已删除的外部 key 必须显式拒绝并给出迁移目标。当前 serve
  部署 YAML 的唯一公开 flag 是 `--deploy-config`。
- 禁止：删除是有意 breaking change 时又加静默 alias/fallback；wrapper 接受但忽略旧值；
  留下仍会发出旧 flag 的可运行命令。
- 验收：replacement 可解析且到达最终 consumer，旧 option parser 失败；standard/headless
  发出同一 canonical 值，wrapper/chart 同时有正向与旧 key 拒绝测试，公开 serve 调用扫描
  不再命中退役 flag。 ^[PR #5647]

## SERV-7h — 兼容性按 ingress 分类，不能按同名 symbol 推断

- 触发：公开 CLI 已移除，但 Python/direct API、offline example 或 resolver 仍保留同名字段。
- 强制：分别列出 public CLI、wrapper/chart、offline example、Python/direct 和内部 resolver；
  public 行为由 Serving owner 决定，仍保留的 loader/schema 语义交给
  [Configuration rules](../configuration/rules.md) 并记录明确 follow-up 边界。
- 禁止：因为仓库仍出现 `stage_configs_path` 就恢复公开 serve flag；也不能因为 public parser
  已删除就宣称所有内部兼容路径已移除。
- 验收：公开 rejection 与 canonical forwarding 测试通过；每个暂留内部/direct 路径有独立
  compatibility test，直到后续迁移显式删除。 ^[PR #5647]

## SERV-7i — Speech 错误响应不得依赖 Request 上的 tokenization instrumentator

- 触发：修改 `_create_speech_error_json_response`、voice list/upload/delete 路由，或 diffusion TTS 在 `serving_tokenization is None` 时的错误路径。
- 强制：使用 upstream 独立的 `create_error_response` 构造 `ErrorResponse`，helper 不再要求 `raw_request` / `base(raw_request)`。无 Speech handler、校验失败与内部错误仍返回既有 OpenAI JSON 与状态码，不因缺 tokenization 升级为 500。
- 禁止：在单测里 mock 掉 `base()` 从而掩盖生产路径对 instrumentator 的依赖；让 diffusion TTS voice 错误在无 tokenization 时落到未捕获异常。
- 验收：构造 `app.state.serving_tokenization=None` 的真实 Request，覆盖 list/upload/delete 的 404/400/校验路径，断言 JSON error shape 且非 500。^[PR #7798]
