---
title: "Telegram 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L39-L47, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L92-L98, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/海外频道.md:L55-L61", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L278-L394, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L157-L174, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L208-L218, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L50-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L21-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L84-L90, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/base.py:L129-L153, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L352-L371, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_telegram_channel.py:L50-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L181-L203, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_telegram_channel.py:L40-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_telegram_channel.py:L18-L37]
feature: "im-telegram"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/telegram/*"]
---

# Telegram 频道：实现深读

[功能概览](feature-im-telegram.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-telegram facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=71132011df4fada5a1b7bf41460441f0f04c1135cafd76f524ebc495abf5af93 -->
**配置默认值与启动门槛**
TelegramChannelConfig 默认 enabled=False、bot_token 为空、allow_from=[]、parse_mode="Markdown"、group_chat_mode="mention"，与 docs/zh/海外频道.md 的配置表一致。enabled 与 bot_token 共同构成启动前置条件：start() 在 enabled=False 时打 warning 返回，在 bot_token 为空时打 error 返回。文档另说明 allow_from 为空列表时允许所有用户。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L39–L47](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L39-L47), [jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L92–L98](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L92-L98), [docs/zh/海外频道.md:L55–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%B7%E5%A4%96%E9%A2%91%E9%81%93.md#L55-L61)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","start":39,"end":47,"sha256":"743a065536239b3af701bda4a217a08ce9060b86a383870ed8f663b256ef40e4"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","start":92,"end":98,"sha256":"2ebf98f9d8832fbdb5a5b5d3ba395ff542fd425a616744e909cd9a9c60915e34"},{"path":"docs/zh/海外频道.md","start":55,"end":61,"sha256":"69ceb354e4ac8c1cd0decdba788c07d1ef1e9f9ffc581adcce3c0c11b5e33b6b"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7047fb80de058e91b238c62b5ef8585177a67591a3ab05c83b1b7007f4e82d35 -->
**入站文本经 _handle_message 校验与群聊模式过滤后生成 telegram_{chat_id} 会话并下发**
文本更新进入 _handle_message：先校验 message/effective_user/effective_chat 与 is_allowed(str(user_id))，群聊按 group_chat_mode 分支（off 直接 return；mention 要求文本含 @{bot_username} 并移除该提及；reply 要求回复的是机器人消息），随后 set_reaction("👀")，以 f"telegram_{chat_id}" 生成 session_id 构造 Message，经 _on_message_cb（协程则 await）或 bus.route_user_message 下发。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L278–L394](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L278-L394)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":394,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"0c698748da91b0b9be447f7ac975b47aa6229c47bd2a8291243206ebd2ef4f94","start":278}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4e8d9b911f55fde10d9ce0bdd112cd18c4a1d0835cc26dee804ac8e334f1b87d -->
**send 按消息元数据或 telegram_ 前缀会话解析 chat_id，缺失即记告警并跳过**
send(msg, *, routing_target=None) 返回 None：chat_id 先取 msg.metadata["chat_id"]，否则从 "telegram_" 前缀的 session_id 解析（int 失败返回 None）；chat_id 或 _extract_content 结果为空时仅 logger.warning 并跳过，不抛异常。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L157–L174](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L157-L174), [jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L208–L218](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L208-L218)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":174,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"4926304995612987d71722f0ee308ccdf2c50aa31ecc33e591fa8628d879d21f","start":157},{"end":218,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"20b3f2d305f24148beea7da4a56d246aeb65342f102f99d6337bbaf4513628a9","start":208}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=efb6854e80f384ae4605377d6493246828ffbd8fee1fc4a140a0b37ce90f6cbc -->
**继承 BaseChannel 并软依赖 python-telegram-bot**
TelegramChannel 声明继承 BaseChannel，__init__ 经 super() 复用基类的 config/bus 存储，start/stop 为基类抽象方法；python-telegram-bot 用 try 导入，失败时置 TELEGRAM_AVAILABLE=False，start() 记录 error 后直接返回、不启动。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L50–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L50-L68), [jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L21–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L21-L33), [jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L84–L90](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L84-L90), [jiuwenswarm/gateway/channel_manager/base.py:L129–L153](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/base.py#L129-L153)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":68,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"40b8dad9b3c613c5ce02e818029b62d492f003d6bfb8f5616a54e2ccb0119548","start":50},{"end":33,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"5836d340318b06a1b5c80418deb2b4a8336af00f3cd2b7818703fdb2289f5bb1","start":21},{"end":90,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"4693bdf0c17c34aea24d35e99efe8f0637568c6b12741bcab534b41a8e604a4f","start":84},{"end":153,"path":"jiuwenswarm/gateway/channel_manager/base.py","sha256":"198bc1527fd6e33e8f8db86f96f00287a9f9579fdee36a38174f32e9dc6b0ec5","start":129}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=48a4c6e2671f683b1ae02079049767721ef8f00808022198051727172772fa58 -->
**send(): 仅 parse/entity 类错误且 parse_mode 非空时重试一次；其余异常由 send() 外层 except 记日志**
send() 内层 send_message 抛异常且 error_str 小写含 "parse" 或 "entity" 且 parse_mode 非空时，以 parse_mode=None 重发一次；否则重新 raise，被 send() 外层 except 记录 error 日志后正常返回。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L181–L203](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L181-L203)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":203,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"d0d8a7f38ee8ff8b99b5044787d04125fab78a0660a6b1605650fdc382fc46c3","start":181}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0f5118e3e3b6797e199f483ccc0e2e2e5c5accc200aa2d7241b092d16acc8f1f -->
**按 chat_id 确定性派生 session_id：省去映射缓存但不区分发送者（推断）**
设计推断（非作者历史意图）：

收益（推断）：session_id=f"telegram_{chat_id}" 就地派生，无需维护 chat→session 缓存，测试也断言 channel 无 _chat_sessions 属性；成本（推断）：该键只含 chat_id 不含 user_id，同一 chat 的不同发送者会得到相同 session_id。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py:L352–L371](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py#L352-L371), [tests/unit_tests/channel/test_telegram_channel.py:L50–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_telegram_channel.py#L50-L58)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":371,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/telegram/telegram_connect.py","sha256":"6e2da76da0df6f6ecce6275effdfbd97f1998f8b908d8c89636111068baf8e10","start":352},{"end":58,"path":"tests/unit_tests/channel/test_telegram_channel.py","sha256":"7d2c380d916759b6f07064943defac6cdfb64929984d2ad666ba303616d9da87","start":50}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-telegram facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f9d4bf9ff8049f3be7e4febcb6b93a0350606477583f12865c901856ed7c9f75 -->
**runtime 单测三次 await 真实 _handle_message，断言由 chat_id 派生 session_id 且无 _chat_sessions**
test_telegram_channel.py 的 pytest.mark.asyncio 用例以 TelegramChannelConfig(enabled=True, group_chat_mode="all") 构造频道，用 _update()（SimpleNamespace 与 _FakeTelegramMessage）伪造 update，三次 await channel._handle_message 后断言 session_id 依次为 telegram_123456、telegram_-987654、telegram_123456，并断言 not hasattr(channel, "_chat_sessions")。

来源：[tests/unit_tests/channel/test_telegram_channel.py:L40–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_telegram_channel.py#L40-L58), [tests/unit_tests/channel/test_telegram_channel.py:L18–L37](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_telegram_channel.py#L18-L37)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":58,"path":"tests/unit_tests/channel/test_telegram_channel.py","sha256":"33eda1bd0d0362ce602acb12999e2110ca44902f8686b36c8e3ca0339a578e42","start":40},{"end":37,"path":"tests/unit_tests/channel/test_telegram_channel.py","sha256":"00061f2e7b0ff806a34b2ab440b71241e0d5c95856647b52c9115f46e93d69f8","start":18}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
