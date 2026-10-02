---
title: "交互式命令行：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/_terminal.py:L5-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/chat.py:L5-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/main.py:L5-L7]
feature: "cli"
entry_points: ["jiuwenswarm/cli/main.py"]
source_globs: ["jiuwenswarm/cli/main.py", "jiuwenswarm/cli/*.py"]
---

# 交互式命令行：实现深读

[功能概览](feature-cli.md) · [owner 入口](_index.md)

<!-- kb:depth feature=cli facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6eafd61eaf6cbc8f4dde7e8a511867809832d58fe17cee046c8417faca7bd644 -->
**对 jiuwenswarm.channels.cli 的模块别名耦合**
jiuwenswarm/cli 下的 _terminal.py、chat.py、events.py 通过 sys.modules[__name__] = import_module("jiuwenswarm.channels.cli.*") 把旧路径整体替换为新实现模块；旧导入路径因此可用，但任何对这些名字的模块级操作（如二次赋值）实际落在被替换后的模块上。

来源：[jiuwenswarm/cli/_terminal.py:L5–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/_terminal.py#L5-L8), [jiuwenswarm/cli/chat.py:L5–L8](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/chat.py#L5-L8), [jiuwenswarm/cli/main.py:L5–L7](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/cli/main.py#L5-L7)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/cli/_terminal.py","start":5,"end":8,"sha256":"8ddc5322eaf88623194548b25c38bc813fc3dc2d798ca97f4a2894741c750f24"},{"path":"jiuwenswarm/cli/chat.py","start":5,"end":8,"sha256":"692dba13e86e9281737a579ac2df79a3cfa329bcecd6b6625fdb39dfd02ae95a"},{"path":"jiuwenswarm/cli/main.py","start":5,"end":7,"sha256":"477cfe72cf6b8e66ed60a4528be3a10570f96ac2f21a5fffacf5d7aae3230cb8"}],"trace":[]} -->
<!-- /kb:depth -->
