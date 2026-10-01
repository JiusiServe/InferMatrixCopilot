---
title: Symphony 检索与图谱编排 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/symphony/service.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/Symphony-技能编排与分发.md
---

# Symphony 检索与图谱编排 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-symphony facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

技能索引与图谱服务支持检索、规划和候选能力处理。图谱构建、生成执行计划和安装技能的边界各自独立，能力可用性取决于启用配置和既有技能。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。

<!-- kb:knowledge owner=feature-symphony facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `experience_request_id(recipe_id, version)`；`SwarmSymphonyService [graph_status, refresh_graph, start_refresh_graph, cancel_build, graph]`；`get_swarm_symphony_service()`；`set_swarm_symphony_service(service)`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。

<!-- kb:knowledge owner=feature-symphony facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

上游 YAML 示例的配置键包括 `symphony.skill_retrieval.build.root_categories`、`symphony.enabled`、`symphony.paths.skills_root`、`symphony.paths.graph_dir`、`symphony.build.max_candidates_per_skill_relation`、`symphony.build.min_edge_confidence`、`symphony.evolution.enabled`、`symphony.orchestration.mode`。这些是示例字段，不单独证明源码默认值或全部优先级。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。

<!-- kb:knowledge owner=feature-symphony facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：检索用树按需披露已安装技能，编排用图验证输入输出衔接，减轻一次注入全部技能的上下文成本；代价是索引和图谱构建需要额外时间并随技能变化维护。候选检索、生成执行路线与具体安装和执行分别完成，不能互相当成成功证据。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。

<!-- kb:knowledge owner=feature-symphony facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

技能索引与图谱服务支持检索、规划和候选能力处理。图谱构建、生成执行计划和安装技能的边界各自独立，能力可用性取决于启用配置和既有技能。 联调时结合[技能安装、挂载与发现](../agents-team/feature-skills.md)、[团队技能与能力复用](../agents-team/feature-swarm-skills.md)、[Skill 自演进](../agent-server-runtime/feature-skill-evolution.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。

<!-- kb:knowledge owner=feature-symphony facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

准备几个可衔接技能，分别构建索引和图谱，验证目录探索、候选选择与执行路线。覆盖缺少索引、缺少上游输入和技能变更；核对路线确认后实际技能输出能交给下一步，而非只在图中相邻。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/symphony/service.py:L1–L1920](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/symphony/service.py#L1-L1920)；[docs/zh/Symphony-技能编排与分发.md:L1–L544](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/Symphony-%E6%8A%80%E8%83%BD%E7%BC%96%E6%8E%92%E4%B8%8E%E5%88%86%E5%8F%91.md#L1-L544)。
