---
title: "WhatsApp 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L67-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L153-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L201-L209, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L57-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L24-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L162-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L24-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L211-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L157-L160, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/海外频道.md:L541-L552", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L107-L112, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L129-L135, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L107-L135]
feature: "im-whatsapp"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/*"]
---

# WhatsApp 频道：实现深读

[功能概览](feature-im-whatsapp.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-whatsapp facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00b666ee279f333296de4d8819270b998114a036f2415767848dbe720ae454b4 -->
**启动链路：WhatsAppChannel.start 到重连循环**
调用方调用 WhatsAppChannel.start() 后，先按配置做守卫检查，置 self._running = True；若 auto_start_bridge 为真则 await self._start_bridge_process() 拉起本地桥进程，随后 asyncio.create_task 启动 self._reconnect_loop()（任务名 whatsapp-channel-connect）。_reconnect_loop 在 while self._running 循环里反复 await self._connect_once()，任何非 CancelledError 异常仅记 warning，随后 asyncio.sleep(5) 再试。_connect_once 的实现不在提供的切片内，故链条止于 _reconnect_loop。

调用路径：`jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py`（`WhatsAppChannel.start`） → `jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py`（`WhatsAppChannel._reconnect_loop`）

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L67–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L67-L83), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L153–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L153-L179), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L201–L209](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L201-L209)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":67,"end":83,"sha256":"a35851e46ce1fdc85641c32bb2021a0f3b04d51ed87ad465c30ec7ba4babdeda"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":153,"end":179,"sha256":"1cea95e6307724011550ebe9ca93801744977667005fba8d896e415bbd631d90"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":201,"end":209,"sha256":"332d3038bfd3f09cad31247c487585078c6ed41de995bdff33e2d83458abcfaf"}],"trace":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","symbol":"WhatsAppChannel.start","start":67,"end":83},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","symbol":"WhatsAppChannel._reconnect_loop","start":201,"end":209}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=30ad3f09f89a34257c29e540e85642a79b4ac8fb12f36883c63e856687a43e66 -->
**start() 的生命周期契约**
start() 是幂等守卫式生命周期入口：已运行（self._running）时仅记 warning 并返回；config.enabled 为假或 bridge_ws_url 为空白时同样直接返回且不置位 _running。调用方义务是先确保 enabled=true 且 bridge_ws_url 非空，否则频道静默不启动（仅日志可见）。channel_id 属性恒返回 self.name（"whatsapp"）。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L67–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L67-L83), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L57–L58](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L57-L58)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":67,"end":83,"sha256":"a35851e46ce1fdc85641c32bb2021a0f3b04d51ed87ad465c30ec7ba4babdeda"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":57,"end":58,"sha256":"67b928c1d79d104ec7784babbc0da4ce9305c3a36b9305c63e9bfa115e5c158f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=a5550cffc83140687da7b8bc43c600b679f42e490fdee8f40d055e1afc0303f8 -->
**WhatsAppChannelConfig 默认值**
enabled 默认 False（需显式开启），bridge_ws_url 默认 "ws://127.0.0.1:19600/ws"，auto_start_bridge 默认 False，bridge_command 默认 "node scripts/whatsapp-bridge.js"。auto_start_bridge 仅在其为真时使 start() 调 _start_bridge_process；bridge_workdir 为空字符串时回退为 Path(__file__).resolve().parents[1]，bridge_env 逐项覆盖到 os.environ 副本之上。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L24–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L24-L33), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L162–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L162-L168)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":24,"end":33,"sha256":"7f0ec50dd86cea9d95405ea786988cf632f620bbe3b6e6d39507104351cf7a74"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","start":162,"end":168,"sha256":"5dfdee57c44b058c8c543cd8db2e79363102cfe97c9e1695d85b28415b2d0302"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=12004928a92ad4eff8c61788f43251d13260db097272bee33d476a07644a72bc -->
**延迟导入 websockets 连本机 bridge（默认 ws://127.0.0.1:19600/ws），失败进入 5 秒重连循环**
`_connect_once` 内 `import websockets` 并连接 `bridge_ws_url`（默认 `ws://127.0.0.1:19600/ws`）；异常被 `_reconnect_loop` 捕获记 warning 后 `asyncio.sleep(5)` 重试。`auto_start_bridge` 生效还需 `bridge_command` 非空，为空时只记 warning 不拉起进程。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L24–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L24-L30), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L211–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L211-L219), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L201–L209](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L201-L209), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L157–L160](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L157-L160)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":30,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"d92624f3bf00354a90fc9fb7615d6651cc777597a143e5cb97377970aa2ab739","start":24},{"end":219,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"f5f996cb4e0bbf48d82291395331a360ec974531cf078606e7a8f4cf6accd874","start":211},{"end":209,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"332d3038bfd3f09cad31247c487585078c6ed41de995bdff33e2d83458abcfaf","start":201},{"end":160,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"24ba0945003d7b7bb42fd27895ac7467dd009234f68f7242c3b91c445760ea00","start":157}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=39bcc59b9b18cb16467c80a3b578236ef140a93443f7a290361b32d97643a38c -->
**send()：_ws 为 None 时静默 return；WhatsApp 未连接时告警后 return（两条守卫均在构帧之前）**
send() 中，`self._ws is None` 的守卫直接 return 且不记任何日志；`not self._whatsapp_connected` 时记录 "WhatsAppChannel send skipped: WhatsApp not connected (state=%s)"（携带 _bridge_state）后 return。两条守卫都在构造 {"type":"send",...} 帧之前结束本次调用，本次调用不发送。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L107–L112](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L107-L112), [jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L129–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L129-L135)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":112,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"f89580093285cd4a0b624264f9057cafa9b4da0bbfda18eebcbeb054207a4161","start":107},{"end":135,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"c31d902b01def6a76d3b4e3ae50a7cdc75adccde21ba22702c7d68de10a24de9","start":129}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=4c8ee8d7e7701bb2996c70432904102ae09d1d81022ddd588352d94f5fc775d4 -->
**文档化手动验证：项目根目录运行 `python -m jiuwenswarm.app`（NOT EXECUTED）**
文档中的人工验收步骤（本轮未执行）：

docs/zh/海外频道.md 记录：在项目根目录运行 `python -m jiuwenswarm.app`，预期应用日志显示 `WhatsAppChannel` 已注册，频道先进入 `bridge_connected`，再按登录状态进入 `connecting`、`qr_pending` 或 `open`。显式标记 NOT EXECUTED：本次仅引用文档，未实际运行。

来源：[docs/zh/海外频道.md:L541–L552](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%B5%B7%E5%A4%96%E9%A2%91%E9%81%93.md#L541-L552)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":552,"path":"docs/zh/海外频道.md","sha256":"b1f169a8349be2bcaea6b183e34a59f08309af1af04ed11d3343d61bdf986a79","start":541}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=im-whatsapp facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c260cdeecb9eba9f1e63ac70d347c6d4162088cbcc51a1e791e4c418dbda4215 -->
**WhatsApp send 关闭 enable_streaming 时仅过滤 event 型 CHAT_DELTA 的局部取舍**
设计推断（非作者历史意图）：

`send` 在 `_ws` 为 None 或 `_whatsapp_connected` 为假时已先返回；仅当 `enable_streaming` 关闭且消息为 `type == "event"` 的 `EventType.CHAT_DELTA` 时才提前返回，空文本或无目标 jid 亦返回。推断收益：非流式下减少增量出站帧；代价：该场景不逐段下发增量内容，且此开关并非唯一发送条件。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L107–L135](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py#L107-L135)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":135,"path":"jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py","sha256":"eac71b9aca044f1e827ae017114ce8cfb8dac02fce4a7ca9c3b3b5217d2feb3b","start":107}],"trace":[]} -->
<!-- /kb:depth -->
