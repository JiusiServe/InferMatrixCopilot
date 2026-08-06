---
title: "AFD plugin 组件入口"
created: 2026-08-06
updated: 2026-08-06
type: index
tags: [afd-plugin, components]
sources:
  - "afd-plugin@a432692:docs/design/module/index.md"
---

# AFD plugin 组件入口

## 什么时候查这里

- 已知 changed file，需要定位唯一知识 owner、风险边界和 focused tests。
- 调查跨 Attention/FFN、connector、model、platform 或 compatibility 的调用链。

## 不放什么

- 仓库级默认门禁放 [仓库规则](../rules.md)。
- 通用 review、debug 或 CI 方法放 [general](../../../general/_index.md)。
- adapter `modules` 服务 changed-path 风险路由；本目录服务人类知识 owner，两者目的不同但本次使用同一七 owner 边界。

## Owner 映射

所有路径已对照 `afd-plugin main @ a432692ed7d5dd6437a4755b530ee7aaf2685dad`。

| 遇到什么 | 查看哪里 | 主源码范围 | 主要验证 |
|---|---|---|---|
| 注册、配置、CPU-safe import、worker class 选择 | [plugin-boundary](plugin-boundary/_index.md) | `afd_plugin/{__init__,config,config_utils,envs,validation}.py`、lazy exports、`pyproject.toml` | config、package、env、classpath tests |
| API 请求、Attention worker/runner、KV 与输出路径 | [attention-runtime](attention-runtime/_index.md) | Attention worker/runner 和 GPU ubatch wrapper | Attention unit、serving/accuracy E2E |
| connector 驱动的 FFN daemon 和 runner | [ffn-runtime](ffn-runtime/_index.md) | FFN worker/runner | FFN/engine-core unit、serving E2E |
| 拓扑、payload、通信和连接生命周期 | [connectors](connectors/_index.md) | `afd_plugin/connectors/**`、`distributed/**` | connector/distributed unit、TP/model E2E |
| 模型注册、角色构造/加载、forward metadata | [model-integration](model-integration/_index.md) | `afd_plugin/model_executor/**` | model unit、model/accuracy E2E |
| CUDA/Ascend graph、DBO/ubatching、profiling、native ops/build | [execution-platforms](execution-platforms/_index.md) | 平台 helper、`csrc/**`、`setup.py`、`MANIFEST.in` | graph/DBO/ops/profiler unit 与硬件 E2E |
| vLLM/vLLM-Ascend adapter 和 monkey patch | [compatibility](compatibility/_index.md) | `afd_plugin/compat/**` 中非平台机制文件 | compat/package/classpath/NPU tests |

## 依赖方向

角色和模型 owner 消费 plugin boundary、connector、platform 和 compatibility；低层 owner 不反向依赖具体 Attention/FFN worker。跨 owner 结论只在最近 owner 保留正文，其他页面只链接。系统总览见 [仓库架构](../architecture.md)。
