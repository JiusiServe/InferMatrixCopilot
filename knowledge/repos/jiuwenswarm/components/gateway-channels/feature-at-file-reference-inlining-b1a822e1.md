---
title: "@path 文件引用内联与 @agent 提及解析（MessageHandler）"
created: 2026-10-06
updated: 2026-10-07
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2873-L2915, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2917-L2944, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2882-L2889, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2950-L2987, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L3007-L3039, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2878-L2913, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2928-L2935, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2891-L2913, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_agent_mentions.py:L75-L77, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2917-L2924, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2846-L2866, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/message_handler/message_handler.py:L2895-L2908]
feature: "at-file-reference-inlining-b1a822e1"
entry_points: ["jiuwenswarm/gateway/message_handler/message_handler.py"]
source_globs: ["jiuwenswarm/gateway/message_handler/message_handler.py"]
---

# @path 文件引用内联与 @agent 提及解析（MessageHandler）

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**公开入口与行为契约**

`MessageHandler.resolve_at_file_references(content, ...)` 通过正则替换把 `@path` 引用替换为 `<file-content path="...">` 块；非文件路径、`@agent-`/`@agent:` 前缀及读取异常（OSError、UnicodeDecodeError）时原样保留匹配文本。`extract_agent_mentions(content)` 是静态方法，解析 `@"<type> (agent)"` 与 `@agent-<type>` 两种格式，返回去掉 `agent-` 前缀的类型名并去重——注意其保序是“按格式分组”的顺序：先收集全部引号格式再收集全部非引号格式（如 `@agent-a @"b (agent)"` 返回 `["b", "a"]`），并非消息中的出现顺序。

Sources / 来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2873–L2915](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2873-L2915), [jiuwenswarm/gateway/message_handler/message_handler.py:L2917–L2944](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2917-L2944)

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**解析流程与路径解析的分布**

附件流程为：`_resolve_structured_attachments` 调用 `_normalize_structured_attachments`（解析路径、按已解析路径去重、补全 type 默认 `file` 与 filename），再把附件拼成 `@"path"` 前缀、经 `strip_attached_mentions` 清理后调用 `resolve_at_file_references` 内联。路径解析逻辑存在两份并行实现：`_resolve_reference_path`（L2951–L2957，供附件与 strip 使用）与 `resolve_at_file_references` 内部 `_replacer` 中的相同 `~/`/绝对/相对规则（L2883–L2889），并非集中一处。`strip_attached_mentions` 的正则支持引号/裸路径及可选 `#suffix`，仅当解析路径命中附件集合时才把 `@` 锚点剥掉，否则整段原样保留（L3018–L3021）。

Sources / 来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2882–L2889](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2882-L2889), [jiuwenswarm/gateway/message_handler/message_handler.py:L2950–L2987](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2950-L2987), [jiuwenswarm/gateway/message_handler/message_handler.py:L3007–L3039](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L3007-L3039)

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**支持的语法与依赖**

文件引用内联跳过 `agent-`/`agent:` 前缀的裸引用，将存在的文件内容包进 `<file-content path="原始引用">` 块，截断时附 `... (truncated, original_size=N bytes)` 后缀；读取用 `errors="replace"` 容忍非 UTF-8 字节。agent 提及支持 `@"<type> (agent)"`（引号格式）与 `@agent-<type>`（裸格式），类型名字符类为 `[\w:.@-]+`，返回去重列表（保序按格式分组顺序）。

Sources / 来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2878–L2913](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2878-L2913), [jiuwenswarm/gateway/message_handler/message_handler.py:L2928–L2935](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2928-L2935)

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**取舍与限制**

Inference / 设计推断（非作者历史意图）：

引用解析采取“静默降级”策略：路径不存在、OSError 或 UnicodeDecodeError 都原样返回匹配文本（L2893–L2894、L2912–L2913），调用方无法从返回值区分“非文件引用”与“读取失败”；且因 `errors="replace"`（L2898、L2900），实际到达 except 的 UnicodeDecodeError 很少触发，坏字节被替换字符吞掉而非保留原文。截断按字符切片而非字节（L2904–L2905），换取实现简单但限制不严格。无意图方面的文档证据，此分析为基于代码的推断。

Sources / 来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2891–L2913](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2891-L2913)

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**现有测试入口**

`tests/unit_tests/gateway/test_agent_mentions.py` 直接针对该特性，其中 `test_empty` 调用 `MessageHandler.extract_agent_mentions("no mentions here")` 并断言返回空列表，验证无提及时的安全返回（该方法对空/无匹配内容返回 `[]`，见 L2923–L2924）。该文件共 88 行，覆盖 `extract_agent_mentions` 的解析行为；但所示片段未包含针对 `resolve_at_file_references`、截断或附件合并路径的测试，这些行为在所示输入中的验证情况未知。

Sources / 来源：[tests/unit_tests/gateway/test_agent_mentions.py:L75–L77](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_agent_mentions.py#L75-L77), [jiuwenswarm/gateway/message_handler/message_handler.py:L2917–L2924](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2917-L2924)

<!-- kb:knowledge owner=feature-at-file-reference-inlining-b1a822e1 facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**内联行为的可调参数与默认值**

`resolve_at_file_references` 没有读取外部配置文件，其行为由两个调用参数控制：`cwd`（默认 `None`，回退 `os.getcwd()` 作为相对路径基准）与 `max_file_size`（默认取模块常量 `_DEFAULT_INLINE_FILE_SIZE_LIMIT`）。当 `max_file_size` 传 `None` 时跳过截断逻辑，直接 `read_text` 读入整个文件；有上限时按 `max_file_size + 1` 读取并在超限时截断，附 `... (truncated, original_size=N bytes)` 后缀。常量本身的具体数值与调用方是否覆盖默认值未在所示片段中出现。

Sources / 来源：[jiuwenswarm/gateway/message_handler/message_handler.py:L2846–L2866](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2846-L2866), [jiuwenswarm/gateway/message_handler/message_handler.py:L2895–L2908](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/message_handler/message_handler.py#L2895-L2908)

