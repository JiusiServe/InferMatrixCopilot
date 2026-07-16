---
title: "vLLM-Omni 代码模块"
created: 2026-07-10
updated: 2026-07-10
type: index
tags: [vllm-omni, components]
sources: []
---

# vLLM-Omni 代码模块

本目录是知识树对 `vllm_omni/` 源码空间的镜像（code-owner 轴）。每个模块页的
"源码入口"列出它拥有的真实源码路径；所有模块页的路径均已验证存在——建目录时
已有的 diffusion/model-executor/serving 在 `main @ 238fc0a6`（此前亦在
`dev/vllm-align @ 4f2b32c` 验证，结果一致），2026-07-16 新增的
scheduler/distributed/config 在当日 `main @ 5c390096`。只有确有知识沉淀的模块才
建目录，不预建空目录（此前预告的 scheduler、config 已在第一条稳定结论落盘时建立；
attention、lora、quantization 等同理，等第一条稳定结论落盘时再建）。

注意：这里的模块划分服务于**知识归属**（一个 owner 覆盖一条职责链），与
copilot `adapters/vllm_omni/manifest.yaml` 的 `modules:`（服务于运行时
`module_for_path()` 路由与 PR 验证分片）粒度不同，属有意为之——例如
Model Executor 在这里同时拥有 `worker/`，而 manifest 将其拆为
`model_executor` 与 `worker_runner` 两个运行时模块。

| 代码模块 | 查看哪里 | 负责什么 |
|---|---|---|
| Config | [config](config/_index.md) | PipelineConfig/deploy YAML 双层 schema、解析合并链、pipeline registry、endpoint 策略 |
| Diffusion | [diffusion](diffusion/_index.md) | 多模型共享的 diffusion pipeline、denoise 和执行机制 |
| Distributed | [distributed](distributed/_index.md) | 跨 stage 通信：connector 后端、KV 迁移管理、协调与负载均衡、ZMQ 路由 |
| Model Executor | [model-executor](model-executor/_index.md) | AR/LLM stage、stage config、并行与设备启动、输入处理和跨 stage 数据桥接 |
| Scheduler | [scheduler](scheduler/_index.md) | AR/生成请求调度、KV transfer 调度面、chunk/full-payload 等待、tensor prefix cache |
| Serving | [serving](serving/_index.md) | 用户入口、请求解析、在线服务和 engine 边界 |
