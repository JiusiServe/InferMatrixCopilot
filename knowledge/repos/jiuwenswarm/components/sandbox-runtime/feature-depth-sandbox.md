---
title: "JiuwenBox 隔离执行：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L405-L528, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/cli/jiuwenbox.py:L302-L319, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L153-L204, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenbox/src/jiuwenbox/server/app.py:L44-L59]
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
