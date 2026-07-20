---
title: "Krea 2 规则"
created: 2026-07-20
updated: 2026-07-20
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #4730"]
confidence: high
---

# Krea 2 规则

只有 `KREA-数字字母` 是可审计规则 ID。

## KREA-1a — text encoder 与 VAE 显式继承目标 dtype

- 触发：构造或替换 Krea 2 text encoder/VAE loader。
- 强制：两者都显式传递 `od_config.dtype`（或当前 canonical dtype owner）。
- 禁止：依赖 `from_pretrained` 默认 fp32，再在 pipeline 中事后 cast；会增加峰值显存并
  产生 dtype mismatch 窗口。
- 验收：loader 单测分别断言两个组件的 `torch_dtype`；真实加载记录组件 dtype 与峰值
  显存。 ^[PR #4730]

## KREA-1b — config-only 读取不能触发全权重下载

- 触发：计算 VAE scale 或读取 `vae/config.json`、`model_index.json`。
- 强制：使用精确文件获取 helper，只请求所需 config；离线 cache 缺文件时给出具体路径。
- 禁止：调用 snapshot/full-weight 下载模式只为读取一个 JSON，阻塞启动并污染 cache。
- 验收：mock Hub/cache 层断言请求文件集合；config 已缓存时无网络，缺失时错误指向具体
  config 而非笼统权重失败。 ^[PR #4730]

## KREA-2a — offline、online 与并行能力逐项验收

- 触发：supported-model 表、recipe 或 PR 声明 online、HSDP、layerwise offload、VAE
  patch parallel。
- 强制：offline 与 online 使用各自真实入口；每个并行/offload 勾选项有独立路径证据。
- 禁止：只有 offline 能跑却宣称 `vllm serve`/images endpoint；用一个分布式 smoke
  同时支撑所有能力。
- 验收：online e2e 从公开 endpoint 返回图像；capability matrix 每格绑定当前 head 的
  命令、环境和结果。 ^[PR #4730]

共享 loader 合同见 [Model Executor EXEC-2a](../../components/model-executor/rules.md)；
证据分层见 [model validation](../../review/guides/model-validation.md)。
