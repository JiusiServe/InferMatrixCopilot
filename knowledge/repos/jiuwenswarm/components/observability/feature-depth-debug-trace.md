---
title: "Debug Dump 与 OTel：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L304-L316, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L556-L568, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L71-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L293-L302, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L21-L28, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_debug_trace.py:L692-L701, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L58-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L71-L95, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L47-L55, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/config.py:L76-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L240-L249, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L378-L380]
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

<!-- kb:depth feature=debug-trace facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d7d02dde8ea5da6062d278099efac9055b9db9161a06316e536c011cc23bd85 -->
**resolve_debug_trace_settings 内的 debug/dump/otel 判定（仅本函数）**
mode 以 code 前缀取 debug_trace.code，否则取 agent 块；debug_enabled = request_debug 或该块 enabled；dump_enabled 在其下默认开、仅当值恰为 False 才关；otel_enabled 还需该块 otel_enabled（默认 False）——已为 true 的 agent_observability 由 sync_agent_observability 处理，不在此函数。

来源：[jiuwenswarm/server/runtime/debug_trace/config.py:L58–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L58-L59), [jiuwenswarm/server/runtime/debug_trace/config.py:L71–L95](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L71-L95)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":59,"path":"jiuwenswarm/server/runtime/debug_trace/config.py","sha256":"3f270c18e16c69eda9ea3d759eae769258c79ba680af1e2c94958e68e84de524","start":58},{"end":95,"path":"jiuwenswarm/server/runtime/debug_trace/config.py","sha256":"127f3d5d2f3d7a112b45c6b880b7ee6c692e5a3aa3ec14d5d19028391f49a1f1","start":71}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=debug-trace facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c3f07ce19ac12ae2d945f52dec6610a31c5c3c4a2c0dd96d6125a832b597fc47 -->
**_load_debug_trace_config 对 jiuwenswarm.common.config 的尽力读取**
函数体内延迟 import common.config.get_config 来读 debug_trace 块；任何异常或非 dict 值都返回 {}，随后 resolve_debug_trace_settings 把 mode/limits/redaction 三个块当空 dict 继续计算。

来源：[jiuwenswarm/server/runtime/debug_trace/config.py:L47–L55](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L47-L55), [jiuwenswarm/server/runtime/debug_trace/config.py:L76–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/config.py#L76-L85)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":55,"path":"jiuwenswarm/server/runtime/debug_trace/config.py","sha256":"5fe96bcfb7fe943672893d250dc1e95929ea624d08a38605f182f0bd5f6589e0","start":47},{"end":85,"path":"jiuwenswarm/server/runtime/debug_trace/config.py","sha256":"11c30da1c583e077ccd107c890306b6153b84eda2f57bec1aa7044b5971a748b","start":76}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=debug-trace facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=804dcfbfc32bc184023a39f7da3c046b5e8e7c207eed4f290df01b79e027b2a2 -->
**dump 文件 mkdir/open 失败仅禁用当前 DebugTraceLogger 实例**
init 这段 try 中 mkdir/open 抛异常即被 except 捕获：记 '[DebugTrace] disabled ... open failed' 警告并置 _disabled=True；此后 flush() 命中 _disabled 守卫直接 return，feed_subagent() 在 _disabled（或 include_subagent_flow 关闭）时同样 no-op 不写文件。

来源：[jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L240–L249](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L240-L249), [jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L293–L302](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L293-L302), [jiuwenswarm/server/runtime/debug_trace/stream_logger.py:L378–L380](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/debug_trace/stream_logger.py#L378-L380)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":249,"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","sha256":"f10aa3a3fc8f8a6eb63240f86b2b23054e59df7576186e24e14ff4e10525f7a1","start":240},{"end":302,"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","sha256":"f6a7ebb3d6b34f38331f990515ee075ae38d5bd0107d45c03909b01a2f435581","start":293},{"end":380,"path":"jiuwenswarm/server/runtime/debug_trace/stream_logger.py","sha256":"932392490e0cc9a1c00928ddc3c9f018daad175223fee007f21ef54db2220a09","start":378}],"trace":[]} -->
<!-- /kb:depth -->
