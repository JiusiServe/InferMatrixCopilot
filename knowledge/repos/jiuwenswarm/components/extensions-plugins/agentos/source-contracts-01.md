---
title: "agentos 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# agentos 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/extensions/agentos/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=c7563262eeeff7328de99d5a68636b798dd01d0794c225fb84f4d0db9daac858 -->
**`jiuwenswarm/extensions/agentos/__init__.py`**

- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.extensions.agentos.agentos_router import AgentCreateFailed`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/__init__.py#L1-L27)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenswarm/extensions/agentos/extension.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=df90b713341bc58a27dd73728f47ff8946473b5994add46a61bbe35b194091ef -->
**`jiuwenswarm/extensions/agentos/extension.py`**

- 源码对模块职责的说明：AgentOS extension entry (discovered by ExtensionLoader).。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from jiuwenswarm.extensions.agentos.agentos_router.extension import AgentOS`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/extensions/agentos/extension.py#L1-L10)。
<!-- /kb:file -->
