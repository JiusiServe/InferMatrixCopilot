---
title: "MCP 配置、凭据与资源：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L107-L195, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L97-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L47-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L74-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L2546-L2590, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L440-L448, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/mcp/test_mcp_config_placeholder.py:L60-L68, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_mcp_startup_prewarm.py:L65-L88, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L300-L324, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L492-L503, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py:L440-L547]
feature: "mcp"
entry_points: ["jiuwenswarm/common/mcp_config.py"]
source_globs: ["jiuwenswarm/common/mcp_config.py"]
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

<!-- kb:depth feature=mcp facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=44f9678905aad75156ef7624f9712fe7d39bc8dab8650844481487a89d4d1444 -->
**preflight 的超时/不可达/401/403 捕获分支就地返回 (False, 原因)；probe 的 stdio PATH 缺失分支**
preflight_mcp_server_reachable 把 httpx.TimeoutException 转 (False, "http probe timed out after {read_t}s…")、ConnectError 等转 "unreachable: …"、其余异常兜底 "probe failed: …"、401/403 转 "auth rejected (HTTP n)"，全部就地返回不抛出；probe_mcp_live_connection 在 stdio 且 command 非空、shutil.which(cmd) 为 None 时返回 (False, "command '…' not found on PATH")，preflight 失败 reason 原样向上返回。

来源：[jiuwenswarm/common/mcp_config.py:L300–L324](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L300-L324), [jiuwenswarm/common/mcp_config.py:L492–L503](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L492-L503)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":324,"path":"jiuwenswarm/common/mcp_config.py","sha256":"0839f75c6ae5658ad9bd1175f26a1a164e25b42f3d549d3bd4f1b6e5d7b42df5","start":300},{"end":503,"path":"jiuwenswarm/common/mcp_config.py","sha256":"2c9e83a6f4aa8dda3d3ecee1d180c2de89fed15c7ca34c968ea8226d1f6a9f38","start":492}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=mcp facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c611f700cb65dd16939aa0e9bbe63e43d8b0e61748df393b3210b048360662d8 -->
**实连探测取舍（docstring 明文）：握手/npx 失败提前暴露，代价是用户在连接期等待**
收益：npx 首次安装与握手失败在连接期（用户等待 connect 时）暴露，而非首轮对话静默退化成 "no tools"；代价：等待同样落在 connect 阶段——两侧均为函数 docstring 原文陈述，非本文推断。

来源：[jiuwenswarm/common/mcp_config.py:L440–L448](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L440-L448)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":448,"path":"jiuwenswarm/common/mcp_config.py","sha256":"7b86e74eb00b211037d3ba62f0853e3a4be621ab001f33b29683b71abfe136c5","start":440}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=mcp facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be0cf2f54c297c601b3d50b3397c712e30316c7bffb45828216e0ddfeec6b7db -->
**已有运行时单测（断言可见，本轮未执行）：占位符保留字面量；prewarm 挂起不中断**
test_stdio_env_placeholder_missing_kept_literal 用 monkeypatch.delenv 加空 resolver，断言 cfg.params["env"]["K"] == "${NONEXISTENT_VAR}"；test_prewarm_times_out_a_hung_mcp_and_continues 把 probe 替换为 sleep 3600、_PREWARM_STALL_TIMEOUT_S=0.1，断言 set(attempted) == {"hung","good"} 且耗时 <0.5s（probe 被打桩，只覆盖 prewarm 的停顿护栏）。

来源：[tests/unit_tests/agentserver/mcp/test_mcp_config_placeholder.py:L60–L68](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/mcp/test_mcp_config_placeholder.py#L60-L68), [tests/unit_tests/agentserver/test_mcp_startup_prewarm.py:L65–L88](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_mcp_startup_prewarm.py#L65-L88)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":68,"path":"tests/unit_tests/agentserver/mcp/test_mcp_config_placeholder.py","sha256":"45f9e9cc85b89be6716c16ad06a9ca70d2346cf3173ba6ebab37d3ea76e2df93","start":60},{"end":88,"path":"tests/unit_tests/agentserver/test_mcp_startup_prewarm.py","sha256":"4270355b6e658a6fbf48ebbd7ddd934fc2c763fb0e14ba87d6fbc208781af391","start":65}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=mcp facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=379e943cbaa2117eac34a3f618f0f682da3e4286cbfed9562f0fe1661a780de0 -->
**probe_mcp_live_connection 各分支返回 (ok, reason)；try 外调用不保证从不抛出**
空名返回 (False, "mcp name is required")；entry 为 None 返回 (True, "")，cfg 为 None 返回 invalid entry 失败。stdio 且 command 非空不在 PATH 时失败；preflight 不可达返回 reason、自身异常仅 debug 后继续；Runner 导入或 add_mcp_server(tag="mcp.probe") 异常各返回 (False, 原因)，成功按 is_ok()/bool（result 为 None 视为成功）返回 (True, "")；但 entry 读取、cfg 构建、which 与结果检查在 try 之外，不构成从不抛出。

来源：[jiuwenswarm/common/mcp_config.py:L440–L547](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L440-L547)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":547,"path":"jiuwenswarm/common/mcp_config.py","sha256":"9fb10bd5c9c66b115869f07c4c6113c89ae61199f1f5ff437bba7f5777208f10","start":440}],"trace":[]} -->
<!-- /kb:depth -->
