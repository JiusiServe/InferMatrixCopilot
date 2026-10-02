---
title: "JiuwenBox 隔离执行：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L405-L528, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py:L302-L319, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L153-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L44-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L488-L490, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/README_CN.md:L565-L576, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/runtime/process.py:L3070-L3100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/runtime/process.py:L281-L286, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/runtime/process.py:L2280-L2319, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/tests/integration/test_server_api_default.py:L716-L728]
feature: "sandbox"
entry_points: ["jiuwenbox/src/jiuwenbox/server/app.py"]
source_globs: ["jiuwenbox/src/jiuwenbox/server/app.py", "jiuwenbox/src/jiuwenbox/*"]
---

# JiuwenBox 隔离执行：实现深读

[功能概览](feature-sandbox.md) · [owner 入口](_index.md)

<!-- kb:depth feature=sandbox facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2c6c219ff5c1b653cd408d7e12b19b4b3cb4922daf47ee834b1670bd31b4ec37 -->
**HTTP 错误映射契约**
create_app 注册异常处理器把领域异常映射为标准 JSON 错误响应：SandboxNotFoundError→404，SandboxStateError/SandboxConflictError→409，InvalidSandboxIdError/InvalidJobIdError/PolicyValidationError/ValidationError→400，BackgroundJobNotFoundError→404；调用方因此可用状态码区分不存在、状态冲突与请求非法。CLI 侧 _CliClient.sandbox_create 向 /api/v1/sandboxes POST 可选 env/policy/policy_mode/sandbox_id 并返回 dict。

来源：[jiuwenbox/src/jiuwenbox/server/app.py:L405–L528](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/app.py#L405-L528), [jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py:L302–L319](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py#L302-L319)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenbox/src/jiuwenbox/server/app.py","start":405,"end":528,"sha256":"2af69c1156eb3c0c8d9a05e75c5caf2beb9e628ddeb0cfaf2201efc1d4fb43f3"},{"path":"jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py","start":302,"end":319,"sha256":"547307a059c4d2f9dc1e155ff5b606a12460191981d39c46e3d93613fe368bbc"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a4849432cea821d23e44e625cf84231538e022c353113b317a01dbdb63db0e2 -->
**JIUWENBOX_SAVE_LOGS_DIR 与健康响应体**
JIUWENBOX_SAVE_LOGS_DIR 默认未设置即完全不写日志文件（仅 DEBUG 级审计事件）；设置后 _build_sandbox_manager 用该目录（expanduser + mkdir）构造 AuditLogger(log_dir=..., filename_strategy="timestamped")，文件在沙箱销毁后保留。JIUWENBOX_HEALTH_RESPONSE_BODY 非空时 /health 以 text/plain 200 原样返回该值，空串视为未设置，且按请求读取。

来源：[jiuwenbox/src/jiuwenbox/server/app.py:L153–L204](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/app.py#L153-L204), [jiuwenbox/src/jiuwenbox/server/app.py:L44–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/app.py#L44-L59)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenbox/src/jiuwenbox/server/app.py","start":153,"end":204,"sha256":"d0d08b92bc13a98c299e907830cc0a0a1b89af67f60ccda7a47fb898396d7340"},{"path":"jiuwenbox/src/jiuwenbox/server/app.py","start":44,"end":59,"sha256":"4e3d4718bf34bffbc6cee53b1f57f8e8e0df751c0e3917af767a4d3dd001c8e9"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=890ec755376ba8da1a59656fdd66efef29ecb981ab49b2808aba9ace0ccd21a8 -->
**ProcessRuntime.exec：信号量约束内经 _exec_via_daemon 执行**
exec(sandbox_id, request) 先记命令摘要日志，经 `_ensure_exec_semaphore()` 取信号量，在 `async with semaphore` 内 `await self._exec_via_daemon(sandbox_id, request)` 并返回其 ExecResult；文档字符串称命令经每沙箱常驻 daemon 的 Unix socket 单次往返执行，在飞命令数受 JIUWENBOX_EXEC_CONCURRENCY（默认可用 CPU 数）约束。

来源：[jiuwenbox/src/jiuwenbox/server/runtime/process.py:L3070–L3100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/runtime/process.py#L3070-L3100)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":3100,"path":"jiuwenbox/src/jiuwenbox/server/runtime/process.py","sha256":"75c572aee3171d1fa748c8d429e8a50d1275097a8f3466813b00071b7cbc22fc","start":3070}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5fef6f17f7e9e0552474460fb407876b9615a6cb9be4a2bbd4c0dc7b8ccc1ea1 -->
**create_app 内联导入 sandbox/policy/proxy 三个 router；jiuwenswarm 侧 sandbox.type 当前仅接通 jiuwenbox（文档表述）**
create_app() 内联导入 routes.sandbox / routes.policy / routes.proxy 三个 router 模块，server 的 API 面依赖这三处路由代码；jiuwenswarm 配置项 sandbox.type 默认 jiuwenbox，文档称当前只接通该 provider。

来源：[jiuwenbox/src/jiuwenbox/server/app.py:L488–L490](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/app.py#L488-L490), [jiuwenbox/README_CN.md:L565–L576](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/README_CN.md#L565-L576)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":490,"path":"jiuwenbox/src/jiuwenbox/server/app.py","sha256":"099408135b894dd0809e69217db15adef8dea5c1d1ea23c5f590965aadecd445","start":488},{"end":576,"path":"jiuwenbox/README_CN.md","sha256":"8e2e83e70f7ff3d15475929dd0dd0a1cbb8e46e0b252b69111441d58155695c3","start":565}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=45fd5dc1d9c4a77909324aef03e201de0f01c5ec0d962d0a7ff7ee14aec2e217 -->
**ProcessRuntime.stop 在守护进程等待超时后向进程组发 SIGTERM；killpg 遇 ProcessLookupError 则清理并返回**
当 proc.wait 超过 DAEMON_SHUTDOWN_TIMEOUT_SECONDS 时，stop 调用 os.killpg(proc.pid, SIGTERM)；若抛出 ProcessLookupError，则弹出 _processes 与 _daemon_socket_ready 表项、移除主机防火墙规则、拆除 cgroup 后 return。

来源：[jiuwenbox/src/jiuwenbox/server/runtime/process.py:L2280–L2319](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/runtime/process.py#L2280-L2319)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2319,"path":"jiuwenbox/src/jiuwenbox/server/runtime/process.py","sha256":"6ce92e35aadf80e17000558ffe16eccce38b2ac51de131d9159e16e19a00e537","start":2280}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ac58f17059e21c82bd717f98af6de6d4f3a004905199e6b8dc01d5626a25027 -->
**DAEMON_STARTUP_LOG_MAX_BYTES=16KiB：启动失败 RuntimeError 有界（注释）vs 超出诊断截断（推断）**
设计推断（非作者历史意图）：

该 16*1024 上限约束计入 supervisor 早退 RuntimeError 的 spawn 期 stdout/stderr：注释称可容纳 traceback 加少量 bwrap/seccomp/landlock 诊断、对经 HTTP 透出的调用方保持有界；代价是超出 16KiB 的诊断丢失（推断）。

来源：[jiuwenbox/src/jiuwenbox/server/runtime/process.py:L281–L286](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/src/jiuwenbox/server/runtime/process.py#L281-L286)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":286,"path":"jiuwenbox/src/jiuwenbox/server/runtime/process.py","sha256":"341d0d24badd5b85b2b4957ed109ced97452ca02f09d351488277ed7756c7b3a","start":281}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=sandbox facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f6ca7d804f1d9d3282426ae9f35eaacb9d8bd29d609aa8cc38314f490714843f -->
**集成测试断言 POST /api/v1/sandboxes 返回 201 且 phase 为 ready**
test_sandbox_process_cannot_inspect_sandbox_daemon_memory 经 client fixture 发起 POST /api/v1/sandboxes，断言 status_code == 201 且 sandbox['phase'] == 'ready'；所示行止于取出 sandbox_id，后续探测断言未在所示范围内。

来源：[jiuwenbox/tests/integration/test_server_api_default.py:L716–L728](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/tests/integration/test_server_api_default.py#L716-L728)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":728,"path":"jiuwenbox/tests/integration/test_server_api_default.py","sha256":"8d3ec3a66131b2539e9dad983c5b4d1a8093d676c1b17f772e2d7e8c2f8dd302","start":716}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
