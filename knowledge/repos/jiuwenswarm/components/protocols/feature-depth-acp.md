---
title: "ACP 与 stdio 桥接：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L36-L60, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/acp/cli.py:L75-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L2432-L2433]
---

# ACP 与 stdio 桥接：实现深读

[功能概览](feature-acp.md) · [owner 入口](_index.md)

<!-- kb:depth feature=acp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=213cad28f677e3ef64166d107f5c4e3f0b87142c79806a6528ae3ed38c801a49 -->
**profile 字段与关闭超时默认值**
profile 从 config.yaml 的 acp_agents 读取：command 必填，args 列表转字符串列表，cwd 仅在非空白字符串时生效，env 仅在为 dict 时传入。环境变量 ACP_CLI_CLOSE_TIMEOUT_S 默认 "30" 秒，作为 finally 中 asyncio.wait_for 包裹（shield）client.close() 的超时。JIUWENSWARM_SKIP_DOTENV 不为 "1" 时从 get_env_file()（配置目录下 .env）以 override=False 加载。

来源：[jiuwenswarm/acp/cli.py:L36–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L36-L60), [jiuwenswarm/acp/cli.py:L75–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/acp/cli.py#L75-L82), [jiuwenswarm/common/utils.py:L2432–L2433](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L2432-L2433)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/acp/cli.py","start":36,"end":60,"sha256":"3ea6bbea36353b9660ecd84019876b00e658ea467b07b486b3ffa9f6e3548fe8"},{"path":"jiuwenswarm/acp/cli.py","start":75,"end":82,"sha256":"809f3601bdc60424725d7732f4806280f0bdd36f18c58eec4f68ddf3867ea692"},{"path":"jiuwenswarm/common/utils.py","start":2432,"end":2433,"sha256":"562c74494478ae96e2d9c95235e3bec4f8f71971510d7db7a1057423ce467782"}],"trace":[]} -->
<!-- /kb:depth -->
