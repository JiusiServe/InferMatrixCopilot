---
title: "WhatsApp 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L67-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L153-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L201-L209, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L57-L58, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L24-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/whatsapp/whatsapp_connect.py:L162-L168]
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
