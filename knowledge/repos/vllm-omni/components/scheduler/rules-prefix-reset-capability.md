---
title: "Running prefix-cache reset 能力规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components, scheduler]
sources: ["PR #8259"]
confidence: high
---

# Running prefix-cache reset 能力规则

## SCHED-RESET-1a — active reset 在 preemption 前检查拓扑 capability

- 触发：修改共享 scheduler 的 running prefix-cache reset，或接入持有已消费帧/排队 PCM 的 stateful decoder。
- 强制：由最终 model config 的 `supports_running_prefix_cache_reset` 声明能力，scheduler 不按模型 architecture 特判。当请求要求 reset running requests、当前有 running request 且 capability 为 false 时，必须在调用父级 reset/preemption 前返回 `False`；完成或 abort 后才可重试。fused Qwen3-TTS 的 false pin 不能被 legacy runtime override 或未归属的 structured field 翻转。
- 禁止：先丢弃 in-flight tokens 再检查不可回滚 codec 状态；仅改共享 scheduler 就宣称所有拓扑支持 active reset；把 idle reset 或既有两阶段默认能力一并禁用。
- 验收：覆盖 active unsupported 的无 mutation 拒绝、idle reset、支持拓扑、legacy override 和 structured owner 拒绝；connector prompt replacement 的 stale fence 同时执行 [SCHED-6d](rules.md#sched-6d--显式-prompt-replacement-必须一次性释放旧状态并回到-admission)。^[PR #8259]
