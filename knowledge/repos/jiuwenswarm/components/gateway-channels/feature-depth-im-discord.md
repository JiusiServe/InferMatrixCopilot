---
title: "Discord 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L190-L217, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L142-L217, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L25-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L163-L176, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/海外频道.md:L143-L151", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L16-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L58-L61, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L116-L140, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/海外频道.md:L285-L289"]
feature: "im-discord"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/discord/*"]
---

# Discord 频道：实现深读

[功能概览](feature-im-discord.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-discord facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=586bbef5fe155937c059ff0b69f2b868be5e26534801069cae60468cfa2c915c -->
**消息回调契约**
_handle_discord_message 处理完一条用户文本后构造 type="req"、req_method=ReqMethod.CHAT_SEND 的 Message：若 _on_message_cb 不为 None 则以其返回值接管投递（调用方需处理返回协程，代码用 asyncio.iscoroutine 检测并 await），否则默认走 self.bus.route_user_message(req)。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L190–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L190-L217)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","start":190,"end":217,"sha256":"2b8ed26acdf28189d96a2d1bd437ff924e9d87c1881cd0c888fbe35ee76a3ccb"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-discord facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c5bf081f720a7d687d4ff5bfed16434a343b2a5baec522b48c48bcb009a9f5ad -->
**入站回调 _handle_discord_message：守卫（非 bot、is_allowed、guild/channel 过滤仅限服务器消息）通过后派发 req**
依次守卫 _running、作者非 bot、author_id 通过 is_allowed、channel 非空；服务器消息须匹配 guild_id/channel_id（配置空串不限制），DM 仅当 block_dm=True 时拒绝并加 🚫。content 非空后加 👀，以 session_id=discord_{channel_id}_{author_id} 构造 CHAT_SEND 的 Message，经 _on_message_cb（未注册则 await bus.route_user_message）派发。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L142–L217](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L142-L217)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":217,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"e49b272d0e9b7d11961965249bc996fa6e0cb5df44dddcd038670b7167692a49","start":142}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-discord facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=99cfd502432a7448172d79487a59d63993b593aa2ed989000fb4da3234768b45 -->
**DiscordChannelConfig 默认 enabled=False、block_dm=False、allow_from=[]；guild_id/channel_id 空串不限制且不过滤 DM**
dataclass 默认：enabled=False、bot_token/application_id/guild_id/channel_id 均为空串、block_dm=False、allow_from=[]。guild_id/channel_id 仅对服务器消息（guild_id 非空）生效，DM 不受二者限制，只在 block_dm=True 时被忽略并加 🚫；文档字段表默认值与代码一致。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L25–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L25-L33), [jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L163–L176](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L163-L176), [docs/zh/海外频道.md:L143–L151](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%B7%E5%A4%96%E9%A2%91%E9%81%93.md#L143-L151)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":33,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"3aeb54553b2163b3f540f81ebfcee8ce220358441d9f4565ccb02e57fe6e0743","start":25},{"end":176,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"41fdc0a19b210222bcda16fa25659b2338aca33f98679f3fbbd412d3a78c59ce","start":163},{"end":151,"path":"docs/zh/海外频道.md","sha256":"82d7f9f594fa08fd44b393d0a615d99c6e39a98eeadcc18790e29c5165ccac09","start":143}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-discord facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f1698601c82260fccdcc2529d193a95ed1ee2d2975bbcde586af2f2c9979e980 -->
**discord.py 为 try-import 可选依赖：ImportError 时 start() 记录 "Discord SDK not installed. Run: pip install discord.py" 后直接返回**
try 导入 discord 成功则 DISCORD_AVAILABLE=True；ImportError 时置 False 且 discord=None，模块仍可导入。start() 首个分支在 not DISCORD_AVAILABLE 时 logger.error 该消息并 return，不构造 client、不抛异常。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L16–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L16-L22), [jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L58–L61](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L58-L61)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"cb9d77da82ecca54b9c6f0820e84e516ab60d0757c57a9805b61db2bd779ebf5","start":16},{"end":61,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"113338296b699fbeb161d834b6e08a3393a59c53f8bd6c3a579e792637d3be14","start":58}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-discord facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dd220900fed3eb9f50f55cba9405ee3245d48cbf5c019ca8580d5e9c271392b5 -->
**send()：客户端缺失/已关闭或空内容静默返回；缺目标频道、fetch 或发送异常记 warning 后返回**
self._client 为 None 或 is_closed() 时直接 return，_extract_outgoing_text 为空同样 return，二者无日志(L117-122)；目标频道 id 为 None 记 'send skipped: missing target channel id' 后返回，fetch_channel 与 channel.send 异常各记 warning 后返回，不向调用方抛出(L124-140)。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py:L116–L140](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py#L116-L140)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":140,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/discord/discord_connect.py","sha256":"0997e2b2c3ab253a68a75cec9c5bac1089af69bafb3f4311ea007580de4896e5","start":116}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-discord facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1bc00dbf179d44d3846ebf1cd4d69008e811fb8cf9265323e09b2e629b3ae28a -->
**文档化手动验证：条件式预期 👀 反应与智能体回复（未执行）**
文档中的人工验收步骤（本轮未执行）：

docs/zh/海外频道.md §8「验证」为手动流程：在已配置频道或私信发送一条短消息；若 Bot 在该场景有添加反应权限，用户消息上应出现 👀；模型与下游配置正确时，应收到智能体回复。该流程为既有文档记载，未执行。

来源：[docs/zh/海外频道.md:L285–L289](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%B7%E5%A4%96%E9%A2%91%E9%81%93.md#L285-L289)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":289,"path":"docs/zh/海外频道.md","sha256":"75ac1f0b5011237aecc9069121aa7f7c7d196214ddce35db979be7bf2c33eea7","start":285}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
