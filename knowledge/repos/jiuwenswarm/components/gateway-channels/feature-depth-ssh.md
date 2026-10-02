---
title: "SSH 频道与远程终端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L144-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L273-L290]
feature: "ssh"
entry_points: ["jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py", "jiuwenswarm/gateway/channel_manager/protocol/ssh/*.py"]
---

# SSH 频道与远程终端：实现深读

[功能概览](feature-ssh.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ssh facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=efe665845840eb9fd52bb9787d8ff0410c4b01d23fd6a933ebeff7bfdac88498 -->
**缺依赖与会话错误的传播**
SSHProxy.start 在 ASYNCSSH_AVAILABLE 为假且 import asyncssh 失败时调用 _raise_missing_asyncssh 抛出，服务不启动。会话期间抛出 asyncssh.Error 时，_handle_ssh_client 记录 error 日志，随后对 stdout 写入 "Proxy error: ..." 和 process.exit(1) 的尝试都包在吞掉异常的 try/except 中，因此输出与退出码是尽力而为；finally 仍会 await unregister_session。

来源：[jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L144–L149](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L144-L149), [jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L273–L290](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L273-L290)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","start":144,"end":149,"sha256":"33b38ca21366e6a56160940f69700745b4d26c6228fafb56a1157fba7b445d15"},{"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","start":273,"end":290,"sha256":"d6a37a446c651d420ae2181a3636a7427c77bd49f7f86d4fa9f0a31e9c9903ae"}],"trace":[]} -->
<!-- /kb:depth -->
