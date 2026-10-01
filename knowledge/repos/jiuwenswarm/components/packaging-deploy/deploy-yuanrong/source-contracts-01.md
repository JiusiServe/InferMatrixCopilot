---
title: "deploy-yuanrong 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# deploy-yuanrong 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=deploy/yuanrong/args_handler.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f855723fe4f63ed84670d3fe07038aedb2aff32ec47977299cca7ba58a7e89e2 -->
**`deploy/yuanrong/args_handler.sh`**

- 源码声明的类型、组件或调用边界：`on`；这是词法声明索引，不把局部变量当成对外导出 API。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/deploy/yuanrong/args_handler.sh#L1-L84)。
<!-- /kb:file -->

<!-- kb:file path=deploy/yuanrong/deploy.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1178d2f09ede489e6790fceeaba2d7fbf4b4e6cddc24218dc9b27383c23d53c7 -->
**`deploy/yuanrong/deploy.sh`**

- 集成边界的导入/加载声明：`source "global_vars.sh"`；`source "common.sh"`；`source "cmd_handler.sh"`；`source "args_handler.sh"`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/deploy/yuanrong/deploy.sh#L1-L67)。
<!-- /kb:file -->
