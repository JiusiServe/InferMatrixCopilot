---
title: "YuanRong Agent 容器文件传输（上传/下载/列举/建目录）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L804-L812, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L469-L479, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L489-L549, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L698-L743, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1027-L1041, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L895-L903, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L55-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L563-L565]
feature: "yuanrong-agent-file-transfer"
entry_points: ["jiuwenswarm/extensions/yuanrong_frontend_client.py"]
source_globs: ["jiuwenswarm/extensions/yuanrong_frontend_client.py", "jiuwenswarm/gateway/channel_manager/web/container_file_http.py"]
---

# YuanRong Agent 容器文件传输（上传/下载/列举/建目录）

<!-- kb:knowledge owner=feature-yuanrong-agent-file-transfer facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**两层结构：YuanRong 前端客户端与网关 HTTP 路由**

下层是 `YuanRongFrontendAgentClient`：同步 HTTP 通过 `asyncio.to_thread` 包成异步，统一经 `bind_southbound_trace_id` 绑定 trace，错误集中在 `_agent_file_http_error` 分类抛 `YuanrongAgentFileError`。上层是 WebChannel 的 `/file-api` 路由（`attach_container_file_routes`）：仅当 `channel.container_file_client` 是 `AgentOSRouterClient` 时挂载，各路由把请求转成 `client.upload/download/list_container_files`、`mkdir_container_dir` 调用。路由前置一个 HTTP 中间件调用 `client.authenticate_http` 做鉴权并把 IAM 身份写入 request.state。下载 `/file-api/download` 有两条分支：`verified_asset_v1` token 经 `fetch_agent_unary` 向 AgentServer 取验证分块；否则从 token 解出 path/session 后走 `download_container_file` 以 64KiB 分块流式输出。所示片段未包含 AgentOSRouterClient 实现，其调用是否落到上述 YuanRong files 接口无法在本次证据内确认。

Sources / 来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L804–L812](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L804-L812), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L469–L479](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L469-L479), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L489–L549](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L489-L549), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L698–L743](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L698-L743)

<!-- kb:knowledge owner=feature-yuanrong-agent-file-transfer facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**关键参数：mode、max_depth 与轮询超时**

`mkdir` 的 `mode` 是可选的：None 或空白字符串归一化为 None（由调用方 umask 决定），仅当给出时才要求匹配 3-4 位八进制数字（如 755 或 0700），否则抛 `YuanrongAgentFileError(BAD_REQUEST)`；网关 `/file-api/mkdir` 同样接受可空的 `mode` 查询参数。`max_depth` 只出现在列举链路（客户端 `list_agent_files` 和网关 `ListFilesQuery`/`_list_container_dir`），mkdir 无此参数；负值处理不对称——客户端抛 `ValueError`（yuanrong_frontend_client.py:902-903），网关返回 HTTP 400（container_file_http.py:564-565）。另外 `wait_until_running` 的超时与重试间隔可由实例属性覆盖，否则用模块常量 `_AGENT_RUNNING_TIMEOUT_SECONDS` / `_AGENT_RUNNING_RETRY_INTERVAL_SECONDS`。

Sources / 来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L1027–L1041](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1027-L1041), [jiuwenswarm/extensions/yuanrong_frontend_client.py:L895–L903](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L895-L903), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L55–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L55-L67), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L563–L565](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L563-L565)

