---
title: "MOSS 注册 reference 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, models]
sources: ["PR #7883"]
---

# MOSS 注册 reference 规则

## MOSS-REF-1d — 注册 voice 必须绑定不可变 generation 并保留 conditioning 身份

- 触发：修改注册 MOSS voice 的 reference binding、cold resolver 或 prefix-cache salt。
- 强制：仅在服务端验证已上传 voice、generation>0 且没有 inline audio override 时，绑定 name/created_at/file_path/ref_text snapshot；blank ref_text 才填默认。cold resolver 在线程中校验路径仍在 uploaded directory、文件 generation 匹配，保留原 WAV PCM16→float32/channel-mixing 处理。缺失/删除 generation 失败，不能换用同名新上传。内部 registered key 不交给普通 URI resolver，解析后移除临时 primary key；salt 以已验证的 name/generation 替代主 ref_audio，继续包含第二 reference 与其余 conditioning。
- 禁止：信任客户端给出的 registered tuple/path；热命中/冷 miss 产生不同 salt；复用旧 generation cache；改变 Nano 的既有 waveform 路径或为省序列化改变音频量化。
- 验收：hot/cold、re-upload、delete、generation/file mismatch、inline override、ref_text 和第二 reference 变化分别覆盖；cold 音频与旧 resolver 一致，上传数据无需驻留 data URI，旧 MOSS 内容/任务 salt 合同仍保持。 ^[PR #7883]
