---
title: MCP 配置、凭据与资源 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/mcp_config.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/MCP配置.md
---

# MCP 配置、凭据与资源 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-mcp facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

MCP 接入合并静态配置与动态服务器状态，再按传输构造客户端。凭据解析、探活和工具暴露各有边界，已保存配置不能替代连接状态验证。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。

<!-- kb:knowledge owner=feature-mcp facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `build_mcp_credential_resolver(name)`；`extract_enabled_mcp_server_entries(config_base)`；`build_mcp_server_config(entry, server_id_scope, credential_resolver)`；`build_enabled_mcp_server_configs(config_base, server_id_scope, resolve_credentials)`；`preflight_mcp_server_reachable(cfg, timeout)`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。

<!-- kb:knowledge owner=feature-mcp facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `mcp.servers`。这些是示例字段，不单独证明源码默认值或全部优先级。 文档中的调用选项包括 `--transport`，适用命令与前置条件沿文档确认。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。

<!-- kb:knowledge owner=feature-mcp facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：MCP 通过 stdio 与 HTTP 等传输复用外部工具服务，扩展工具集合；代价是凭据解析、服务器生命周期和动态工具发现都必须独立管理。静态配置与连接状态可能不同，资源可读与工具可调用也需要分开验证。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。

<!-- kb:knowledge owner=feature-mcp facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

MCP 接入合并静态配置与动态服务器状态，再按传输构造客户端。凭据解析、探活和工具暴露各有边界，已保存配置不能替代连接状态验证。 联调时结合[技能安装、挂载与发现](../agents-team/feature-skills.md)、[模型平台与 API 配置](feature-models.md)、[JiuwenBox 隔离执行](../sandbox-runtime/feature-sandbox.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。

<!-- kb:knowledge owner=feature-mcp facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

添加最小 stdio 或 HTTP 服务，核对凭据解析、探活、工具发现与一次调用。覆盖服务不可达、无效凭据、重载、禁用和资源读取，检查退出后子进程或连接清理。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/common/mcp_config.py:L1–L647](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/mcp_config.py#L1-L647)；[docs/zh/MCP配置.md:L1–L126](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/MCP%E9%85%8D%E7%BD%AE.md#L1-L126)。
