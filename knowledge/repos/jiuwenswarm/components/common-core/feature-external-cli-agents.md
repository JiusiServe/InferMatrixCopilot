---
title: 外部 Claude 与 Codex CLI 智能体的职责、接口与配置
created: '2026-10-01'
updated: '2026-10-01'
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/设置与频道升级迁移指南.md
---

# 外部 Claude 与 Codex CLI 智能体的职责、接口与配置

本页提供该能力的基本知识与验证入口，固定基线 `f0a69728c96b`。

<!-- kb:knowledge owner=feature-external-cli-agents facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

外部 CLI 智能体通过受管理的可选运行时接入，runtime 模块负责状态、安装、激活路径与安装后校验，catalog 模块探测宿主已安装 CLI 并校正内置模型目录。设置迁移文档将三方 Agent 限定在集群模式；它与 JiuwenSwarm 自带 process CLI 频道或交互命令行不是同一个接入边界。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

<!-- kb:knowledge owner=feature-external-cli-agents facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

运行时入口包括 get_external_cli_runtime_status、install_external_cli_runtime、install_external_cli_runtime_from_artifacts、activate_external_cli_runtime_paths 与 pinned_sdk_requirements。模型目录通过 reconcile_builtin_models 和 refresh_external_cli_builtin_models 校正；CLI 探测有超时，运行时安装有独立校验，因此状态和模型列表应分别核对。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

<!-- kb:knowledge owner=feature-external-cli-agents facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

设置中的 Claude 与 Codex 分别声明 enabled、use_builtin 和 cli_path；取消使用内置 CLI 后可检测或选择文件路径。受管理安装读取发布 artifact manifest，并检查下载 wheel 的 sha256；路径激活、宿主平台与固定 SDK 版本影响运行时可用性，不能只根据已填写路径认定 CLI 能执行。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

<!-- kb:knowledge owner=feature-external-cli-agents facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：受管理运行时与版本化 artifact 便于桌面安装保持一致，代价是需要处理平台差异、下载校验和并发安装。实现使用安装锁与 staging，再校验和替换运行目录；用户选择外部 CLI 路径更灵活，但模型目录、认证与可执行程序仍须在同一宿主环境验证。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

<!-- kb:knowledge owner=feature-external-cli-agents facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

用户在实验功能启用三方 Agent 并选择内置或自定义 CLI，宿主检查运行时后将模型目录与真实 CLI 能力对齐，供集群协作路径消费。该能力关联 Team、模型选择和桌面打包；外部 CLI 被识别、SDK 包安装成功和能够完成一次真实协作任务是不同验证步骤。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

<!-- kb:knowledge owner=feature-external-cli-agents facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

检查各平台内置运行时与自定义路径，覆盖下载校验失败、并发安装锁、CLI 探测超时和模型目录变化。之后在集群模式核对真实协作输出与选用模型；本页未下载或安装外部工具，也未执行带认证的上游 CLI 请求。

源码与文档：[jiuwenswarm/common/external_cli_runtime.py:L1–L1022](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L1-L1022)；[jiuwenswarm/common/external_cli_catalog.py:L1–L170](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L1-L170)；[docs/zh/设置与频道升级迁移指南.md:L1–L211](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E8%AE%BE%E7%BD%AE%E4%B8%8E%E9%A2%91%E9%81%93%E5%8D%87%E7%BA%A7%E8%BF%81%E7%A7%BB%E6%8C%87%E5%8D%97.md#L1-L211)。

关联阅读：[team](../agents-team/feature-team.md)；[models](feature-models.md)；[desktop](../launch/feature-desktop.md)；[process-cli](../gateway-channels/feature-process-cli.md)。
