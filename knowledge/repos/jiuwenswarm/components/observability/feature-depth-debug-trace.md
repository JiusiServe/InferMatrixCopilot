---
title: "Debug Dump 与 OTel：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L304-L316, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L556-L568, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L71-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L293-L302, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L21-L28]
feature: "debug-trace"
entry_points: ["jiuwenswarm/server/runtime/debug_trace/config.py", "jiuwenswarm/server/runtime/debug_trace/stream_logger.py"]
source_globs: ["jiuwenswarm/server/runtime/debug_trace/config.py", "jiuwenswarm/server/runtime/debug_trace/stream_logger.py", "jiuwenswarm/server/runtime/debug_trace/*.py"]
---

# Debug Dump 与 OTel：实现深读

[功能概览](feature-debug-trace.md) · [owner 入口](_index.md)

<!-- kb:depth feature=debug-trace facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=213bea8b51a64fb5e3c2331bc06f6411ad66a7ac8a3aa47f1a9cfb9152c97a77 -->
**子代理开始边界写入 dump 的调用链**
以一次子代理派发为例：输入是 source 标签与 prompt。DebugTraceLogger.begin_subagent 先调用 _flush_run 把此前累积的主 run 文本刷出，再调用 _write_raw 写入 "========== subagent start ==========" 边界行（含 timestamp/source/prompt，prompt 按 generic_payload_max_chars 截断）；_write_raw 在写盘前对 body 做 _sanitize_log_text 脱敏并 flush 文件。整个调用链包在 try/except 中，异常经 _safe_warn 降级为警告，不向上抛。

调用路径：`jiuwenswarm/server/runtime/debug_trace/stream_logger.py`（`DebugTraceLogger.begin_subagent`） → `jiuwenswarm/server/runtime/debug_trace/stream_logger.py`（`DebugTraceLogger._write_raw`）

来源：[jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L304–L316](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L304-L316), [jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L556–L568](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L556-L568)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","start":304,"end":316,"sha256":"1446e03e927893cc9fb19c7c5df14eb0e370017f9fa8f83d331a0473aa05e3e1"},{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","start":556,"end":568,"sha256":"dbc5d18ca0504b57956a6e4a08e64de7911d372768605a21de006dc8e27822c5"}],"trace":[{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","symbol":"DebugTraceLogger.begin_subagent","start":304,"end":316},{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","symbol":"DebugTraceLogger._write_raw","start":556,"end":568}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=debug-trace facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e1e1e61c58f49286b1dc589638d05d77690ab9eae81fd0c07350ce0f57f35af6 -->
**resolve_debug_trace_settings 与 feed_subagent 的契约**
resolve_debug_trace_settings(*, mode: str, request_debug: bool) 是关键字-only 入口，每次调用都重新加载 debug_trace 配置块并返回 frozen 的 DebugTraceSettings；调用方义务是传入本 run 的模式与请求级 /debug 标志。DebugTraceLogger.feed_subagent(*, source, chunk) 在禁用或 include_subagent_flow 关闭时是静默 no-op，调用方无需先自行判断开关。

来源：[jiuwenswarm/server/runtime/debug_trace/config.py:L71–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L71-L79), [jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L293–L302](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L293-L302), [jiuwenswarm/server/runtime/debug_trace/config.py:L21–L28](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L21-L28)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/debug_trace/config.py","start":71,"end":79,"sha256":"927c8f24e871fe592a120b9e4a6837290e44c3f20ee0e7a19f1e42bcc13d71af"},{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","start":293,"end":302,"sha256":"f6a7ebb3d6b34f38331f990515ee075ae38d5bd0107d45c03909b01a2f435581"},{"path":"jiuwenswarm/server/runtime/debug_trace/config.py","start":21,"end":28,"sha256":"1b220816ebe15df693651b62254e7cc159694332b53e97b9dcc959b0d93ece59"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=debug-trace facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=23b22d3b0f20a7b793927a8570df7ee0faf9d4bd028c43c38b2e52a4c687429b -->
**在 _write_raw 统一脱敏兜底（推断）**
设计推断（非作者历史意图）：

推断：注释说明 trace 文件直接 file.write、不走 logging，主 SensitiveDataFilter 覆盖不到，因此在 _write_raw 这个所有写路径的汇聚点统一做 _sanitize_log_text（含 api_key/Bearer 及指纹）。收益是 _emit、run 边界、_safe_warn 等写入无需各自脱敏；代价是每行落盘前多一次扫描，且防护正确性完全依赖该单点与 _sanitize_log_text 的实现。

来源：[jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L556–L568](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L556-L568)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","start":556,"end":568,"sha256":"dbc5d18ca0504b57956a6e4a08e64de7911d372768605a21de006dc8e27822c5"}],"trace":[]} -->
<!-- /kb:depth -->
