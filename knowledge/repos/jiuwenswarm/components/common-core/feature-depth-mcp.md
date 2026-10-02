---
title: "MCP 配置、凭据与资源：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L107-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L97-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L47-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L74-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L2546-L2590]
---

# MCP 配置、凭据与资源：实现深读

[功能概览](feature-mcp.md) · [owner 入口](_index.md)

<!-- kb:depth feature=mcp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c78146026a0b1d77c60453cde4d064562b6e31283ed3b1764a0796923112794 -->
**build_mcp_server_config 的契约**
build_mcp_server_config(entry) 要求 entry 含非空 name，transport 必须属于 {stdio, sse, http, streamable-http, streamable_http}，stdio 还需 command、HTTP 还需 url，否则返回 None（调用方静默跳过）。credential_resolver 缺省为 None，此时占位符保持字面量（向后兼容）；传入 resolver 才会替换 env/args/url/headers 中的 ${VAR}。

来源：[jiuwenswarm/common/mcp_config.py:L107–L195](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L107-L195)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/mcp_config.py","start":107,"end":195,"sha256":"c38c56f87dc89cd067c350f14d8f555a2429f004c4a0f1adeecc1ba217c91636"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=mcp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=612dd8a6f663461fd864a651be298ef8017282772af3ee594c9dcb3d6970910f -->
**enabled 默认与凭据优先级**
mcp.servers 条目的 enabled 缺省按 True 处理（bool(item.get("enabled", True))）。占位符解析优先级为：该 MCP 的 CredentialStore 存储值优先，未命中再取 os.environ，都没有则保留字面 ${VAR}（build_mcp_credential_resolver 的 resolver 闭包定义此顺序；无存储凭据时整个 resolver 为 None）。

来源：[jiuwenswarm/common/mcp_config.py:L97–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L97-L104), [jiuwenswarm/common/mcp_config.py:L47–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L47-L71)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/mcp_config.py","start":97,"end":104,"sha256":"d22d9bd215bfc4008e85ca38a08c25e70d073a1523ad7e6699fbf55fecf0a57c"},{"path":"jiuwenswarm/common/mcp_config.py","start":47,"end":71,"sha256":"fd57e75cbe0703a48aad75bfdad851d8c82c74027f54040b13318991a32639c5"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=mcp facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=889fed189c6b429b560325e2593cb65cc65362378bdadf1c15eb163547c3c397 -->
**与 mcp/state.json 动态连接器的合并**
extract_enabled_mcp_server_entries 的权威来源是 get_mcp_servers()，它合并 config.yaml 的 mcp.servers 与 mcp/state.json 中 state==connected 的记录，同名冲突时 state.json 优先；传入的 config_base 仅在 store 读取失败（如 bootstrap 早期）时作回退。因此 config_base 里的 servers 会漏掉动态注册的 MCP。

来源：[jiuwenswarm/common/mcp_config.py:L74–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L74-L104), [jiuwenswarm/common/config.py:L2546–L2590](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L2546-L2590)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/mcp_config.py","start":74,"end":104,"sha256":"cc1a4726b552d9b9e16a1abcf2784cd153aaca7680991457c8239e1eaf3cbcc2"},{"path":"jiuwenswarm/common/config.py","start":2546,"end":2590,"sha256":"3c531a1262b724b1b5074759142c7ce9cde5cf72db97de3e1ace09b7bc5fea5c"}],"trace":[]} -->
<!-- /kb:depth -->
