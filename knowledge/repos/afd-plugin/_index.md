---
title: "AFD plugin 仓库知识入口"
created: 2026-08-05
updated: 2026-08-06
type: index
tags: [afd-plugin]
sources:
  - "afd-plugin@a432692:README.md"
  - "afd-plugin@a432692:docs/design/module/index.md"
---

# AFD plugin 仓库知识入口

## 仓库和适用范围

- 上游仓库：`vllm-project/afd-plugin`。
- 默认分支：`main`。
- 知识镜像基线：`a432692ed7d5dd6437a4755b530ee7aaf2685dad`，对应 vLLM `0.26.0`。
- 适用范围：AFD 插件的注册与配置、Attention/FFN 角色运行时、connector/distributed、模型集成、CUDA/Ascend 平台机制和上游兼容 patch。
- 仓库自己的 `AGENTS.md`、`.agents/skills/run-e2e/SKILL.md`、CI 和当前代码保持权威；这里保存可路由的 owner 知识。

## 什么时候查这里

- 修改 `afd_plugin/**`、`csrc/**`、打包文件或 AFD GPU/Ascend 运行路径。
- 调查插件注册、Attention/FFN 角色运行、connector、模型包装、平台机制或兼容补丁。
- 为 AFD changed files 选择最近 owner 和 focused tests。

## 不放什么

- 换到其他仓库仍成立的方法放 [general](../../general/_index.md)。
- vLLM-Omni 的模型、远端、benchmark 或 rebase 经验放 [vllm-omni](../vllm-omni/_index.md)。
- 不复制 AFD 仓库完整 README、AGENTS 或 E2E skill；运行细节以目标仓库当前文件为准。
- 不记录本机 checkout 路径、硬件账号、模型 cache 或凭据。

## 目录内容

| 遇到什么 | 查看哪里 | 说明 |
|---|---|---|
| 开始任何 AFD review 或 issue answer | [仓库规则](rules.md) | 仓库身份、支持边界与验证门禁 |
| 理解系统边界和端到端数据流 | [仓库架构](architecture.md) | Attention/FFN、connector、模型与平台关系 |
| 按源码路径找最近 owner | [组件入口](components/_index.md) | 七个 owner、源码边界与 focused tests |
| 修改注册、配置、CPU-safe import 或 worker 选择 | [plugin-boundary](components/plugin-boundary/_index.md) | normative 插件边界和专项规则 |
| 新增或刷新 monkey patch | [compatibility](components/compatibility/_index.md) | 版本补丁、非 AFD 路径与移除条件 |
| 核对 connector/graph/DBO 当前支持组合 | [execution-platforms](components/execution-platforms/architecture.md) | v0.26 CUDA/Ascend 平台现状 |

默认 briefing 只加载本入口和仓库规则；深层 owner 页面由 changed-file route 或 `doc_search` / `doc_read` 按需读取。
