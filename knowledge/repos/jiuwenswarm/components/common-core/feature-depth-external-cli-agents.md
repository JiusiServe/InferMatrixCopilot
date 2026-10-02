---
title: "外部 Claude 与 Codex CLI 智能体：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_runtime.py:L215-L239, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/external_cli_catalog.py:L24-L27]
---

# 外部 Claude 与 Codex CLI 智能体：实现深读

[功能概览](feature-external-cli-agents.md) · [owner 入口](_index.md)

<!-- kb:depth feature=external-cli-agents facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=8a2d1b35ba8281b375531ef33c12b5f6187928234ca0e8faa329f795ee4a82fd -->
**运行时目录与探测超时的取值**
external_cli_site_packages 在冻结 Windows 下解析为 sys.executable 同级的 runtime/external-cli/<cli_agent>/site-packages，在冻结 macOS 下为 ~/Library/Application Support/<DISPLAY_NAME>/runtime/external-cli/<cli_agent>/site-packages（用户目录以占位符表示）；非冻结环境抛 RuntimeError。模型目录刷新的探测超时默认 DEFAULT_PROBE_TIMEOUT_S = 15.0 秒。

来源：[jiuwenswarm/common/external_cli_runtime.py:L215–L239](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_runtime.py#L215-L239), [jiuwenswarm/common/external_cli_catalog.py:L24–L27](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/external_cli_catalog.py#L24-L27)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/common/external_cli_runtime.py","start":215,"end":239,"sha256":"0d43a5b773460a56c4eb85a162cbe1cdd9dab6e5b6e7002353da61ab46b5bbbc"},{"path":"jiuwenswarm/common/external_cli_catalog.py","start":24,"end":27,"sha256":"276e99eb8c6dd94f84fe7406fea2f43bedb725979bdcc023ee297000e8238914"}],"trace":[]} -->
<!-- /kb:depth -->
