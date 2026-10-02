---
title: "生命周期 Hooks 与扩展：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L90-L100, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/extensions/manager.py:L89-L109]
feature: "hooks"
entry_points: ["jiuwenswarm/extensions/manager.py"]
source_globs: ["jiuwenswarm/extensions/manager.py", "jiuwenswarm/extensions/*.py"]
---

# 生命周期 Hooks 与扩展：实现深读

[功能概览](feature-hooks.md) · [owner 入口](_index.md)

<!-- kb:depth feature=hooks facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2f0254f060009147374512b98dbe60b3a8f9e65bdf5a6a262b071b1baebf31cb -->
**transport 扩展按 manifest 标志整体跳过**
设计推断（非作者历史意图）：

Runtime 直连（include_transport_extensions=False）时依据 manifest 的 requires_transport is True 直接跳过整个扩展包并记 info 日志，而不是逐能力选择性挂载。推断：收益是加载路径简单、避免无传输层的宿主挂载不可用扩展；代价是同包内不依赖 transport 的能力也一并丢失，且该过滤完全信任 manifest 声明。

来源：[jiuwenswarm/extensions/manager.py:L90–L100](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L90-L100)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/extensions/manager.py","start":90,"end":100,"sha256":"29ecdb708aaa4663754417b9db05a2c16ec0303367f87ac01dace1d547c23b5f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=hooks facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=10164c78dc93cc1226b1399f4ef62ed50d89fc30ef156d3ea8140b61769af54e -->
**单根路径加载失败的隔离**
load_all_extensions 对每个扩展根路径各自 try/except：当 load_manifest 或 load_extension 抛出任意 Exception 时，108-109 行捕获并 logger.error 记录路径与异常，for 循环继续处理下一个 root，异常不向外重抛。该分支只证明单个失败根路径被跳过且循环继续推进，不构成对其余扩展必然加载成功的保证。

来源：[jiuwenswarm/extensions/manager.py:L89–L109](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/manager.py#L89-L109)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":109,"path":"jiuwenswarm/extensions/manager.py","sha256":"0a2cb91d16a87efa1e1f199f995898cdeac50188604baa608f89bf36394feb54","start":89}],"trace":[]} -->
<!-- /kb:depth -->
