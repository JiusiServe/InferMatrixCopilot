---
title: "Realtime model-context 自动截断合同"
created: 2026-10-09
updated: 2026-10-09
type: rule
tags: [vllm-omni, components]
sources: ["PR #8566"]
confidence: high
---

# Realtime model-context 自动截断合同

## RT-TRUNC-1 — 截断只移动 model cursor，保留可操作的 conversation history

- 触发：修改 Realtime prompt budget、conversation item 插入/删除或自动截断。
- 强制：完整 items 仍可 retrieve/delete；模型上下文从独立 first-item cursor 取后缀，cursor item 删除时前移，cursor 已在末尾时新 append 可进入模型上下文。预算探测用无 cache 的 speculative render，预留输出预算，按后缀探测可容纳输入；只把 input_text/input_tokens 超限识别为可截断错误。
- 禁止：为缩短 prompt 删除用户历史；吞掉无关 render/model 错误；把 preflight 探测说成对最终再次 render 的无条件长度保证。
- 验收：覆盖 retrieve/delete、cursor 删除/末尾追加、超长历史、输出预算和无关错误传播；检查实际送入模型的 prompt，若最终 render 变化需另验证预算。 ^[PR #8566]
