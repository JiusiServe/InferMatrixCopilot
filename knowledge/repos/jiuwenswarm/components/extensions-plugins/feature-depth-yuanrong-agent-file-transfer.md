---
title: "YuanRong Agent 容器文件上传/下载/列举/建目录：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1304-L1332, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1315-L1324, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L618-L626, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L1333-L1369, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/extensions/test_yuanrong_frontend_client.py:L1171-L1183, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/yuanrong_frontend_client.py:L924-L967]
feature: "yuanrong-agent-file-transfer"
entry_points: ["jiuwenswarm/extensions/yuanrong_frontend_client.py"]
source_globs: ["jiuwenswarm/extensions/yuanrong_frontend_client.py", "jiuwenswarm/gateway/channel_manager/web/container_file_http.py"]
---

# YuanRong Agent 容器文件上传/下载/列举/建目录：实现深读

[功能概览](feature-yuanrong-agent-file-transfer.md) · [owner 入口](_index.md)

<!-- kb:depth feature=yuanrong-agent-file-transfer facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=be708e07f82a1cae29d3cbb40b48a9cae194f68a5944bd5ed2b6c30c52481d74 -->
**mkdir_agent_dir：strip 校验、NUL 仅查 path 后经 asyncio.to_thread 发送并解析**
调用 mkdir_agent_dir 后先 _ensure_connected，将 instance_id 与 path 各自 strip 并在为空时抛 ValueError；随后仅对 normalized_path 检查 "\x00"，命中则抛 http_status=400、error_code=BAD_REQUEST 的 YuanrongAgentFileError。通过后经 _normalize_mkdir_mode 规整 mode，bind_southbound_trace_id 绑定 trace，asyncio.to_thread 调 _do_agent_file_mkdir 发送请求，并把 body/status/normalized_path 交给 _parse_agent_file_mkdir_response 返回 dict。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L924–L967](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L924-L967)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":967,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"5d992c35990e1406161a07390737503239bb48eee22d46f35fc7cdcc1315d3c0","start":924}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-agent-file-transfer facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9e216dd96d4537460eecfff84b3d467f67f84e17602c96f518f1d131755a6016 -->
**_do_agent_file_download 以带 Range 头的同步 GET 返回 (status, data, content_type, total_size)**
对 _agent_files_download_url 发 GET，头含 Accept: */*、合并后的 auth 头与 bytes={offset}-{end} Range；成功路径读取响应体并从 Content-Range 解析 total_size（回退 offset+Content-Length），把状态、数据、类型与总大小打包返回给调用方处理。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L1304–L1332](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1304-L1332)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1332,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"6154ae7ed3f6b2e625e74b5dbfe7bd8a2494162808d49e69ae6d372a8020eb01","start":1304}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-agent-file-transfer facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6d0f186ab3b606ce01519dee27c0b762e9854755cb77eeaa95c90e5ce84e78d8 -->
**文件下载直接依赖 urllib.request 同步 HTTP，web 层依赖 client.download_container_file**
_do_agent_file_download 内联使用 urllib.request.urlopen 完成 HTTP；后果是每次块下载为同步阻塞调用。raw_file_get 通过闭包 _one_chunk 调用 client.download_container_file，并以 AgentOSFileTransferError 作为可识别的错误契约分支。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L1315–L1324](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1315-L1324), [jiuwenswarm/gateway/channel_manager/web/container_file_http.py:L618–L626](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/web/container_file_http.py#L618-L626)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1324,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"49f6c39c1e3b71df125a10f2c2248aa05eded192a6607f8d5787b02100929e3b","start":1315},{"end":626,"path":"jiuwenswarm/gateway/channel_manager/web/container_file_http.py","sha256":"1b3ad7ee44ce72883219943764902bb575406c2b288c900fdccf7dba657cb648","start":618}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-agent-file-transfer facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=16b4b65fceab0834b44b771217780b4cdb5dcd9544dd7a258abb6b2cf1ec726d -->
**下载 HTTPError 不抛出而返回错误状态元组；超时抛 YuanrongAgentApiError，416 降级为 info 日志**
HTTPError 分支读取错误体并返回 (status, body, content_type, total_size) 交由上层判定，仅记录日志（status==416 用 info，其余 error）；其他异常中若 _is_timeout_error 命中则抛 YuanrongAgentApiError("file download timeout after {resolved_timeout}s")，否则返回 500 状态元组。

来源：[jiuwenswarm/extensions/yuanrong_frontend_client.py:L1333–L1369](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/yuanrong_frontend_client.py#L1333-L1369)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1369,"path":"jiuwenswarm/extensions/yuanrong_frontend_client.py","sha256":"3a1787357fb580f1c5ac005cdcf5693638cc6e5703e12a8e3d5efbf5b17c4b61","start":1333}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=yuanrong-agent-file-transfer facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c90f34f68874c7e1fbe41af0670c33c5188398e9eaf08e80097007d5100b196c -->
**运行时测试覆盖空路径与 NUL 路径的本地拒绝分支**
test_mkdir_agent_dir_rejects_empty_path 断言 path 为空白时抛出 match="path is required" 的 ValueError；test_mkdir_agent_dir_rejects_nul_path 断言含 \x00 的 path 抛出 YuanrongAgentFileError 且 error_code == "BAD_REQUEST"。此为已存在的自动化运行时用例，此处未执行。

来源：[tests/unit_tests/extensions/test_yuanrong_frontend_client.py:L1171–L1183](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/extensions/test_yuanrong_frontend_client.py#L1171-L1183)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":1183,"path":"tests/unit_tests/extensions/test_yuanrong_frontend_client.py","sha256":"fdb1a1484127399cae8f25b66578f7c273dbc3121981ef6b5e6d93a6873b3c89","start":1171}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->
