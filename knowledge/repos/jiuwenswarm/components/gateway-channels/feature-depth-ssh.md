---
title: "SSH 频道与远程终端：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L144-L149, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L273-L290, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_ssh_channel.py:L205-L219, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/channel/test_ssh_channel.py:L279-L281, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_agentos_ssh_relay.py:L392-L416, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py:L1-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L18-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L13-L18, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L163-L193, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L144-L171, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L180-L182, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L119-L138, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/base.py:L129-L136, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L124-L141, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L184-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py:L14-L18]
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

<!-- kb:depth feature=ssh facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=00aaaeba45bbe49eecdfc0f8a2be79486c86744c0193b09c56ba7e43fb27db1b -->
**启用且 asyncssh 可导入时的 SshChannel.start 启动路径**
SshChannel.start() 在 _running 已置位或 config.enabled 为假（记 "[SSHChannel] disabled by config" 日志）时直接返回；否则构建 SSHProxy 并 await start()——ASYNCSSH_AVAILABLE 为假且导入失败时经 _raise_missing_asyncssh 抛出——成功后置 _running=True、记录 started 日志并 await wait_closed()。

来源：[jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L163–L193](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py#L163-L193), [jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L144–L171](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L144-L171), [jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L180–L182](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L180-L182)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":193,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py","sha256":"5d5794c9148f282ddedde172a4087b74cfdca74889e83d253802bfe45a5c1008","start":163},{"end":171,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","sha256":"fa748b48e43e3693e9561da54966b3310bc80121478eacf188dc28d9b253545a","start":144},{"end":182,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","sha256":"a8ee183f53caad86999377ab8eeba2fda07f7fd992445e665038d51719e1055a","start":180}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ssh facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8eb7f0817fe2611b31d7bad58c7e3400349af74dc0199a0b930f4e1eade3388f -->
**SshChannel 构造签名与 SSHProxy 的 authenticator 解析优先级**
SshChannel(BaseChannel).__init__(config: SshChannelConfig, router: RobotMessageRouter, key_registry: KeyRegistry | None = None) 先经 super().__init__(config, router) 将 config 存为 self.config、router 存为 self.bus；SSHProxy.__init__ 中显式传入的 authenticator 优先，否则由 key_registry 构造 SshPublicKeyAuthenticator，两者皆无则为 None。

来源：[jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L119–L138](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py#L119-L138), [jiuwenswarm/gateway/channel_manager/base.py:L129–L136](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/base.py#L129-L136), [jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L124–L141](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L124-L141)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":138,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py","sha256":"c10dcb244a1a5da3cd636cd6ef31ef7c16f54366441da252c129a9260f330e19","start":119},{"end":136,"path":"jiuwenswarm/gateway/channel_manager/base.py","sha256":"df45a09b523dacad51f85dce35d958204af1bffe37c76912102ce63a7124036f","start":129},{"end":141,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","sha256":"97e297979cc7b3f23994874bf9ffea5ce68caa0e992ba3b8001a7072e8eb0c3d","start":124}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ssh facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f0f4958dea7acfa514c81811a7a22733e2669d3182eff7b23b1b79a311c8e725 -->
**ssh 包惰性导出：频道类延迟加载 ssh_connect，KeyRegistry 直接取自 auth 模块，未知名抛 AttributeError**
包 __getattr__：取 SshChannel/SshChannelConfig/SshAuthConfig 时才 import ssh_connect（其顶层引入 server.py 的 SSHProxy/SSHAgentHooks，server.py 再引入 ssh_authenticator、ssh_key_registry 与 ssh/config）；取 KeyRegistry 直接来自 extensions.agentos.auth.ssh_key_registry；其余名字抛 AttributeError，故包级导入不加载 ssh_connect。

来源：[jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py:L1–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py#L1-L29), [jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py:L18–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py#L18-L24), [jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L13–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L13-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/__init__.py","sha256":"94c46cf6998f217040028c348632275077ab79f002125c13de6c0c7f474f6522","start":1},{"end":24,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/ssh_connect.py","sha256":"0be98fd83e218300c1ea63b3a3fc821f0c73d43cdac08d50fad79720f0239c17","start":18},{"end":18,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","sha256":"3f87db015c09380f7f221fa9eb0f940fef1b2b1e68b5ef1a6de898fb58698fbb","start":13}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ssh facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=27c294bf666f01947ae76ab8ef776cbbf8de6bfd22d5ff685097425ad70ebd3a -->
**键路径无文件时才自动生成 ssh-rsa 2048 主机键；算法与键长硬编码**
设计推断（非作者历史意图）：

_ensure_host_key 先 mkdir 父目录：键路径已存在即 read_private_key 复用，不存在才 generate_private_key("ssh-rsa", key_size=2048) 并落盘私钥与 .pub。收益：该不存在分支可就地补齐缺失的键文件；代价：算法与键长写死，ProxyConfig 仅 listen_host/listen_port/host_key_path 三个字段、无对应设置。

来源：[jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py:L184–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py#L184-L194), [jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py:L14–L18](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py#L14-L18)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":194,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/server.py","sha256":"1e920c56a6ccf41102662be5c2cafe82cb916adbc442d6731b46a0f153a3013c","start":184},{"end":18,"path":"jiuwenswarm/gateway/channel_manager/protocol/ssh/config.py","sha256":"2d0309989028a60482097b57f51cf643adfb2918645cba89788991b9333918db","start":14}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ssh facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2a1d8c573e7b61685d3d18bd7f7bc826eee7fa54ac1bfd5a79faadb388cd6e9f -->
**运行时单测断言：身份 metadata 来自注册条目；relay 用例断言 relay_started/ran/exit_code**
`test_handle_ssh_client_uses_authenticated_identity` 注册指纹 `SHA256:ok`、source=`tui_switch` 的 KeyRegistryEntry 后，断言捕获 metadata `username=="auth-user"`、`auth_source=="tui_switch"`；relay 用例经 `send_request(_ssh_envelope(...))` 断言 `response.payload["status"]=="relay_started"`、`stub_relay.ran==[("ssh_alice_1234","sbx-1","alice")]` 且 `session.exit_code==0`（relay 以 stub 注入）。

来源：[tests/unit_tests/channel/test_ssh_channel.py:L205–L219](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_ssh_channel.py#L205-L219), [tests/unit_tests/channel/test_ssh_channel.py:L279–L281](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/channel/test_ssh_channel.py#L279-L281), [tests/unit_tests/extensions/test_agentos_ssh_relay.py:L392–L416](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_agentos_ssh_relay.py#L392-L416)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":219,"path":"tests/unit_tests/channel/test_ssh_channel.py","sha256":"2742d7d649f71112362ac8ed52e8c90acd436f93bf34146277cb70bf08889a8f","start":205},{"end":281,"path":"tests/unit_tests/channel/test_ssh_channel.py","sha256":"d7160517b16f534bd82110ace3b1dae7055459e23226f25abffc384b076fc360","start":279},{"end":416,"path":"tests/unit_tests/extensions/test_agentos_ssh_relay.py","sha256":"6ccab0f37a969eeafbb7d448f258a197d1a48d6946de75e6bb5d9817ea6b3e35","start":392}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
