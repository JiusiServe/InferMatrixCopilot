---
title: "gateway-channel-manager 审查规则"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [jiuwenswarm, components]
sources: ["PR #7625"]
confidence: high
---

# gateway-channel-manager 审查规则

## JW-XIAOYI-AUDIT-1a — 小艺流式审计有界且异常不影响投递

- 触发：修改 xiaoyi_0.2.4.beta3 XiaoyiChannel.send 的 stream audit。
- 强制：统计放在异常隔离块，仅读取消息；按 session/task 累计正文/思考与切换次数，字典最多 64 条，样本最多三条且截断；终态移除状态，有计数帧才向既有 logger 输出一行汇总。
- 禁止：诊断异常向 send 传播；修改或丢弃帧；无界保存状态；新增逐帧日志或独立日志文件；把网关观测直接等同于模型内在行为证明。
- 验收：构造统计异常仍投递原消息；超过容量时淘汰最旧记录；终态后无残留，空轮不输出汇总。^[PR #7625]
