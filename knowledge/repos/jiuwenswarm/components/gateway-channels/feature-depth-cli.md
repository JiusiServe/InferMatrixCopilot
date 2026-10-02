---
title: "交互式命令行：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/_terminal.py:L5-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/chat.py:L5-L8, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/cli/main.py:L5-L7, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/cli/main.py:L19-L21, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/channels/cli/main.py:L29-L36, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/命令行指令.md:L228-L235"]
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

<!-- kb:depth feature=cli facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=ee8ffd6874595ec32c5e391cbaa21a63670894642d96f9ea04d690f2029a35d8 -->
**JIUWENSWARM_SKIP_DOTENV 与 .env 优先级**
环境变量 JIUWENSWARM_SKIP_DOTENV 未设置或不等于 "1"（strip 后比较）时，main 启动时执行 load_dotenv(dotenv_path=get_env_file(), override=False)：已存在的进程环境变量优先于 .env 文件中的同名值；设为 "1" 则跳过这段加载，但导入阶段的 parse_dotenv_early("jiuwenswarm") 仍先行执行，不受该开关控制。文档另给出 --mode 默认 code.normal、--gateway-url 默认 ws://127.0.0.1:19001/tui。

来源：[jiuwenswarm/channels/cli/main.py:L19–L21](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/cli/main.py#L19-L21), [jiuwenswarm/channels/cli/main.py:L29–L36](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/channels/cli/main.py#L29-L36), [docs/zh/命令行指令.md:L228–L235](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%91%BD%E4%BB%A4%E8%A1%8C%E6%8C%87%E4%BB%A4.md#L228-L235)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":21,"path":"jiuwenswarm/channels/cli/main.py","sha256":"3090d4f1cabe879c39d99b19384d6c20c4873b0a50f8245b254162847f1e901a","start":19},{"end":36,"path":"jiuwenswarm/channels/cli/main.py","sha256":"182353e75ac384a2e571cffc0b4c01099a45e30fb68488983309f189cc4d15cf","start":29},{"end":235,"path":"docs/zh/命令行指令.md","sha256":"9813474f2c6f782731dfec8a3c40586f7fde304c43dda8bbe0ce7c5e23851425","start":228}],"trace":[]} -->
<!-- /kb:depth -->
