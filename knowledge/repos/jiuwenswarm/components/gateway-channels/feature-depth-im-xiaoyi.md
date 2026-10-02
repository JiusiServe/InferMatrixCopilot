---
title: "小艺 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_utils/push.py:L55-L132, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/xiaoyi/xiaoyi_connect.py:L386-L412, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/国内频道.md:L67-L103"]
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
