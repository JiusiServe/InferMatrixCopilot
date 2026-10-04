---
title: "小艺 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L55-L132, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L386-L412, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/国内频道.md:L67-L103", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L119-L132, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L40-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L59-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L298-L337, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L363-L364, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py:L109-L154]
feature: "im-xiaoyi"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/*"]
---

# 小艺 频道：实现深读

[功能概览](feature-im-xiaoyi.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-xiaoyi facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eccc6680ae883aed594f029e9c5cb26f1b98cd70c50a083f67479c2816e06bdf -->
**XiaoYiPushService.send_push 的布尔契约**
send_push(text, push_text) 以 JSON-RPC 2.0 结果载荷 POST 到 PushConfig.push_url，30 秒总超时；HTTP 200 返回 True，非 200、aiohttp.ClientError 或其他异常都只记日志并返回 False，不抛出。调用方必须检查返回布尔值，不能假设推送已送达。签名方式按 config.mode 分叉：xiaoyi_claw 用 x-uid/x-api-key 头，否则用 X-Access-Key/X-Sign(HMAC-SHA256)/X-Ts。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L55–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py#L55-L132)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py","start":55,"end":132,"sha256":"5fad34e6f2cfe89181fb0ef63215d20776eba334f086b1c1644a563bbf0bb5ae"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0ae4c37a8ab4ad8269aaa37e3fede37da8d20376cd9ff01d8216bc49526cb2ed -->
**enabled 默认关闭与启动前置校验**
文档默认 `enabled: false`、`enable_streaming: true`，mode 固定 `xiaoyi_channel`；配置位于 ~/.jiuwenswarm/config/config.yaml 的 channels.xiaoyi.apps，保存后运行中服务自动重载。代码侧生效条件：XiaoyiChannel.start 在 enabled=False 时直接返回；mode == "xiaoyi_channel" 且 ak/sk/agent_id 任一为空时记 error 并返回，不建立任何连接。启用 push 时 api_id 与 push_id 需同时填写。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L386–L412](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py#L386-L412), [docs/zh/国内频道.md:L67–L103](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%9B%BD%E5%86%85%E9%A2%91%E9%81%93.md#L67-L103)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py","start":386,"end":412,"sha256":"feecbf0a51ca95a6c87540fead4308e35973f7cc72a87d02899ba2e3298bf96e"},{"path":"docs/zh/国内频道.md","start":67,"end":103,"sha256":"9f344b2093ebf9c64850180730a55532949a4cfd041759042295bc0006d2d317"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9122367751e7eb08272d1ff2637e14b2965a4a625b0061aacc6298fd5c3ec200 -->
**XiaoYiPushService.send_push：mode=="xiaoyi_claw" 选定头部分支后 POST，status 200 才返回 True**
send_push(text, push_text) 生成毫秒时间戳与 message_id，构造 jsonrpc 2.0 result 负载（apiId/pushId/pushText、kind "task"、status completed、含 push_text 文本 artifact）；guard self.config.mode == "xiaoyi_claw" 时用 x-uid/x-api-key 头，否则用 X-Access-Key/X-Sign（来自 _generate_signature）/X-Ts；以 ClientTimeout(total=30) POST self.config.push_url，response.status == 200 记录日志并 return True，否则读取 body、记录错误日志并 return False。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L55–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py#L55-L132)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":132,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py","sha256":"5fad34e6f2cfe89181fb0ef63215d20776eba334f086b1c1644a563bbf0bb5ae","start":55}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a28ea2c727ca3f1771996dbff48a60392ab0702599e7bf76e8b57f0ea2eedef9 -->
**XiaoyiChannel.__init__ 耦合 XiaoyiChannelConfig 字段；channel_id 为空时 getter 回退类名 "xiaoyi"**
__init__ 接收 XiaoyiChannelConfig，用 config.file_upload_url/api_key/uid 组装 file_upload_config，并保存 config.api_id/push_id；channel_id 属性返回 self.config.channel_id or self.name，而 name 固定为 "xiaoyi"，即 channel_id 未配置（假值）时该属性返回 "xiaoyi"。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L298–L337](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py#L298-L337), [jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L363–L364](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py#L363-L364)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":337,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py","sha256":"37a1f1f7fec04d3cef5192b2292e31f31eda40ef8c262daa483350e8917bb6ca","start":298},{"end":364,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py","sha256":"b9efccad1c1e84e357f7f05cecd0fc3f41b995c6b359763a93b7113cea44970b","start":363}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c69e3b9a89494dcb123ee791f6b7da724f0f533fc9b148eb89b86e559100f25 -->
**_fetch_from_url：超 max_bytes 抛 ValueError；ClientResponseError/TimeoutError 转链式 RuntimeError 上抛**
在 _fetch_from_url 内，content-length 或实际读取的 buffer 超过 max_bytes 时 raise ValueError("File too large: … (limit: …)")（两个 except 只匹配 ClientResponseError 与 TimeoutError，故该 ValueError 不被捕获）；ClientResponseError 转 RuntimeError("HTTP {status}: {reason}")，asyncio.TimeoutError 转 RuntimeError("Download timeout after {timeout_ms}ms")，均 from 原异常向本函数调用方抛出。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py:L109–L154](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py#L109-L154)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":154,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/media.py","sha256":"65b0d40dbd1bf7e6ed54255d357c2c179c56d06aaa7dc4aa7fd36fe9fcb293cb","start":109}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e479ebea97a748feae19bbe2077269a9da6432842a93423bb0bb1c2d9c97604b -->
**send_push 以记录日志并返回 False 代替抛错（推断）**
设计推断（非作者历史意图）：

收益（推断）：HTTP 状态非 200、`aiohttp.ClientError` 或其他异常都只被记录日志并返回 `False`，推送失败不会中断调用方；代价（推断）：调用方只拿到裸布尔值，无法区分失败原因，细节仅存在于日志中。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L119–L132](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py#L119-L132)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":132,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py","sha256":"cdbe5eb307c19653eb7aa04293e24d5b83661467064b605ad6430cf6b728e5c7","start":119}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-xiaoyi facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8784777ae1511feb24872788f3c1609ef82725ef3dc95e86597974d01660af11 -->
**异步运行时测试断言首次 start 安装 provider、最后一个 stop 后恢复 fallback provider**
`test_provider_installs_on_first_start_and_restores_after_last_stop`（`pytest.mark.asyncio`）用真实 `XiaoyiChannel` 实例断言 `host_services.get_runtime_xiaoyi_channel("xiaoyi-first") is first`，`first.stop()` 后该 ID 变为 None 而 second 仍在，两个都 stop 并 `asyncio.sleep(0)` 后查询返回 `fallback` 对象。

来源：[tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L40–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py#L40-L49), [tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py:L59–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py#L59-L83)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":49,"path":"tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py","sha256":"dd05843c9508e9c5bc3a9435c70d6c4c64e033ffc4b265fdbe2976ca092d78e0","start":40},{"end":83,"path":"tests/unit_tests/runtime/test_runtime_xiaoyi_host_provider.py","sha256":"e0bdc777370a8fac9d4a9028bb8987f76461f909a48ffa0927c389f411616f03","start":59}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
