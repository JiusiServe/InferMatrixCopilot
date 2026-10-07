---
title: "@path 文件引用内联与 @agent 提及解析：实现深读"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2909-L2915, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_at_file_references.py:L20-L22, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_at_file_references.py:L9-L13, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_at_file_references.py:L177-L180, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2846-L2866, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2882-L2908, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2846-L2871, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2873-L2915]
feature: "at-file-reference-inlining-b1a822e1"
entry_points: ["jiuwenswarm/gateway/message_handler/message_handler.py"]
source_globs: ["jiuwenswarm/gateway/message_handler/message_handler.py"]
---

# @path 文件引用内联与 @agent 提及解析：实现深读

[功能概览](feature-at-file-reference-inlining-b1a822e1.md) · [owner 入口](_index.md)

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3518c32db4d773a42ff16a9348f448fb82f5a98330608285159cd3d6ccb0f648 -->
**pattern.sub 对 content 中的 @path 匹配逐个替换为 file-content 包裹的文件文本**
对传入 content 执行 pattern.sub：每个匹配成功读取的文件被替换为 '\n<file-content path="{raw}">\n{text}\n</file-content>\n'；本切片未显示 pattern 构造与读取主体（2906 之前）。

来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2909–L2915](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2909-L2915)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2915,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"4f53342f5ec71336a85953dfb9fb5aafb68eb286ce584cf28bbf5504e8f4a48c","start":2909}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=95c3ddbcd0474f05a2e6d1715125624d6725660900c2e009ef84bc0cec402b22 -->
**静态方法 resolve_at_file_references(content, cwd=None, max_file_size=_DEFAULT_INLINE_FILE_SIZE_LIMIT) -> str**
Empty content returns as-is. Matched non-agent @path/@"quoted" refs (after #L... suffix strip, ~/ expand, cwd/absolute resolution) that resolve to an existing file are replaced by a <file-content path=...> block; only when max_file_size is None is the whole file read — otherwise reading is capped and oversized files get a truncation suffix. Non-files, OSError/UnicodeDecodeError, and raw values starting agent-/agent: keep the original match. Caller supplies content and optionally cwd; default cwd is os.getcwd().

来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2846–L2871](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2846-L2871), [jiuwenswarm/gateway/message_handler/message_handler.py:L2873–L2915](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2873-L2915)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2871,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"ee69fd5769c5c5b9f06a3a18010dd3ad8a6c85c5c4da4598e9667f083387ebee","start":2846},{"end":2915,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"7783f32c9a5a00875566f037db11a7c281e3c7e45af397f15c6c59de31492af8","start":2873}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=7432856b22077756e8f0f2368149759cf9ec25b7ca1c4ce11271322c48c83b72 -->
**max_file_size 默认 _DEFAULT_INLINE_FILE_SIZE_LIMIT；None 读全文，否则截断加尾注**
参数 max_file_size 默认值为模块常量 _DEFAULT_INLINE_FILE_SIZE_LIMIT（2850，具体数值未在所示片段中给出）。max_file_size 为 None 时整文件读取（2897-2898）；否则读取 max_file_size+1 字符并在超出时截断到 max_file_size，追加 '... (truncated, original_size=N bytes)' 尾注（2900-2908）。相对路径按 cwd（缺省 os.getcwd()，2866）拼接，~/ 前缀展开到用户主目录（2883-2889）。

来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2846–L2866](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2846-L2866), [jiuwenswarm/gateway/message_handler/message_handler.py:L2882–L2908](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2882-L2908)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2866,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"e9ca93cfa0e4aebfb3af4dd3ec00ea9e5a8002e3cfc6fd0bad71c59b8e8cd2d6","start":2846},{"end":2908,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"08f07e1f5961cb76768adee61b8a5731995dc26518a85a82842207dcf6d15416","start":2882}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6555e137e3d23b065055da8ae010d10951de94f2eaceb548d34c7de70d6c41a0 -->
**路径解析以调用方提供的 cwd 为基准（测试用 os.path.basename/dirname 构造）**
设计推断（非作者历史意图）：

测试把消息中的引用写成 basename，并把 cwd 设为 dirname，说明文件解析依赖调用方传入的工作目录而非固定根；这是从测试构造推断的耦合，实现在所提供的切片中不可见。

来源：[tests/unit_tests/gateway/test_at_file_references.py:L20–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_at_file_references.py#L20-L22)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"tests/unit_tests/gateway/test_at_file_references.py","sha256":"6fc1ff23ffda29ba75faa9f069c6f0a558f88ef7322e151cb13fb6663632ec11","start":20}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2d06a6cbf1f8ef0d87c58744107faa6b151203678a2da7116c0f2e2436bef61f -->
**文件读取触发 OSError 或 UnicodeDecodeError 时返回原始匹配串 m.group(0)，异常不外传**
读取文件的 try 块捕获 (OSError, UnicodeDecodeError) 后返回 m.group(0)，即该 @path 引用原文保留在 content 中，替换静默跳过；其他异常路径未在切片中显示。

来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2909–L2915](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2909-L2915)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":2915,"path":"jiuwenswarm/gateway/message_handler/message_handler.py","sha256":"4f53342f5ec71336a85953dfb9fb5aafb68eb286ce584cf28bbf5504e8f4a48c","start":2909}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=438661aef32eb44fba4fa84b909d9cc555a6b5809fd350874c2670a3f14ca8d2 -->
**内联换取自包含，代价是消息体膨胀（依据测试文档字符串推断）**
设计推断（非作者历史意图）：

测试类文档字符串称 @path → <file-content> 内联：收益是代理无需文件系统访问即可看到内容；成本是文件内容进入消息文本，体积随文件增长。此为基于文档字符串与命名的推断。

来源：[tests/unit_tests/gateway/test_at_file_references.py:L9–L13](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_at_file_references.py#L9-L13)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":13,"path":"tests/unit_tests/gateway/test_at_file_references.py","sha256":"8e2352ec5815cb4423e91bf37d8791f145f06384016ea6fad94886034e168d24","start":9}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=at-file-reference-inlining-b1a822e1 facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c0f6749e520ce5cafa77f69500a88d1ff6fbd9ecd412ca27466120505e03acc1 -->
**助手级单测：直接断言无 @ 输入原样返回**
test_no_at_symbol_returns_unchanged 直接调用 MessageHandler.resolve_at_file_references 并断言返回 "hello world"；断言仅覆盖助手本身，非网关消息链路的运行时集成。内联与 strip 用例的断言行未在提供切片内。

来源：[tests/unit_tests/gateway/test_at_file_references.py:L177–L180](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_at_file_references.py#L177-L180)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":180,"path":"tests/unit_tests/gateway/test_at_file_references.py","sha256":"a71c6269ef0b156e2d92ec8b068d922705436be022350d719e748901a2b76fc5","start":177}],"trace":[],"validation_kind":"helper_unit"} -->
<!-- /kb:depth -->
