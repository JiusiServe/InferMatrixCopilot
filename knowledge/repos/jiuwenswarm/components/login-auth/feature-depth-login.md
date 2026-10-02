---
title: "账号登录与凭据续期：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/auth/account_kit.py:L92-L99, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/华为账号登录.md:L15-L27"]
feature: "login"
entry_points: ["jiuwenswarm/common/auth/service.py"]
source_globs: ["jiuwenswarm/common/auth/service.py", "jiuwenswarm/common/auth/*.py"]
---

# 账号登录与凭据续期：实现深读

[功能概览](feature-login.md) · [owner 入口](_index.md)

<!-- kb:depth feature=login facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=baf31ae3ac6ef818dd200592854ad3cb5a8d11bd59242f94a88a777dd700d3a8 -->
**登录开关由远端配置决定**
login_enabled() 的唯一判据是 get_remote_config() 返回非 None 且 is_effective 为真；配置地址有默认值所以默认开启，把 JIUWENSWARM_CONFIG_URL 显式设为 off（或空串等）或拉不到配置即整体关闭（auth 路由 404）。

来源：[jiuwenswarm/common/auth/account_kit.py:L92–L99](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/auth/account_kit.py#L92-L99), [docs/zh/华为账号登录.md:L15–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E5%8D%8E%E4%B8%BA%E8%B4%A6%E5%8F%B7%E7%99%BB%E5%BD%95.md#L15-L27)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/auth/account_kit.py","start":92,"end":99,"sha256":"2edda21cdf757b022d7e96dac26658571143bd52b1089eb052065942f7c3cafb"},{"path":"docs/zh/华为账号登录.md","start":15,"end":27,"sha256":"c181611912d83f895ad333e358f18c935445f8270348d8529c1a9d3c00f5cfe2"}],"trace":[]} -->
<!-- /kb:depth -->
