---
title: "微信 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407-L447, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L911-L974, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L26-L34, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L413-L414, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L438-L443, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L422-L431, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L969-L971, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L637-L647, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407-L414, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L466-L470, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L472-L476, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L1111-L1113, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L472-L585, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L612-L649, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/国内频道.md:L585-L601"]
feature: "im-wechat"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/wechat/*"]
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

<!-- kb:depth feature=im-wechat facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4bc2144715dffd56ede33343e71707885f6895d72a42cc4ef51e9f1aa5303838 -->
**发送策略为模块级常量（hard_max=10, content_part_limit=9, interval_sec=0.5），start() 启动时记录**
发送上限在导入时固化为模块常量（所示片段未从用户配置读取）：MAX_MESSAGES_SEND_TO_WECHAT=10、WECHAT_CONTENT_SEND_LIMIT=max(1,10-1)、WECHAT_SEND_INTERVAL_SEC=0.5；start() 以 hard_max/content_part_limit/interval_sec 记录该策略，轮询 HTTP 会话超时为 config.long_poll_timeout_sec+5（实例配置）。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L26–L34](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L26-L34), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L413–L414](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L413-L414), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L438–L443](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L438-L443)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":34,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"886b997ea940740afd2a0a7e971a40ea81af8dfa3f4a0874904fed185244c4cd","start":26},{"end":414,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"8133dab39526447e57f8c30ee8e99b380b38ecf7bb120c08d5c0b205f98637e0","start":413},{"end":443,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"f6cb5eeda3177e38a4f26c02a4d89261cbe9c898ac7fc240a982528f93945e46","start":438}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-wechat facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5d3712e4122f7ed91207709c3e49006619cf1d72ef30e1bbdd65db08d6c384a6 -->
**依赖 start() 创建的 aiohttp 会话：send() 未就绪仅告警返回，_send_message 无会话抛 RuntimeError**
start() 创建 total=config.long_poll_timeout_sec+5 的 aiohttp.ClientSession（L413-414）；send() 在无会话或无 config.bot_token 时仅告警并返回（L474-476）；_send_message 先经 _require_http，会话为 None 时抛 RuntimeError("WechatChannel HTTP client is not initialized")（L466-470、L1111-1112）。两处守卫条件不同，互不覆盖 bot_token。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L407–L414](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L407-L414), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L466–L470](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L466-L470), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L472–L476](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L472-L476), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L1111–L1113](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L1111-L1113)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":414,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"74d446a2a364534fefd0ff196958fdc7b2380ae6dc2538c0285a2759c473265b","start":407},{"end":470,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"cb3e092dc13cf2b8b73a3ed765dc5d5f1ecb558d4e5f886612397bbb2e7dc373","start":466},{"end":476,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"c32e09493a0b7733d3050b83116ee56655f8f43379dadb4f7777e9142fb21bbc","start":472},{"end":1113,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"0c19d9f12a3ed7c97d3fbe7a0c5a31fe3d58303caec40b725471d7d79aab56b1","start":1111}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-wechat facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=11e5899f9cad2a93669f78a3d6c31eb238f11e5ffa8c4644a84732a683ccd7e4 -->
**start() 登录失败记日志后上抛且不创建轮询任务；可重试 WechatSendMessageError 转为暂存+繁忙提示**
start() 中 _load_or_login_credentials 抛错时 logger.exception 后原样 raise，轮询任务不会创建；bot_token 为空且 auto_login=false 的登录准备分支抛 RuntimeError("WechatChannel 未配置 bot_token，且 auto_login=false")。发送分片循环中 WechatSendMessageError 且 ret 属于 WECHAT_SENDMESSAGE_RETRYABLE_RETS 时，暂存剩余分片、下发繁忙提示并 return，其余 ret 上抛。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L422–L431](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L422-L431), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L969–L971](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L969-L971), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L637–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L637-L647)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":431,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"09fe46b13042f746851fd26f756a624612399cb9bdcbe37ee3c0b337e26dbf5d","start":422},{"end":971,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"e4d579d336309ad426733feb4d458d9e6989301de4b3ec63482b516808dda48e","start":969},{"end":647,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"c967eb6eebb60493aff790f83b4bd5fbd710162205f1c0d2c20c095852ae7c70","start":637}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-wechat facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9f50857a4619d7cd386450ee8d2d7e08a48ec5e90584be1f7499aeb526d0582c -->
**WechatChannel CHAT_TOOL_CALL：仅 enable_streaming 时下发，限额触发时暂存不送达**
设计推断（非作者历史意图）：

send 在 _http 与 bot_token 就绪后处理 CHAT_TOOL_CALL：非流式直接 return（少发过程消息，代价是工具过程不可见）；流式合并已积累 delta 与工具文本，但限额触发时仅 _stash_overflow_content 暂存并 return，进入 helper 后仍需 user_id 与 context_token 才真正送达。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L472–L585](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L472-L585), [jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py:L612–L649](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py#L612-L649)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":585,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"d3fa54aed6835aaef427b261284cecfdcb9c6d518cbe673673280422305546b1","start":472},{"end":649,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/wechat/wechat_connect.py","sha256":"7a8ee4e8bd592dd7f78e2ea5d7f0df2cf7aa689e777dddb00aa94c64ff3999f1","start":612}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-wechat facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5aa817ab5b537757d74226baa83ab0560b36613b00e2abde17dc6eb15340835c -->
**个人微信扫码接入的文档化手动检查（NOT EXECUTED，仅断言二维码出现）**
文档中的人工验收步骤（本轮未执行）：

文档化人工步骤（NOT EXECUTED，本轮未执行）：先在微信「我→设置→关于微信→版本更新」升级至最新版，再在前端「频道」→「微信」启用微信配置并保存，页面出现二维码，随后用手机微信「扫一扫」扫描完成接入。仅覆盖二维码展示与扫码入口，不含消息收发或认证成功的断言。

来源：[docs/zh/国内频道.md:L585–L601](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%9B%BD%E5%86%85%E9%A2%91%E9%81%93.md#L585-L601)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":601,"path":"docs/zh/国内频道.md","sha256":"3a1e24d4968b051352e34cba27956d0476e3cb528de6aa3be5bb32ba4caf3a9d","start":585}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
