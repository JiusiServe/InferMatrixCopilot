---
title: "Worktree 隔离工作：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860-L1870]
---

# Worktree 隔离工作：实现深读

[功能概览](feature-worktree.md) · [owner 入口](_index.md)

<!-- kb:depth feature=worktree facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=23e5fcc71f1e0d4690a0cdf2677d048c34643908cab9bf2aa0d8df1f38e49522 -->
**构造失败降级为禁用**
WorktreeRail 构造抛出任意 Exception 时被 except Exception 捕获，仅记录一条包含异常信息的 warning（"WorktreeRail create failed"），随后返回 None，不缓存失败状态——下一次调用会重新尝试构造。

来源：[jiuwenswarm/server/runtime/agent_adapter/interface_code.py:L1860–L1870](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/server/runtime/agent_adapter/interface_code.py#L1860-L1870)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/server/runtime/agent_adapter/interface_code.py","start":1860,"end":1870,"sha256":"18043274369a327dc1ddb9c3a92db2e5c2eaacb8d2edc77683a8465d3f3de580"}],"trace":[]} -->
<!-- /kb:depth -->
