---
title: "ACP 与 stdio 桥接：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L36-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L75-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L2432-L2433, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L13-L24, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/stdio_client.py:L1-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/subprocess_env.py:L1-L12, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/acp/stdio_client.py:L512-L521, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_acp_stdio_client_st.py:L162-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/system_tests/test_acp_stdio_client_st.py:L191-L199, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L19-L29, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L32-L62, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L65-L86, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/acp/stdio_client.py:L484-L492, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/acp/stdio_client.py:L545-L549, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L13-L66, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/stdio_client.py:L3-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/acp/stdio_client.py:L488-L543]
feature: "acp"
entry_points: ["jiuwenswarm/acp/stdio_client.py"]
source_globs: ["jiuwenswarm/acp/stdio_client.py", "jiuwenswarm/acp/*.py"]
---

# ACP 与 stdio 桥接：实现深读

[功能概览](feature-acp.md) · [owner 入口](_index.md)

<!-- kb:depth feature=acp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=213cad28f677e3ef64166d107f5c4e3f0b87142c79806a6528ae3ed38c801a49 -->
**profile 字段与关闭超时默认值**
profile 从 config.yaml 的 acp_agents 读取：command 必填，args 列表转字符串列表，cwd 仅在非空白字符串时生效，env 仅在为 dict 时传入。环境变量 ACP_CLI_CLOSE_TIMEOUT_S 默认 "30" 秒，作为 finally 中 asyncio.wait_for 包裹（shield）client.close() 的超时。JIUWENSWARM_SKIP_DOTENV 不为 "1" 时从 get_env_file()（配置目录下 .env）以 override=False 加载。

来源：[jiuwenswarm/acp/cli.py:L36–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L36-L60), [jiuwenswarm/acp/cli.py:L75–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L75-L82), [jiuwenswarm/common/utils.py:L2432–L2433](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L2432-L2433)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/acp/cli.py","start":36,"end":60,"sha256":"3ea6bbea36353b9660ecd84019876b00e658ea467b07b486b3ffa9f6e3548fe8"},{"path":"jiuwenswarm/acp/cli.py","start":75,"end":82,"sha256":"809f3601bdc60424725d7732f4806280f0bdd36f18c58eec4f68ddf3867ea692"},{"path":"jiuwenswarm/common/utils.py","start":2432,"end":2433,"sha256":"562c74494478ae96e2d9c95235e3bec4f8f71971510d7db7a1057423ce467782"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=55980febf77f3708266f50a7231ab2efc99fec38b49e34b41476864ed44fc037 -->
**main 把 _run_once 的返回值传入 sys.exit；acp_agents profile 要求非空 command**
argparse：agent 必填，message 可选默认 'Hello'；_run_once 在 acp_agents profile 缺失/非 dict 或 command 为空时局部返回 2，成功为 0，connect/chat 抛 Exception 时在 except 内局部返回 1——客户端构造位于 try 之外，构造异常不被捕获。

来源：[jiuwenswarm/acp/cli.py:L19–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L19-L29), [jiuwenswarm/acp/cli.py:L32–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L32-L62), [jiuwenswarm/acp/cli.py:L65–L86](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L65-L86)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/acp/cli.py","sha256":"14e0f7bcfce77336daacaa54effde6b3e8fb84ab18c10f3ea8bd18f91bf79574","start":19},{"end":62,"path":"jiuwenswarm/acp/cli.py","sha256":"f631f3904e2e5fe7da89b029d773fee3e5ee7714c15829707c06cc8309823372","start":32},{"end":86,"path":"jiuwenswarm/acp/cli.py","sha256":"5ab88b2748a32e1647e6121d4ac25d273681a80c8aa9428fc00f6099614b53cb","start":65}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cc412039d74fa54eaa1c7925457aa93c94e6a21787576ad1e8202962158a77c1 -->
**耦合：common.config 读取与 common.acp 的兼容 re-export 层**
`cli` 从 `jiuwenswarm.common.config.get_config` 读 `acp_agents`；`jiuwenswarm/acp/stdio_client.py` 与 `subprocess_env.py` 仅 re-export `jiuwenswarm.common.acp` 实现，docstring 自述为保住 `jiuwenswarm-acp-chat` 等旧 import 路径，且该层将在阶段 3 删除。

来源：[jiuwenswarm/acp/cli.py:L13–L24](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L13-L24), [jiuwenswarm/acp/stdio_client.py:L1–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L1-L13), [jiuwenswarm/acp/subprocess_env.py:L1–L12](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/subprocess_env.py#L1-L12)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":24,"path":"jiuwenswarm/acp/cli.py","sha256":"8b9672ab8144599058bbeacb41fa0a772cc95512ee3a9619148b2503286edb97","start":13},{"end":13,"path":"jiuwenswarm/acp/stdio_client.py","sha256":"422262a66b290159d6a474f703a7a43260dd1582cd5146ef36764a889e02bf61","start":1},{"end":12,"path":"jiuwenswarm/acp/subprocess_env.py","sha256":"6c9b8a2e73f68dda8eca4c981911b026fe38e654fbba05e5c018e6f5fbdb313a","start":1}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2935e2b34fce2f90bcf4e77312801538a76a4f4750dedeb5bca7361f723675f8 -->
**profile/command 无效时 _run_once 局部返回 2 且不构造客户端；会话期异常被 except 捕获后局部返回 1**
acp_agents 非 dict、profile 非 dict 或 command 为空时 _run_once 记录错误并局部返回 2，不构造客户端——connect 的 ValueError('ACP agent command is empty') 在该路径不会到达；rpc 层收到 JSON-RPC error 对象即 raise RuntimeError，chat 异常（含 'not connected; call connect() first' 前置检查）被 except 捕获，记录 '[ERROR] ACP session failed' 后局部返回 1。

来源：[jiuwenswarm/acp/cli.py:L19–L29](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L19-L29), [jiuwenswarm/acp/cli.py:L32–L62](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L32-L62), [jiuwenswarm/common/acp/stdio_client.py:L484–L492](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/stdio_client.py#L484-L492), [jiuwenswarm/common/acp/stdio_client.py:L545–L549](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/stdio_client.py#L545-L549)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":29,"path":"jiuwenswarm/acp/cli.py","sha256":"14e0f7bcfce77336daacaa54effde6b3e8fb84ab18c10f3ea8bd18f91bf79574","start":19},{"end":62,"path":"jiuwenswarm/acp/cli.py","sha256":"f631f3904e2e5fe7da89b029d773fee3e5ee7714c15829707c06cc8309823372","start":32},{"end":492,"path":"jiuwenswarm/common/acp/stdio_client.py","sha256":"ba05896addcaacc6bcf9588d54901d8728c33050c023c3a4f17b046fcecf1104","start":484},{"end":549,"path":"jiuwenswarm/common/acp/stdio_client.py","sha256":"acc8c6bf4bdcf3a4a5a11f46ac1b3d33313b8f709f4a9f79f6524f877ce9008f","start":545}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b764173337b703ac6cdd921fe6c6ed9bee1414fb7b5223e7a630d88e5ab03b5d -->
**initialize 能力取舍：声明 FS 能力、放弃 terminal**
`initialize` 声明 `clientCapabilities.fs.readTextFile=True/writeTextFile=True` 而 `terminal=False`；行内注释自述收益是让 Codex ACP 等 Agent 完成工具回合，代价是本客户端不支持 terminal 能力。

来源：[jiuwenswarm/common/acp/stdio_client.py:L512–L521](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/stdio_client.py#L512-L521)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":521,"path":"jiuwenswarm/common/acp/stdio_client.py","sha256":"db42a5b1c6a0c1d5bd0eb714ce35ec205ba5ecb1182a0db5874883d671c22a64","start":512}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f46ddde99ad89ca095a8a57afb8376ffa673ac2580ca946da27059c5907b562f -->
**系统测试：真实子进程假 Agent 上的 connect/chat 断言**
`test_stdio_client_connect_and_chat_with_fake_agent` 拉起 tmp_path 生成的子进程假 Agent，断言 `client.session_id == "st-fake-session"` 且 `chat("hello st") == "echo:hello st"`；`test_stdio_client_chat_raises_on_jsonrpc_error` 断言 `chat` 抛出匹配 `ACP JSON-RPC error:.*agent failed` 的 `RuntimeError`。

来源：[tests/system_tests/test_acp_stdio_client_st.py:L162–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_acp_stdio_client_st.py#L162-L187), [tests/system_tests/test_acp_stdio_client_st.py:L191–L199](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/system_tests/test_acp_stdio_client_st.py#L191-L199)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":187,"path":"tests/system_tests/test_acp_stdio_client_st.py","sha256":"087dedd5f9a1db11193a70ff33866177642104f655d0da98e81380c65e89fb8b","start":162},{"end":199,"path":"tests/system_tests/test_acp_stdio_client_st.py","sha256":"6567f340642ed53c3ae22113ad86f6aba2a80d7f6476d5a93531bbcd36511828","start":191}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=acp facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=56034d5bd9949b2efe83a90cc634f6ec29f9129acd21a03955e6fdff9cd10869 -->
**ACP CLI 冒烟路径：acp_agents profile → AcpStdioClient.connect 建会话 → _run_once 本地返回 0/1/2**
_get_spec 从 get_config() 的 acp_agents 字典按 strip 后的 agent 名取 profile，无该字典或 profile 非字典时记 error 返回 None；_run_once 据此返回 2，command 去空白后为空也返回 2。有效时构造 AcpStdioClient（jiuwenswarm/acp/stdio_client.py 仅从 common.acp re-export 以保持旧 import 路径）并 connect：已关闭抛 RuntimeError、空命令抛 ValueError，随后以三路 PIPE（_KILL_PG 为真时加 start_new_session）启动子进程，先发 initialize（protocolVersion 1、fs 读写均为 True、terminal 为 False，超时 120 秒），再发 session/new（cwd 取 self._cwd 绝对化值否则 os.getcwd()，mcpServers 为空列表，超时 60 秒）；结果须为 dict，sessionId 缺失或为空时可回退 session_id，strip 后仍为空则抛 RuntimeError，否则存入 _session_id。回到 _run_once，connect/chat 成功后以 info 记录 out 或「(empty response)」并返回 0；仅该 try 内的 Exception 记「[ERROR] ACP session failed」返回 1；finally 中按 ACP_CLI_CLOSE_TIMEOUT_S（默认 30）作超时对 shield 的 close 等待，关闭异常仅记 warning。

来源：[jiuwenswarm/acp/cli.py:L13–L66](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L13-L66), [jiuwenswarm/acp/stdio_client.py:L3–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/stdio_client.py#L3-L13), [jiuwenswarm/common/acp/stdio_client.py:L488–L543](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/acp/stdio_client.py#L488-L543)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":66,"path":"jiuwenswarm/acp/cli.py","sha256":"b1bb9aa5687e7636f149063136010556b001477c9bd99af7a1a8f863e83c433c","start":13},{"end":13,"path":"jiuwenswarm/acp/stdio_client.py","sha256":"3c7eb93789351b7385a5d3e5f3c434dd0f6b29bf2468d599959feaaa8663ea19","start":3},{"end":543,"path":"jiuwenswarm/common/acp/stdio_client.py","sha256":"4f6d47c0ee78e4ec984eff6e58ac9247448aaa7c7465a5cf9126c1f03302c53e","start":488}],"trace":[]} -->
<!-- /kb:depth -->
