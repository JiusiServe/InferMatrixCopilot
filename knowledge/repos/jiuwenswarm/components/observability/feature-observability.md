---
title: 执行轨迹与保留 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/observability/sink.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/日志.md
---

# 执行轨迹与保留 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-observability facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

轨迹系统把执行事件投影为可保存和可展示的记录。实时队列、最终结果和保留清理的职责不同，查看器中的缺口不自动证明任务未执行。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。

<!-- kb:knowledge owner=feature-observability facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `TrajectoryRecordSink [start, consume, consume_snapshot, consume_stream_frame, request_stop]`；`TrajectorySessionSinkRouter [start, consume, consume_snapshot, consume_stream_frame, close]`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。

<!-- kb:knowledge owner=feature-observability facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `logging.level`、`logging.console_level`、`logging.gateway`、`logging.channel`、`logging.agent_server`、`logging.full`。这些是示例字段，不单独证明源码默认值或全部优先级。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。

<!-- kb:knowledge owner=feature-observability facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：实时队列与持久轨迹让执行可观察，保留清理限制长期存储；代价是展示、最终结果和落盘不处在完全相同的时序。应用日志与框架日志独立，某个查看器缺记录不能单独证明 Agent 没有执行。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。

<!-- kb:knowledge owner=feature-observability facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

轨迹系统把执行事件投影为可保存和可展示的记录。实时队列、最终结果和保留清理的职责不同，查看器中的缺口不自动证明任务未执行。 联调时结合[Debug Dump 与 OTel](feature-debug-trace.md)、[FACT/TIP 双轨经验](../agent-server-runtime/feature-ttse.md)、[Agent Loop 与 Rail 装配](../agent-server-runtime/feature-harness.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。

<!-- kb:knowledge owner=feature-observability facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

完成一次含工具与子任务的运行，核对事件身份、最终结果和持久记录。检查日志轮转、保留清理、消费者中断与重复事件，再分别定位应用层日志和框架层日志的输出路径。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/observability/sink.py:L1–L1016](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/observability/sink.py#L1-L1016)；[docs/zh/日志.md:L1–L245](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E6%97%A5%E5%BF%97.md#L1-L245)。
