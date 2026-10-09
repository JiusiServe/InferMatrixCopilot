---
title: "部署 platform overlay 的最终配置合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, components]
sources: ["PR #8409"]
confidence: high
---

# 部署 platform overlay 的最终配置合同

## PLAT-1a — 平台能力由合并后的全部 stage 配置与验证共同决定

- 触发：修改 deploy YAML 的 platforms overlay 或 supported-model 平台标记。
- 强制：按 platform 合并最终 stage 后核对 devices 数量与 TP、parallel_config、backend、各 stage 显存、eager/capture 与模型输入限制。XPU profile 的多卡切分、FlashInfer 替换及 Fish top-p eager 等约束随所属 stage 生效；支持声明需对应可运行入口的证据。
- 禁止：从 stock YAML 或单字段推出平台可用；把该 PR 未改动模型说成已验证无需 overlay，或把 YAML 存在当作硬件运行通过。
- 验收：验证 overlay 选择和最终 stage args，覆盖设备/TP 与 backend 不匹配；实际运行证据绑定具体硬件、checkpoint、head 和入口。 ^[PR #8409]
