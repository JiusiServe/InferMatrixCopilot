---
title: "Vite Dev WS Traffic Logger (/__dev/ws-log)：实现深读"
created: 2026-10-07
updated: 2026-10-07
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L409-L441, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L355-L367, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L157-L181, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L368-L382, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L429-L436, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L36-L53, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L89-L142, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L423-L440, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/web/frontend/vite.config.ts:L383-L398]
feature: "dev-ws-traffic-logger"
entry_points: ["jiuwenswarm/channels/web/frontend/vite.config.ts"]
source_globs: ["jiuwenswarm/channels/web/frontend/vite.config.ts", "jiuwenswarm/channels/web/frontend/src/components/LogsPanel/index.tsx", "jiuwenswarm/channels/web/app_web.py"]
---

# Vite Dev WS Traffic Logger (/__dev/ws-log)：实现深读

[功能概览](feature-dev-ws-traffic-logger.md) · [owner 入口](_index.md)

<!-- kb:depth feature=dev-ws-traffic-logger facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=eb5618d119c5a559ffebfc81acfebd1bc339a1c13a45c3f1c2fdea208f36a024 -->
**POST 回调累积请求体、脱敏后以 JSONL 追加写入日志**
POST 分支用 req.on('data') 累积 raw，end 回调尝试 JSON.parse（失败保留原文），经 maskSensitive 脱敏后写成 `{ts,payload}` 行 append 到 ws-dev.log，成功返回 200 {ok:true}。

来源：[jiuwenswarm/channels/web/frontend/vite.config.ts:L409–L441](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L409-L441)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":441,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"b925a2a996c70957f2bc9563f3cf6b381abf5dd26eaff7f41cd35c691f031dc7","start":409}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dev-ws-traffic-logger facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1d3832da8a16b20e09ac0cc0c67f7a900291858a38200e163a4423d9d3efbabd -->
**limit 查询参数默认 300，非有限回退 300，有效值夹在 1–2000**
日志路径固定由 resolveProjectRootDir() 推导为 agent/.logs/ws-dev.log；configureServer 时 mkdirSync 递归建目录并 writeFileSync 清空文件。GET 的 limit 缺省 '300'，Number.isFinite 不满足时取 300，否则 clamp 到 1–2000。

来源：[jiuwenswarm/channels/web/frontend/vite.config.ts:L355–L367](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L355-L367), [jiuwenswarm/channels/web/frontend/vite.config.ts:L157–L181](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L157-L181)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":367,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"7b6dcc7fa6f212d3a0d034f9ccb57f8296bbdef598bb9e05bd083a2760a91311","start":355},{"end":181,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"db2805c2db7f016f3b2d41315f5dd9b3f6f9fbf4e86dfbaff506cf2591488374","start":157}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dev-ws-traffic-logger facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=9fb9d5b37a24cbcb54a1d74680ce722530c0ac25baec4678204ba503ca9d2dd4 -->
**POST 写盘前调用本地 maskSensitive，敏感键值整体掩码但空值/已脱敏/哈希异常有例外**
POST 'end' 回调调用同文件的 maskSensitive（L427），后者递归处理对象/数组，键名命中 looksSecretKey 时将值经 maskWithFp 替换为 ******(fp:..)，字符串值再经 maskValueShapes 兜底；maskWithFp 内部空值返回 '******'、已脱敏值原样返回、createHash 异常返回 '******'。中间件本身依赖 fs（mkdirSync/writeFileSync/readFile/appendFile）与 path 解析 agent/.logs/ws-dev.log。与后端 SensitiveDataFilter 一致仅为注释声明。

来源：[jiuwenswarm/channels/web/frontend/vite.config.ts:L36–L53](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L36-L53), [jiuwenswarm/channels/web/frontend/vite.config.ts:L89–L142](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L89-L142), [jiuwenswarm/channels/web/frontend/vite.config.ts:L423–L440](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L423-L440)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":53,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"4edafbadf1043f5d35ff42d8398d01aeb90224d129742d5614d68059ec6ffce5","start":36},{"end":142,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"a9ffc3125110419e47285a6b6b673aaef345949bad3852e7525401ac489674d9","start":89},{"end":440,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"b32c34cc6046af1d9998e1a11c2f1b0774862cca2fe41f9d7578aa642eaa9ef7","start":423}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dev-ws-traffic-logger facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=da4ca50d1e900150490997997aa64c2563e451d01507dd8ab4f5889af98091be -->
**读错误 ENOENT 返回 200 空列表，其余 500；写失败 500**
GET fs.readFile 出错且 code==='ENOENT' 时返回 200 {ok:true,entries:[],count:0}；其他读错误记 logger.error 并返回 500 {ok:false,error:'read_failed'}。POST appendFile 出错记 logger.error 并返回 500 {ok:false,error:'write_failed'}。

来源：[jiuwenswarm/channels/web/frontend/vite.config.ts:L368–L382](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L368-L382), [jiuwenswarm/channels/web/frontend/vite.config.ts:L429–L436](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L429-L436)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":382,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"34b71d58a3116f4db32c3ab1ffd7ae12e2c19f1757ea1d0c4496cdbc4105396e","start":368},{"end":436,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"3660a72af85adaad6b015f207f7338692b2f0b2870250eabfce3fafa1c057174","start":429}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=dev-ws-traffic-logger facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7c8b4e398be11f285c5ca53e67be2f95c7910c9337de00929f98dc315418b90c -->
**每次 dev 启动清空日志便于排查，但代价是该文件中的历史条目被覆盖**
设计推断（非作者历史意图）：

configureServer 里 mkdirSync 后 writeFileSync(logFile,'') 清空 ws-dev.log，注释说明是为避免历史数据干扰排查（收益）。成本（推断）：GET 走 readFile 全量读取再 slice(-limit)，日志增长时读取与解析开销随之增加；且清空使该文件中此前记录的条目不再可查。

来源：[jiuwenswarm/channels/web/frontend/vite.config.ts:L355–L367](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L355-L367), [jiuwenswarm/channels/web/frontend/vite.config.ts:L383–L398](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/web/frontend/vite.config.ts#L383-L398)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":367,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"7b6dcc7fa6f212d3a0d034f9ccb57f8296bbdef598bb9e05bd083a2760a91311","start":355},{"end":398,"path":"jiuwenswarm/channels/web/frontend/vite.config.ts","sha256":"007e1b3276b76b77b0384fb94122daf9f4f4a9b07337252c81a7b293faf1caae","start":383}],"trace":[]} -->
<!-- /kb:depth -->
