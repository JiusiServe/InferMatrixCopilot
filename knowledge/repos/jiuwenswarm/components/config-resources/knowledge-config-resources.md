---
title: "内置日报技能：采集、报告接口与模型配置"
created: 2026-10-01
updated: 2026-10-01
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L65-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L45-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L63-L92, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L97-L148, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L28-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py:L104-L139, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L77-L111, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L116-L148]
---

# 内置日报技能：采集、报告接口与模型配置

<!-- kb:knowledge owner=config-resources facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 内置日报技能的采集、分析、渲染链路

此处说明 resources 中随包提供的 advanced-daily-report 技能。DataAggregator 固定创建 memory 与 todo 采集器，Git 根据 git_repo 可选创建，邮件采集器则在 collect() 中按 email_config 延迟创建。ReportGenerator.generate_daily() 依次采集、调用 WorkAnalyzer、按开关执行 AI 分析，最后渲染日报。

来源：[jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L65–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py#L65-L148), [jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L45–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py#L45-L92)

<!-- kb:knowledge owner=config-resources facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 日报入口的参数与返回值

`generate_daily(date=None, config=None) -> str` 的函数文档约定返回 Markdown 日报；未传 config 时创建 ReportConfig。采集入口 `collect(date=None, include_comparison=True) -> CollectedData` 将日期、采集时间以及 memory/todo/Git/email 数据组织成聚合对象。日期未传时由两个入口各自计算当天日期。

来源：[jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L63–L92](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py#L63-L92), [jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L97–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py#L97-L148)

<!-- kb:knowledge owner=config-resources facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 报告开关与技能专用模型配置

ReportConfig 默认 enable_ai_analysis=False、include_trends=True、include_suggestions=True、output_format=markdown。AIAnalyzer 的配置加载优先读 ai_analysis 的 model_name/api_base/api_key；没有这一段时读 react.model_name，并从 react.model_client_config 读 api_base 与 api_key。该技能的回退默认 model_name 为 glm-4.7、api_base 为 `https://open.bigmodel.cn/api/paas/v4`、api_key 为空；它们是这个 helper 的默认值。

来源：[jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L28–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py#L28-L39), [jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py:L104–L139](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/analyzers/ai_analyzer.py#L104-L139)

<!-- kb:knowledge owner=config-resources facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 可选 AI 与本地报告链路

设计推断（非作者历史意图）：

日报入口默认关闭 AI 分析。启用后，AIAnalyzer 延迟创建，并由同步入口通过 asyncio.run 调用其异步分析；初始化或分析异常会在这一层记录日志并返回 None，随后日报入口仍进入渲染。由此推断，本地报告链路减少了对 LLM 可用性的依赖，但启用 AI 后该同步调用仍需等待分析完成。

来源：[jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py:L77–L111](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/generators/report_generator.py#L77-L111)

<!-- kb:knowledge owner=config-resources facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## memory、todo、Git 与邮件的可选集成

聚合器始终采集 workspace 中的 memory 和 todo；只有配置了 Git 采集器才取指定日期的提交。邮件配置包含 address、auth_code 与可选 provider（默认 163），初始化和采集异常在 collect() 内记录日志后继续；include_comparison 控制是否追加历史对比数据。

来源：[jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py:L116–L148](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/resources/agent/workspace/skills/advanced-daily-report/collectors/aggregator.py#L116-L148)

