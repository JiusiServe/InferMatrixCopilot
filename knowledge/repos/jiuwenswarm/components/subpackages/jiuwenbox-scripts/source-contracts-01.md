---
title: "jiuwenbox-scripts 源码接口与集成边界 01"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: []
---

# jiuwenbox-scripts 源码接口与集成边界 01

本页逐文件说明这一源码模块声明的接口、类型与依赖。记录来自静态源码声明，不证明控制流、配置生效、外部服务可用或测试通过；功能语义与设计取舍沿上级功能页继续阅读。

<!-- kb:file path=jiuwenbox/scripts/build_docker.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f06707edb870366132811671a43af784e26f4bf91a07c93326d20a950707cdfe -->
**`jiuwenbox/scripts/build_docker.sh`**

- 脚本执行边界：`docker build -f "$PROJECT_DIR/docker/Dockerfile" -t "$IMAGE_REF" "$PROJECT_DIR" "$@"`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/scripts/build_docker.sh#L1-L26)。
<!-- /kb:file -->

<!-- kb:file path=jiuwenbox/scripts/run_docker.sh pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a53e1e14ed9d42caee24b4265ed9216ba3d34097bf37b5cdc1a549370c0b8e6 -->
**`jiuwenbox/scripts/run_docker.sh`**

- 脚本执行边界：`docker run -itd \`。

源码依据：[完整声明与实现](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenbox/scripts/run_docker.sh#L1-L241)。
<!-- /kb:file -->
