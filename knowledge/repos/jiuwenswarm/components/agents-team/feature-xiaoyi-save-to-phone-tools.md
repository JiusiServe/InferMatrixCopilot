---
title: "小艺保存到手机工具（save_media_to_gallery / save_file_to_file_manager）"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L43-L54, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L51-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L21-L26, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L102-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L227-L255, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L164-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60-L67, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L74-L81, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L85-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29-L40, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L25-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L74-L92]
feature: "xiaoyi-save-to-phone-tools"
entry_points: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py", "jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py"]
---

# 小艺保存到手机工具（save_media_to_gallery / save_file_to_file_manager）

<!-- kb:knowledge owner=feature-xiaoyi-save-to-phone-tools facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**channels.xiaoyi 上传配置**

工具从全局配置的 `channels.xiaoyi` 读取三个键：`file_upload_url`（OBS 服务 base_url）、`api_key`、`uid`，用于构造 `XiaoyiObsUploadConfig`。base_url 和 api_key 缺失（或 uid 缺失）时抛 `ToolInputError`；注意 `uid` 经 `str(xc.get("uid"))` 转换，缺失时变成真值字符串 `"None"`，因此缺失的 uid 实际不会触发该错误。请求侧将 uid 同时用作 header（`x-uid`）和 `fileOwnerInfo` 的 `uid`/`teamId`，api_key 走 `x-api-key`，并固定附带 `x-request-from: openclaw`。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L43–L54](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L43-L54), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L51–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L51-L59)

<!-- kb:knowledge owner=feature-xiaoyi-save-to-phone-tools facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**命令组装与执行流程**

工具在 save_tools.py 内直接完成参数校验、本地文件上传换公网 URL（`_ensure_public_url` 通过 aiohttp 会话调用 `upload_local_file_public_url`）以及设备命令字典的组装，随后交给共享 `.utils` 的 `execute_device_command` 执行并用 `raise_if_device_error` 检查结果。两个命令均为 Common/Action 事件：图库用 intentName `SaveMediaToGallery`，文件管理器用 `SaveFileToFileManager`，bundleName 都是 `com.huawei.hmos.vassistant`，executeMode 为 background，permissionId 含 `ohos.permission.WRITE_IMAGEVIDEO`。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L21–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L21-L26), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L102–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L102-L146), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L227–L255](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L227-L255)

<!-- kb:knowledge owner=feature-xiaoyi-save-to-phone-tools facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**输入校验与错误处理路径**

工具入口对必填参数与 media_type 枚举做显式校验并抛 ToolInputError；该异常在两个工具的兜底 except 中被原样 re-raise，不记日志也不包装。上传侧的分阶段检查不对称：prepare 除 HTTP 状态外还校验业务码 `code != "0"`，文件上传仅检查 HTTP 状态，completeAndQuery 检查 HTTP 状态且要求返回 `fileDetailInfo.url` 非空，否则抛 RuntimeError。设备执行结果经 `raise_if_device_error` 检查（其实现位于未展示的 .utils 中）。本次输入不含任何测试文件。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L164–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L164-L168), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L60–L67](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L60-L67), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L74–L81](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L74-L81), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L85–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L85-L92)

<!-- kb:knowledge owner=feature-xiaoyi-save-to-phone-tools facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**本地文件上传换公网 URL 的三段式 OBS 流程**

当 url 不是 `http://`/`https://` 开头时，工具将其视为本地路径，通过 `upload_local_file_public_url` 上传：先同步读入整个文件并计算 SHA-256，POST `{base}/osms/v1/file/manager/prepare`（携带 `x-uid`、`x-api-key`、`x-request-from: openclaw` 头，校验业务码 `code == "0"`），再按 prepare 返回的 `uploadInfos[0]` 的 method（缺省 PUT）、url 和服务端给的 headers 上传文件内容，最后 POST `completeAndQuery` 并要求返回 `fileDetailInfo.url` 非空；任一步失败抛 RuntimeError。已是 http(s) 的 URL 则直接透传，跳过上传。objectType 固定为 `TEMPORARY_MATERIAL_DOC`。

Sources / 来源：[jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py:L29–L40](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/save_tools.py#L29-L40), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L25–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L25-L59), [jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py:L74–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/xiaoyi_phone_tools/file_upload_helpers.py#L74-L92)

