---
title: "微信 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407-L447, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L911-L974]
---

# 微信 频道：实现深读

[功能概览](feature-im-wechat.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-wechat facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=88426582eb1f54bde43c928af6fa8f4ddf773443b637fa5a2cd16020a001872c -->
**启动链路：start 先加载凭据再进入轮询**
WechatChannel.start 启动时先创建带 long_poll_timeout_sec+5 总超时的 aiohttp 会话，随后同步 await WechatChannel._load_or_login_credentials；后者按配置 bot_token → 本地凭据文件 → 扫码登录的顺序解析凭据，未配置且 auto_login=false 时抛 RuntimeError 使启动失败，成功后 start 才创建 _poll_loop 任务。

调用路径：`jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py`（`WechatChannel.start`） → `jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py`（`WechatChannel._load_or_login_credentials`）

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407–L447](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L407-L447), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L911–L974](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L911-L974)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","start":407,"end":447,"sha256":"e6c8c4311ca2ed6371671ca7a11e6d19ef6ff8bd7354f4eedf805c73d9d562c0"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","start":911,"end":974,"sha256":"dee889723b208dcba413b90eba773d20c6e06c5587f3e07edb6587675f25624a"}],"trace":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","symbol":"WechatChannel.start","start":407,"end":447},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","symbol":"WechatChannel._load_or_login_credentials","start":911,"end":974}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-wechat facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=96d155e1cd820ddc05e30f8d93790298134e62a6a5227d714b3fad651529ccb8 -->
**start 的生命周期契约**
WechatChannel.start 是幂等防护的入口：self._running 已置位时仅告警并返回；正常路径完成凭据加载后用 asyncio.create_task 启动名为 "wechat-channel-poll" 的轮询任务，并以 while self._running: await asyncio.sleep(1) 保持存活。登录阶段任何异常都会被记录后 re-raise，调用方必须处理启动失败。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407–L447](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L407-L447)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","start":407,"end":447,"sha256":"e6c8c4311ca2ed6371671ca7a11e6d19ef6ff8bd7354f4eedf805c73d9d562c0"}],"trace":[]} -->
<!-- /kb:depth -->
