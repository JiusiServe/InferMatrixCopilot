---
title: "连接器市场与 MCP 授权流程：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L14-L30, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146-L169, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L182-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/tests/marketSearchClient.test.mjs:L33-L52, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx:L299-L312, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx:L316-L317, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx:L17-L23, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L220-L232, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L559-L565, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L1-L2, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146-L168, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L171-L179, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L213-L227]
feature: "connectors"
entry_points: ["jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts", "jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx"]
source_globs: ["jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts", "jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx"]
---

# 连接器市场与 MCP 授权流程：实现深读

[功能概览](feature-connectors.md) · [owner 入口](_index.md)

<!-- kb:depth feature=connectors facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b79b9d5a981378d366e22ede958d2a670e94ac8eb8c1df946331474fec678563 -->
**去掉 MOCK FALLBACK、按方法内联字段映射**
设计推断（非作者历史意图）：

事实：mcp.* 方法不再有 tryReal() 包装，失败即抛错，只有后端未实现的 pluginPackagesApi 保留 mock 兜底；snake_case→驼峰转换在每个方法内联（fromRawSummary/fromRawDetail/fromRawConnect），不建通用转换器。推断：这样换来问题不被假数据掩盖、每个响应形状独立可控，代价是字段增减时要在多处内联映射里同步修改，且无兜底时后端故障会直接以错误暴露给用户。

来源：[jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L14–L30](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L14-L30), [jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146–L169](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L146-L169)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","start":14,"end":30,"sha256":"79a296ab2b4790b7e34df699594a8bc930294c175f766c4be502d74f24e02d82"},{"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","start":146,"end":169,"sha256":"123783bff7b7a22e03db130ae9e80b042db9cfbb420975b14eef4a304b46dd1a"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=36fb6891724f7fee581311478a4ad0c26e84c6e47611369ef7d92e8b91556dc9 -->
**上传导入 onConfirm 成功回调：关闭弹窗并置 successToast，success Toast 2600ms 后自动关闭**
回调先 setUploadError(null)，await importPluginLocal({ path })；result.ok 为真时关弹窗并 setSuccessToast(t(...)) 后 return，316–317 行以 variant="success" 渲染 Toast（isError 为假 → setTimeout(onClose, 2600)），onClose 即 setSuccessToast(null)，卸载时 clearTimeout。

来源：[jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx:L299–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx#L299-L312), [jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx:L316–L317](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx#L316-L317), [jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx:L17–L23](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx#L17-L23)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":312,"path":"jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx","sha256":"75c317ef2361f2ca14a58ad00bb6b3d22df98b081b3c88e7cd14d19e8dc05f4e","start":299},{"end":317,"path":"jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx","sha256":"4f748ace428d547c5c659ce61bd0b5d1bcf2a8456dcab4408a1a5a4de55236e8","start":316},{"end":23,"path":"jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/Toast.tsx","sha256":"e335078cd03381b4a60fb068c34f09ed195d05504d5a2f56bb8afeb37f24bec5","start":17}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=e19c3a3ffac90a6dd1cbb43215149208d01d27ce607e1f31077967110c273959 -->
**waitAuth 契约：mcp.wait_auth 携带 name 与 step_index 并用 WAIT_AUTH_TIMEOUT_MS 超时**
waitAuth(name, stepIndex) 调 webRequest('mcp.wait_auth', { name, step_index: stepIndex }, { timeoutMs: WAIT_AUTH_TIMEOUT_MS })，结果经 fromRawConnect 返回 ConnectorConnectResponse；cancelConnect(name) 发 'mcp.cancel_connect'，响应 type:'cancelled' 且 applied 可选。

来源：[jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L220–L232](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L220-L232)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":232,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"1d74e9c33ba4355d54daf09365ab6baa6a81298b517058687affc975c3947c8a","start":220}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=32722bc187b2e96d7486ab94cf8f365aacb1ec33f6085b473e8f3846b17b6e0e -->
**list 的 query='' 默认省略 query 键；filter 无客户端默认**
list 的 query 默认 ''，为空时请求体省略 query 键（...(query ? { query } : {})）且第四参传 !query；filter 无客户端默认值，注释记录后端缺省按 'builtin' 处理，曾实测导致『我的MCP』完全看不到自定义 MCP。

来源：[jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L182–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L182-L194)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":194,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"75c82b9dbc745391c4cc409a542613c288737345ef854db746d3776851da77e4","start":182}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c55c7a349e49514facce44597468b8bcf8a45849ecf452a1d6ef5f04ec420aec -->
**导入失败（result.ok 为假）时错误留在弹窗内 uploadError；rejectAllPending 逐项清定时器并以同一 WebError 拒绝**
onConfirm 中 if (result.ok) 不成立时不执行关闭分支，setUploadError(result.error) 把错误留在打开的弹窗内；webClient.rejectAllPending(error) 一旦被调用（调用点不在所示行），对 this.pending 每项 window.clearTimeout(entry.timeoutId) 并 entry.reject(error)，随后 this.pending.clear()。

来源：[jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx:L299–L312](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx#L299-L312), [jiuwenswarm/channels/web/frontend/src/services/webClient.ts:L559–L565](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/webClient.ts#L559-L565)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":312,"path":"jiuwenswarm/channels/web/frontend/src/components/ConnectorMarket/index.tsx","sha256":"75c317ef2361f2ca14a58ad00bb6b3d22df98b081b3c88e7cd14d19e8dc05f4e","start":299},{"end":565,"path":"jiuwenswarm/channels/web/frontend/src/services/webClient.ts","sha256":"bf50193c4221955b3bb40488fc0ff81725ec8f12d7d3bd27dde7449096808a1b","start":559}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2b53a0e83af32ec8b84dfd058d0a66c91a8b5a342b3c130e48fcec7d751db635 -->
**运行时测试执行 connectorApi.list（stub webClient.request 传输）**
测试 stub webClient.request（'mcp.list' 返回 {items: []}，未预期 method 抛 Unexpected method）后实际执行 connectorApi.list('builtin', '销售')，并以 deepEqual 断言转发序列（49-52 行可见 agent_templates/agent_groups/plugin_packages 三项参数断言）；传输层被 stub，非真实 WS 集成。

来源：[jiuwenswarm/channels/web/frontend/tests/marketSearchClient.test.mjs:L33–L52](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/tests/marketSearchClient.test.mjs#L33-L52)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":52,"path":"jiuwenswarm/channels/web/frontend/tests/marketSearchClient.test.mjs","sha256":"318a5464b2f8f564a606603b5ca36b728d693c817df719db13b27c19cdd7c4a7","start":33}],"trace":[],"validation_kind":"automated_runtime"} -->
<!-- /kb:depth -->

<!-- kb:depth feature=connectors facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=792528cce424de888cecf1859b12a82a4e7b8a53c5e3420b14ee229c35540bd2 -->
**connectorApi 的 connect/waitAuth 依赖 webClient 的 webRequest 并共用 fromRawConnect 映射**
connectorApi.ts 第2行从 './webClient' 导入 webRequest。connect(name) 调 'mcp.connect'（传 { name }），waitAuth(name, stepIndex) 调 'mcp.wait_auth'（传 name 与 step_index），各自传 10 分钟的 timeoutMs 覆盖——注释称 webClient 默认 15s 会让 hold-open 握手在前端先超时。两处响应均经 fromRawConnect 把 installed_skills、server_id_scope、step_index 等原始键映射为驼峰字段。

来源：[jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L1–L2](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L1-L2), [jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L146–L168](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L146-L168), [jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L171–L179](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L171-L179), [jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts:L213–L227](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts#L213-L227)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"f8486f81ae19a87fed97fb7b2e1db77867a2442f182b3df8b5154f9c52d68e68","start":1},{"end":168,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"324d0de47e2212d93c329ec6685ba1eb097f81119156cef59be2669231981c81","start":146},{"end":179,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"2024a845eec040b92e31dc4a90bb11f668dc0e1974d501586cde27dede462ff0","start":171},{"end":227,"path":"jiuwenswarm/channels/web/frontend/src/services/connectorApi.ts","sha256":"f9ec7db45fd8433cf5ca20553ecde699dab9e39adb1ebea6c878a8260be7cd57","start":213}],"trace":[]} -->
<!-- /kb:depth -->
