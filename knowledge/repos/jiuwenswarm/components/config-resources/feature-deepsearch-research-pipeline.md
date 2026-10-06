---
title: "openJiuwen-DeepSearch 深度研究执行管线"
created: 2026-10-06
updated: 2026-10-06
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L200-L230, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L293-L339, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L233-L258]
feature: "deepsearch-research-pipeline"
entry_points: ["jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py"]
source_globs: ["jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/validate_environment.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/convert_docx.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/convert_html.py", "jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/verify_skill_structure.py"]
---

# openJiuwen-DeepSearch 深度研究执行管线

<!-- kb:knowledge owner=feature-deepsearch-research-pipeline facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b verdict=pass -->

**入口与调用契约**

命令行入口 `main.py --mode query --query "题目" [--background|--foreground]`，`--mode` 仅支持 `query`，`--query` 默认为 "AI手机研究报告"。`execute_deep_search(query)` 供 Agent 调用，成功返回报告字符串，配置缺失（ValueError）或执行异常时记日志并返回 None；main 据此以退出码 0/1 结束。未指定 `--foreground` 时默认走后台模式：父进程以 `JIUWEN_BACKGROUND_MODE=1` 重新拉起分离的子进程并写 PID.info 后退出；若环境已是 `JIUWEN_BACKGROUND_MODE=1`，run_background 直接返回，由 main 继续前台执行研究。

Sources / 来源：[jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L200–L230](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L200-L230), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L293–L339](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L293-L339), [jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py:L233–L258](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/openJiuwen-DeepSearch/scripts/main.py#L233-L258)

