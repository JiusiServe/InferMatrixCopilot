---
title: "E2A 统一请求响应协议：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L119-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L301-L310, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/e2a/test_gateway_normalize.py:L23-L41, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/e2a/test_wire_codec.py:L203-L210, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/session_updates.py:L101-L156, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L105-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/session_updates.py:L24-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/acp/session_updates.py:L135-L139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/wire_codec.py:L174-L183, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/wire_codec.py:L221-L229, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/wire_codec.py:L204-L227, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/e2a/models.py:L462-L492]
feature: "e2a"
entry_points: ["jiuwenswarm/common/e2a/models.py"]
source_globs: ["jiuwenswarm/common/e2a/models.py", "jiuwenswarm/common/e2a/*.py"]
---

# E2A 统一请求响应协议：实现深读

[功能概览](feature-e2a.md) · [owner 入口](_index.md)

<!-- kb:depth feature=e2a facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5a6a33383476b638e0279a043d62af82a39e80bb0cf8d7e35017fa3f334ac216 -->
**build_acp_tool_descriptor 的输入契约**
build_acp_tool_descriptor 的 tool_call_id 是唯一必填关键字参数；arguments 宽松接受 dict、JSON 字符串或其他类型，由 _normalize_arguments 归一为 dict（字符串解析失败或解析结果非 dict 时包装为 {"input": 原字符串}）。调用方只需给出原始工具名，别名与 kind 推断由函数内部完成。

来源：[jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L119–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/acp_tool_updates.py#L119-L148), [jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L301–L310](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/acp_tool_updates.py#L301-L310)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/e2a/acp/acp_tool_updates.py","start":119,"end":148,"sha256":"bd150266786e3188b77a0b49ce48cc19903ac7f2e135e683636ad4b631da2213"},{"path":"jiuwenswarm/common/e2a/acp/acp_tool_updates.py","start":301,"end":310,"sha256":"48dcc0f5d82fe2edf556ff96de801c25817ccc6cd09fba69bcb45e5b7dab28a7"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=02c45ccf191d3dd437eed6750c5444aecc8abee6829cb50c5c7fb8b59245bab5 -->
**build_acp_session_update 将带非空文本的 delta 事件映射为 thought/message chunk 或 None**
event_type 为 CHAT_DELTA/CHAT_REASONING 且 payload 的 content 非空时：is_reasoning_event 为真则把文本追加进 state.thought_text 并返回 agent_thought_chunk（messageId 由 state helper 生成），否则追加 assistant_text 并返回 agent_message_chunk；空文本、CHAT_SYMPHONY_STATUS 及未列出的 event_type 均返回 None。

来源：[jiuwenswarm/common/e2a/acp/session_updates.py:L101–L156](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/session_updates.py#L101-L156), [jiuwenswarm/common/e2a/acp/acp_tool_updates.py:L105–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/acp_tool_updates.py#L105-L111)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":156,"path":"jiuwenswarm/common/e2a/acp/session_updates.py","sha256":"cdb80ea4a104c4046ea80dc8192dfc4ae43a7e991dff2dd0024bc7b07a62018e","start":101},{"end":111,"path":"jiuwenswarm/common/e2a/acp/acp_tool_updates.py","sha256":"2f41008fa0d487c8cb8a3ce4f828c2d8d08d007b47a1c3aaf6696016b9e2fc4c","start":105}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=753aaf6994e67119aa92349e45acd775921cb2c6906eaef777b8f4a5b6dd2081 -->
**merge_params_to_acp_prompt：仅 method=="session/prompt" 且 params 无 prompt 键时的补全优先级与提前返回**
method=="session/prompt" 且浅拷贝 p 无 prompt 键才补全：content_blocks 为非空 list 时直接作 prompt，否则 text/content/query 中第一个真值本身是非空 str 才生成单条 text block（真值非 str 不再后查）；p 已含 prompt 键则 L477 提前返回，该路径不写 session_id、也不把 acp_meta 合入 _meta。

来源：[jiuwenswarm/common/e2a/models.py:L462–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/models.py#L462-L492)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":492,"path":"jiuwenswarm/common/e2a/models.py","sha256":"c0115d43d0dd7c3709d6681a2a0e977bfa360c22435dc01b7c3294cec45fee1e","start":462}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a1131883be25cb4e050b8ffaa30137d138acf5abcc669002759244a8685bb12c -->
**工具调用与工具结果更新共用 state 上惰性创建的同一 tool_call_cache**
CHAT_TOOL_CALL 分支调 build_acp_tool_call_update，CHAT_TOOL_UPDATE/CHAT_TOOL_RESULT 分支调 build_acp_tool_result_update，二者都传 _ensure_tool_call_cache(state)；该 helper 在 state.tool_call_cache 不是 dict 时新建空 dict 挂回 state 并返回，同一 state 的后续事件经 getattr 取到同一 dict。

来源：[jiuwenswarm/common/e2a/acp/session_updates.py:L24–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/session_updates.py#L24-L29), [jiuwenswarm/common/e2a/acp/session_updates.py:L135–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/acp/session_updates.py#L135-L139)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/common/e2a/acp/session_updates.py","sha256":"35095b6fb7157fed0457b90d3987c6d497bb2211935fa9caf1f0d0db507b26cf","start":24},{"end":139,"path":"jiuwenswarm/common/e2a/acp/session_updates.py","sha256":"784b2b9c3d82abe99a4d23a67f5697de9f2970ed6518b0f2d221a7330b1104b7","start":135}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d7a1ca369df017f67126547bd50c5f91c561341de1f08ae06dfa981d1be4b984 -->
**wire chunk 的 from_dict 失败原样上抛且无兜底；无法识别形状抛含 key 列表的 ValueError**
is_e2a_response_wire_dict 为真而 E2AResponse.from_dict 抛错时，记录 stage=from_dict 异常日志后 raise，此路径不走 legacy 兜底；非 E2A 形状时若 _deprecated_chunk_shape 为假则抛 ValueError，消息附带最多前 32 个顶层 key（deprecated 形状仅告警并按 raw dict 转换）。

来源：[jiuwenswarm/common/e2a/wire_codec.py:L174–L183](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/wire_codec.py#L174-L183), [jiuwenswarm/common/e2a/wire_codec.py:L221–L229](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/wire_codec.py#L221-L229)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":183,"path":"jiuwenswarm/common/e2a/wire_codec.py","sha256":"c3824c064e657d1756ff86c0f1822e2880a8314800c4f60a7d62d6e431ef17f4","start":174},{"end":229,"path":"jiuwenswarm/common/e2a/wire_codec.py","sha256":"b1b9baa8f63516c1060197dfb037d936d4f1f0c29162565d51f23e8716d8b448","start":221}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1ff971df05a2c0b6eb5432eb0906f4f82974db3be2c6170acce7f63560a23b0e -->
**推断：legacy/deprecated 回退提高解码容错，代价是保留两条非主路径分支**
设计推断（非作者历史意图）：

推断：逆转换失败且 metadata 里 legacy 键为 dict 时能返回 chunk 而非上抛，是容错收益；代价是解码器须同时维持这条回退分支与 deprecated 形状的仅告警接受分支，非主转换路径增多。

来源：[jiuwenswarm/common/e2a/wire_codec.py:L204–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/e2a/wire_codec.py#L204-L227)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":227,"path":"jiuwenswarm/common/e2a/wire_codec.py","sha256":"9b6737ec4a4a0a7db969d57123a1dd1b50305e7c8896f1bf26646d04d105693a","start":204}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=e2a facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=994ab2a5400cd4865a6326a06f26bf95c834f5a68528fb9f135f65e0d8a04fc9 -->
**单测断言 wire 往返保留 execution_id 及 chunk 形状抛 ValueError**
test_execution_binding_survives_agent_wire_and_web_payload 以四种 event_type 参数化，实际执行 e2a_response_from_agent_chunk→e2a_response_to_agent_chunk→WebChannel._build_event_payload，断言 payload['execution_id']=='execution-A' 且 payload['session_id']=='session-A'；test_wire_codec.py 将 is_complete=False 的 chunk wire 传入 parse_agent_server_wire_unary，以 pytest.raises(ValueError) 断言其抛错。

来源：[tests/unit_tests/e2a/test_gateway_normalize.py:L23–L41](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/e2a/test_gateway_normalize.py#L23-L41), [tests/unit_tests/e2a/test_wire_codec.py:L203–L210](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/e2a/test_wire_codec.py#L203-L210)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":41,"path":"tests/unit_tests/e2a/test_gateway_normalize.py","sha256":"8e2c04cec7322bd998c2eb7f465304b19e3e32ab844afe740b8f1697363d7dce","start":23},{"end":210,"path":"tests/unit_tests/e2a/test_wire_codec.py","sha256":"f8c2571a0453e5b3f374bd95dc96c3b7ddf0a54445a721beecd1decdc982c018","start":203}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
