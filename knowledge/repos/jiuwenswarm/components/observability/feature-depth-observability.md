---
title: "执行轨迹与保留：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L261-L289, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py:L62-L70]
---

# 执行轨迹与保留：实现深读

[功能概览](feature-observability.md) · [owner 入口](_index.md)

<!-- kb:depth feature=observability facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5122d74a8d08b46bc056b1061990bcd7ee8afbec91bc5585273e3e623935cb3c -->
**帧队列满的降级行为**
consume_stream_frame 在 _frame_queue.put_nowait 抛 queue.Full 时不阻塞也不重试：计 dropped 与 dropped_frames，打 warning 说明实时流将出现缺口直到该 span 的完整输出随终态记录到达，然后正常返回。另一个触发点是 _record_owner_is_consistent 拒绝跨会话主体（subject_session 既非空也非 owner 或 owner_sub_ 前缀）时计 failed 直接丢弃。

来源：[jiuwenswarm/observability/sink.py:L261–L289](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L261-L289), [jiuwenswarm/observability/sink.py:L62–L70](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L62-L70)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/observability/sink.py","start":261,"end":289,"sha256":"3344f21523fe9d599ee18860e75d72539a9aa21cf70aa8bd84eaf972b3800967"},{"path":"jiuwenswarm/observability/sink.py","start":62,"end":70,"sha256":"5467ed789fb548f44003de76dca8f5a274ea0254dfb233d9acab51dc65577ddf"}],"trace":[]} -->
<!-- /kb:depth -->
