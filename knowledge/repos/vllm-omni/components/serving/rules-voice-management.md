---
title: "Speech voice management 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, components]
sources: ["PR #7795"]
---

# Speech voice management 规则

## SERV-VOICE-1a — Voice deletion 必须按异常类型区分 builtin 与不存在

- 触发：修改 /v1/audio/voices delete、uploaded speaker storage 或错误映射。
- 强制：在 upload lock 内以规范化name判断，builtin集合排除uploaded项；builtin/default删除抛InvalidPresetVoiceReferenceError，未知name抛InvalidVoiceReferenceError，API先捕preset子类映射403/ForbiddenError，再捕父类映射404/NotFoundError，成功返回明确成功响应。uploaded删除继续清metadata/data-URI/speakerartifactcache，unlink失败保持带voice name的warning。
- 禁止：以message substring决定403/404；将builtin当不存在返回404；把async delete恢复为无法表达原因的bool；只在testclient中模拟抛异常而不检查实际HTTPstatus/body。
- 验收：builtin、default、unknown（含带not found文字的合法name）、uploaded成功与unlink失败分别覆盖route和handler；错误类继承/捕获顺序和case-normalizedname仍正确。 ^[PR #7795]
