---
title: "执行轨迹与保留：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L261-L289, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L62-L70, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L472-L511, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/config.py:L98-L109, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/store.py:L2336-L2357, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/observability/test_trajectory_session_usage.py:L107-L118, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/observability/test_trace_store.py:L506-L518, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L302-L326]
feature: "observability"
entry_points: ["jiuwenswarm/observability/sink.py"]
source_globs: ["jiuwenswarm/observability/sink.py", "jiuwenswarm/observability/*.py"]
---

# 执行轨迹与保留：实现深读

[功能概览](feature-observability.md) · [owner 入口](_index.md)

<!-- kb:depth feature=observability facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5122d74a8d08b46bc056b1061990bcd7ee8afbec91bc5585273e3e623935cb3c -->
**帧队列满的降级行为**
consume_stream_frame 在 _frame_queue.put_nowait 抛 queue.Full 时不阻塞也不重试：计 dropped 与 dropped_frames，打 warning 说明实时流将出现缺口直到该 span 的完整输出随终态记录到达，然后正常返回。另一个触发点是 _record_owner_is_consistent 拒绝跨会话主体（subject_session 既非空也非 owner 或 owner_sub_ 前缀）时计 failed 直接丢弃。

来源：[jiuwenswarm/observability/sink.py:L261–L289](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L261-L289), [jiuwenswarm/observability/sink.py:L62–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L62-L70)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/observability/sink.py","start":261,"end":289,"sha256":"3344f21523fe9d599ee18860e75d72539a9aa21cf70aa8bd84eaf972b3800967"},{"path":"jiuwenswarm/observability/sink.py","start":62,"end":70,"sha256":"5467ed789fb548f44003de76dca8f5a274ea0254dfb233d9acab51dc65577ddf"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=observability facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fd8aaa1ed8c200ffe7117f63d5fd451982d005b9265b57f1a9b81191c4a167ff -->
**TrajectoryRecordSink._write_batch：坏记录只计数不中断，成功后更新 committed/conflicts**
writer 线程的 _write_batch 遍历批次：queued_final 为真走 from_core_record，否则 from_core_snapshot；构造抛 AttributeError/TypeError/ValueError/OverflowError 时仅计数 failed 并 warning，批次继续；无记录且无帧直接 return，否则调用 _write_records_with_retry，成功后按 result.inserted/conflicts 更新计数。

来源：[jiuwenswarm/observability/sink.py:L472–L511](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L472-L511)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":511,"path":"jiuwenswarm/observability/sink.py","sha256":"8a34459bfae62ae41fa5f581f660d3742cadad046b49994ac5507a0019cc85fd","start":472}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=observability facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6dd881736f0b878e53a11da27bd01f4f58e1783803450deb4dc5701855d9ee0d -->
**TrajectoryRecordSink.close：先 request_stop 再限时 join 写线程，超时返回 False 且不清 _thread**
close() 先调用 request_stop()，再以 max(0.1, timeout) 秒 join 写线程（timeout 关键字参数默认 15.0）；线程不存在或已停止时返回 True 并把 _thread 置为 None；超时则记录队列内记录数并返回 False，_thread 保持不变。

来源：[jiuwenswarm/observability/sink.py:L302–L326](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L302-L326)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":326,"path":"jiuwenswarm/observability/sink.py","sha256":"1bf9bbba3fa146c0e3e0f5fc1245a10d2bafa2883ef0350f7c2b93be47151b1f","start":302}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=observability facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=90145a2012a013777e491f549751da44e7307673dabefe5c7956eba6b74e9507 -->
**会话库路径按 SHA-256 摘要路由，database_files 连同 WAL 旁车一起返回**
会话数据库路径由规范化 session_id 的 SHA-256 摘要决定：database_root/digest[:2]/{digest}.sqlite3；database_files 返回该文件及其 -wal、-shm 三个路径，删除会话库须三者同删，否则残留 WAL 会被同路径后建的库重放。

来源：[jiuwenswarm/observability/config.py:L98–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/config.py#L98-L109)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/observability/config.py","sha256":"5b5a44f9903678b0113068e2f24651f6c4f23e5ff2b4bb21f6683225cea3a984","start":98}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=observability facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ef6525c976ba7254e2540b5aff857bfbb4b15b6866325c678e491671858aeb6 -->
**AsyncTrajectoryReader._connect 依赖 aiosqlite 与 _SCHEMA_VERSION，版本不符读作不存在**
_connect 依赖 aiosqlite 与 _SCHEMA_VERSION 常量：session_scoped 时先经 session_database_path 换算路径，文件不存在返回 None；以 mode=ro 打开并设 busy_timeout 与 query_only=ON 后校验 PRAGMA user_version，不等于 _SCHEMA_VERSION 即关闭连接并返回 None，旧版本库在读端表现为不存在。

来源：[jiuwenswarm/observability/store.py:L2336–L2357](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/store.py#L2336-L2357)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2357,"path":"jiuwenswarm/observability/store.py","sha256":"353491340d795bc1918d4d3fda1b21633bc70723dada5b1ef432def41c2edde8","start":2336}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=observability facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1e15a1664847671ba95e20a85ab67241c58610dedb9ef253f4d03df0e93aea86 -->
**usage 与 raw 读取的既有运行时断言（未执行）**
引用现有测试源码，本次未执行：test_trajectory_session_usage.py L107 运行 AsyncTrajectoryReader(database_path).get_session_request_usage("session-1")，L111-118 断言 len(by_identity)==3、shared 的 usage total==11 且 cacheRead==5、两条 cumulative_usage input 为 15/20；test_trace_store.py L512-516 断言 get_raw_record 返回字节与 final_record.raw_json 全等。

来源：[tests/unit_tests/observability/test_trajectory_session_usage.py:L107–L118](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/observability/test_trajectory_session_usage.py#L107-L118), [tests/unit_tests/observability/test_trace_store.py:L506–L518](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/observability/test_trace_store.py#L506-L518)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":118,"path":"tests/unit_tests/observability/test_trajectory_session_usage.py","sha256":"7b6feb4ef78f5742c751554c1e139113cbbe6884cc49b73c71951f4a241ef04b","start":107},{"end":518,"path":"tests/unit_tests/observability/test_trace_store.py","sha256":"68b1ac9d8a22a01ff6212a16c295c1347d860921e398aed8677cf2e3dc24334c","start":506}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
