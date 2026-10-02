---
title: "Telegram 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L39-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L92-L98, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/海外频道.md:L55-L61"]
---

# Telegram 频道：实现深读

[功能概览](feature-im-telegram.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-telegram facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71132011df4fada5a1b7bf41460441f0f04c1135cafd76f524ebc495abf5af93 -->
**配置默认值与启动门槛**
TelegramChannelConfig 默认 enabled=False、bot_token 为空、allow_from=[]、parse_mode="Markdown"、group_chat_mode="mention"，与 docs/zh/海外频道.md 的配置表一致。enabled 与 bot_token 共同构成启动前置条件：start() 在 enabled=False 时打 warning 返回，在 bot_token 为空时打 error 返回。文档另说明 allow_from 为空列表时允许所有用户。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L39–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L39-L47), [jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L92–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L92-L98), [docs/zh/海外频道.md:L55–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%B7%E5%A4%96%E9%A2%91%E9%81%93.md#L55-L61)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","start":39,"end":47,"sha256":"743a065536239b3af701bda4a217a08ce9060b86a383870ed8f663b256ef40e4"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","start":92,"end":98,"sha256":"2ebf98f9d8832fbdb5a5b5d3ba395ff542fd425a616744e909cd9a9c60915e34"},{"path":"docs/zh/海外频道.md","start":55,"end":61,"sha256":"69ceb354e4ac8c1cd0decdba788c07d1ef1e9f9ffc581adcce3c0c11b5e33b6b"}],"trace":[]} -->
<!-- /kb:depth -->
