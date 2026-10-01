---
title: Auto Harness 评测优化 的职责、接口与配置
created: 2026-10-01
updated: 2026-10-01
type: guide
tags:
- jiuwenswarm
sources:
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/auto_harness/service.py
- openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/AutoHarness.md
---

# Auto Harness 评测优化 的职责、接口与配置

本页是该功能的基本知识入口，基线 `f0a69728c96b`。它连接源码契约与上游功能文档；详细字段和行为仍沿固定引用核对。

<!-- kb:knowledge owner=feature-auto-harness facet=architecture pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 职责与边界

Auto Harness 将基座或专家 Harness 的优化组织成评测驱动的 pipeline。任务调度、评测结果、Package 管理和激活共同组成闭环，而不修改模型权重。 本页记录入口职责与边界；逐文件的类型、函数和依赖关系见同 owner 的源码接口记录。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。

<!-- kb:knowledge owner=feature-auto-harness facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 接口与调用入口（API）

可定位的实现声明包括 `reset_harness_packages_state()`；`validate_harness_config_fields(config_path)`；`validate_harness_config_paths(config_path, package_dir)`；`validate_harness_config(config_path, package_dir)`；`ActiveAutoHarnessRun`。这些是源码定位入口，具体公共用户操作沿功能文档查证；本页不把内部符号直接当成稳定 HTTP API。参数、返回类型、错误传播和生命周期应在所列实现与调用方一起核对。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。

<!-- kb:knowledge owner=feature-auto-harness facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 配置入口与生效条件

 实现中直接读取的环境变量名称包括 `API_KEY`、`API_BASE`、`BASE_URL`、`MODEL_NAME`、`MODEL`；名称与实际部署值分开核对。 文档中的调用选项包括 `--pipeline`、`--interval`、`--history`、`--repo`、`--page`、`--labels`，适用命令与前置条件沿文档确认。 修改设置时还要检查配置加载位置与本功能的装配或连接时机，不能只由“保存成功”判断当前运行实例已经采用新值。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。

<!-- kb:knowledge owner=feature-auto-harness facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 设计取舍

**设计推断**：评测驱动优化 Harness 而非训练模型权重，使提示词、工具和 Rail 改动能沉淀为 Package 或 PR；代价是评测质量决定改进是否可信。Meta 与 Expert 两条 pipeline 的目标和产物不同，运行任务成功不能代替基线与候选的效果比较。以上分析从所列接口与功能边界得出，不宣称作者曾评估所有替代方案。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。

<!-- kb:knowledge owner=feature-auto-harness facet=features pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 数据流与关联功能

Auto Harness 将基座或专家 Harness 的优化组织成评测驱动的 pipeline。任务调度、评测结果、Package 管理和激活共同组成闭环，而不修改模型权重。 联调时结合[Harness Package 与热激活](feature-rsi-packages.md)、[Debug Dump 与 OTel](../observability/feature-debug-trace.md)、[Agent Loop 与 Rail 装配](../agent-server-runtime/feature-harness.md)的入口、数据归属和生效条件查证；这些关联页解释不同阶段，不能只凭一项成功判定整个链路完成。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。

<!-- kb:knowledge owner=feature-auto-harness facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b -->

## 怎样验证

使用小评测任务分别检查基座和专家优化 pipeline 的输入、过程记录与评测结果。核对候选 Package 或 PR 的改动和验证证据，再验证失败任务的状态与产物不会被当成已激活优化。这些是建议的验收步骤，本页没有记录上游运行测试已执行或已通过。

源码与文档：[jiuwenswarm/agents/harness/common/auto_harness/service.py:L1–L3349](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/auto_harness/service.py#L1-L3349)；[docs/zh/AutoHarness.md:L1–L311](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/AutoHarness.md#L1-L311)。
