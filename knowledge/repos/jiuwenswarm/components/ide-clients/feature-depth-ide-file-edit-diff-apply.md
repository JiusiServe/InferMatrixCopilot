---
title: "IDE 端代理文件编辑直接应用（DiffApplier）：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L81-L83, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt:L70-L78, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L112-L119, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt:L309-L310, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70-L85, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L112-L123, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L273-L286, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L75-L79, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70-L82, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L85-L102, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70-L79, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/ide/vscode/VSCode插件指南.md:L307-L320"]
feature: "ide-file-edit-diff-apply"
entry_points: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt", "jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts"]
source_globs: ["jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/ui/ChatToolWindow.kt", "jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts", "jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt", "jiuwenswarm/channels/ide/packages/vscode-extension/src/ui/ChatPanel.ts"]
---

# IDE 端代理文件编辑直接应用（DiffApplier）：实现深读

[功能概览](feature-ide-file-edit-diff-apply.md) · [owner 入口](_index.md)

<!-- kb:depth feature=ide-file-edit-diff-apply facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=37ff09b39b001d2767a6a5e6e99da8a98e26953cd221b9af2e4ac168be0d02cd -->
**handleToolCall 按 EDIT_TOOLS 与参数守卫分派 write_file 到 writeEntireFile**
回调先取 payload.tool_name，不在 EDIT_TOOLS 集合即返回 false；parseArguments 成功后从配置读 requireApproval。write_file/create_file 分支在 args.path 缺失时返回 false，否则以 isNew = create_file 或文件不存在 调 writeEntireFile 并返回其布尔结果。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70–L85](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L70-L85), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L112–L123](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L112-L123), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L273–L286](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L273-L286)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":85,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"8102dcc429f9b102c9851d096d46c2aa21fde92bce6db2e58b36807058f11523","start":70},{"end":123,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"b75a6f3b40a9cdd04e8f0d795565f1088918a1dead997c9d8fb949dfd010dffe","start":112},{"end":286,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"18ef0746434a19320c57529d860fe3b8e3031438f9166d2fb634954d3419abdf","start":273}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7ca04fe2b1f6700c997979ee7e758f150a75e053d028ffe4aafdb7c2f3b19b2f -->
**VS Code 端审批开关 jiuwenswarm.approveEdits，默认 false**
每次调用通过 vscode.workspace.getConfiguration('jiuwenswarm').get('approveEdits', false) 读取，默认不要求审批，布尔值传入 applyStrReplace/writeEntireFile。JetBrains 端对应 settings.approveEdits 与 autoApplyEdits 两个设置。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L81–L83](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L81-L83), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt:L70–L78](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt#L70-L78)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":83,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"dcfba59246d44119c63f46f00b281dfa3a780878ebf697bc7281d788401ce7a3","start":81},{"end":78,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt","sha256":"cb68b126f06a3e2e5605d6f288d132e9cfe0617a7cd2691ccb08d13709be3c95","start":70}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=527ed07f4d333c6e948ff86cdb09d70a31441ae0b2326eccb3344c15cb3d9d9b -->
**依赖 vscode 配置 API、fs 存在性检查与 EDIT_TOOLS 工具名集合**
VS Code 分支依赖 vscode.workspace.getConfiguration 与 fs.existsSync 判定 isNew；JetBrains 端依赖 JiuwenSwarmSettings.instance() 提供设置，EDIT_TOOLS 集合限定四种工具名（str_replace_editor、write_file、create_file、edit_file）。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L112–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L112-L119), [jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt:L309–L310](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt#L309-L310)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":119,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"bf33d17d53064221b4c1e747dad7f7ddbc1773e21b567589c6a147bffbed3cf3","start":112},{"end":310,"path":"jiuwenswarm/channels/ide/packages/jetbrains-plugin/src/main/kotlin/com/jiuwenswarm/plugin/editor/DiffApplier.kt","sha256":"a372efd0757cea5640f2686de40cead4f75748e004e4e2c1c08a1b91d2b1bc2f","start":309}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=523b0543ffe9b6d7b13af1cab895a8b48a8fa3a40f461856fcb2197a44ea7f9c -->
**参数不可解析时 console.warn 并返回 false；path 缺失静默返回 false**
parseArguments 对非对象且非字符串的 arguments 或 JSON.parse 抛错返回 null；handleToolCall 据此记录 console.warn 后返回 false，不进入写分支。write_file 分支中 filePath 为空时直接 return false，无告警。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L75–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L75-L79), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L273–L286](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L273-L286), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L112–L119](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L112-L119)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":79,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"6ddf42bbede9fbffffef2eae0e1e566edac308b32b25cde6d241526ada076145","start":75},{"end":286,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"18ef0746434a19320c57529d860fe3b8e3031438f9166d2fb634954d3419abdf","start":273},{"end":119,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"bf33d17d53064221b4c1e747dad7f7ddbc1773e21b567589c6a147bffbed3cf3","start":112}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=0cf112ec3227b118c5dbfd5de68733600d97ebd0bb70bd8618b9db3d1c147224 -->
**handleToolCall：异步入口，按 tool_name 过滤并在参数可解析时委托各工具分支**
handleToolCall(event) 是 async、返回 Promise<boolean>；payload 缺 tool_name 或不在 EDIT_TOOLS 时返回 false，parseArguments 失败时 console.warn 并返回 false。str_replace_editor 的 'str_replace' 分支要求 args.path 存在且 old_str 已定义（new_str 缺省为 ''），然后委托 applyStrReplace(filePath, oldStr, newStr, requireApproval)；'create' 委托 writeEntireFile。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70–L82](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L70-L82), [jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L85–L102](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L85-L102)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":82,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"1cd472fd5310f8bdb3dacdce3cde278ad2ff55df0553a2286172e10c1b20bf02","start":70},{"end":102,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"84bf128c044cb2f38deb73b372810ece4527e45379826018ef4392fd9080b128","start":85}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1c6b225b64d09a0747360ae8c6697fccdd789fcd530d7efb45c272890e1e4482 -->
**守卫不满足时静默返回 false：控制流简单但无用户提示**
设计推断（非作者历史意图）：

（推断）入口对缺失或未列入 EDIT_TOOLS 的 tool_name 直接返回 false、不做提示，仅参数解析失败才 console.warn；这换来简单的调用方布尔语义，代价是守卫分支对用户不可见。

来源：[jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts:L70–L79](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts#L70-L79)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":79,"path":"jiuwenswarm/channels/ide/packages/vscode-extension/src/editor/DiffApplier.ts","sha256":"b1265c8d11fdebc48d1cc7c2c3ecf05e6b8dc1644dae0a07fdf21c4136459087","start":70}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=ide-file-edit-diff-apply facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3001cb15d9cbb9b00cbd826a543e15201dc11773583ea8b55211453291555789 -->
**文档化的手动验证：approveEdits 批准/拒绝提示（未执行）**
文档中的人工验收步骤（本轮未执行）：

文档写明：智能体调用 str_replace_editor / write_file / create_file 时扩展应用编辑并弹通知 toast；启用设置 jiuwenswarm.approveEdits 后每次变更前出现批准/拒绝提示，拒绝丢弃编辑、批准写入磁盘。此为文档步骤，标注 NOT EXECUTED，所示输入无自动化测试。

来源：[docs/zh/ide/vscode/VSCode插件指南.md:L307–L320](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/ide/vscode/VSCode%E6%8F%92%E4%BB%B6%E6%8C%87%E5%8D%97.md#L307-L320)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":320,"path":"docs/zh/ide/vscode/VSCode插件指南.md","sha256":"042472f555477bd25497b4fcc5933fc61b8e838a2e1a8763b735e987828cd887","start":307}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
