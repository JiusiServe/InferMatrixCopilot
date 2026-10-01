---
title: "skill-retrieval 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# skill-retrieval 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenswarm/symphony/skill_retrieval/__init__.py pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=64b90503267e089b45750dfe1be68b3df35c217ac1c83c54a427d2d9362d5b82 -->
**`jiuwenswarm/symphony/skill_retrieval/__init__.py`**

- 源码对模块职责的说明：JiuwenSwarm adapter for Symphony's optional Skill taxonomy index.。
- 集成依赖（导入声明，不等于全部运行时依赖）：`from .runtime import SkillTaxonomyRuntime`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/skill_retrieval/__init__.py#L1-L5)。
<!-- /kb:file -->
