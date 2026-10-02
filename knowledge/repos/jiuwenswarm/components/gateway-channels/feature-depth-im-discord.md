---
title: "Discord 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L190-L217]
---

# Discord 频道：实现深读

[功能概览](feature-im-discord.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-discord facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=586bbef5fe155937c059ff0b69f2b868be5e26534801069cae60468cfa2c915c -->
**消息回调契约**
_handle_discord_message 处理完一条用户文本后构造 type="req"、req_method=ReqMethod.CHAT_SEND 的 Message：若 _on_message_cb 不为 None 则以其返回值接管投递（调用方需处理返回协程，代码用 asyncio.iscoroutine 检测并 await），否则默认走 self.bus.route_user_message(req)。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L190–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L190-L217)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","start":190,"end":217,"sha256":"2b8ed26acdf28189d96a2d1bd437ff924e9d87c1881cd0c888fbe35ee76a3ccb"}],"trace":[]} -->
<!-- /kb:depth -->
