---
title: "Auto Harness 评测优化：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L961-L980, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py:L880-L958]
---

# Auto Harness 评测优化：实现深读

[功能概览](feature-auto-harness.md) · [owner 入口](_index.md)

<!-- kb:depth feature=auto-harness facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=3ed54ef3378de2b3fdb41fd41a541fae7e877eb6141b80c41c815f3bc08c965f -->
**模型回退配置与环境变量**
当请求未携带 Model 时，AutoHarnessService._build_model_from_env 依次读取环境变量 API_KEY、API_BASE（回退 BASE_URL）、MODEL_NAME（回退 MODEL）；API_KEY 或 MODEL_NAME 缺失时记录 warning 并返回 None，否则以 temperature=0.95 构造 Model。git 分支默认值方面：git_base_branch 未设置时默认 "develop"，且 pipeline_preference 为 EXTENDED_EVOLVE_PIPELINE 时强制 "develop"；git_remote 未设置时默认 "origin"。

来源：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L961–L980](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L961-L980), [jiuwenswarm/agents/harness/common/auto_harness/service.py:L880–L958](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L880-L958)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","start":961,"end":980,"sha256":"2b4aea00c9530897916b3acd5717c1167c24de61f14990a1168df9ffce9fc7ca"},{"path":"jiuwenswarm/agents/harness/common/auto_harness/service.py","start":880,"end":958,"sha256":"61014a73abf4d5d8f7239efc2d7b13acc6fd742f12444f53151cd6c2b93895cd"}],"trace":[]} -->
<!-- /kb:depth -->
