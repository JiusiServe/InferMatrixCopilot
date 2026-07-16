---
title: "测试分级（L1–L5）与 pytest markers"
created: 2026-07-16
updated: 2026-07-16
type: guide
tags: [vllm-omni, ci]
sources: [docs/contributing/ci/CI_5levels.md, docs/contributing/ci/tests_markers.md]
---

# 测试分级（L1–L5）与 pytest markers

官方 spec：`docs/contributing/ci/CI_5levels.md` + `tests_markers.md`
（`main @ 5c390096` 复核）。测试金字塔五级 + Common 规范
（PR 模板/checklist 与 CI 失败说明）。

## 五级定义

| 级别 | 范围 | marker | 触发 | 目录 |
|---|---|---|---|---|
| L1 | 单元/逻辑（CPU，<15min） | `core_model and cpu` | 每个带 `ready` label 的 PR | `tests/<component>/test_*` |
| L2 | 高优模型 E2E + 需 GPU 的单测（请求成功/输出非空/格式对——**不含精度**） | `core_model` | `ready` PR / main+nightly | `tests/e2e/...` |
| L3 | 进阶模型 E2E | `advanced_model` | 每次 merge 到 main | `tests/e2e/...` |
| L4 | 全量模型：功能 + 性能 + 精度 + 文档示例 | `full_model` | nightly（或 PR label + rebuild） | `tests/e2e/`、`tests/dfx/perf/`、doc example 测试 |
| L5 | 长期稳定性 | — | weekly | `tests/dfx/stability/` |

与仓库硬门禁的对应（[rules.md](../../rules.md)）：**L2 只许 CPU/mock 功能、不得触发
真实 stage/device/GPU 初始化；真实权重、精度、性能与 profiling 属 L4**。

## markers（pyproject.toml 定义）

- 分级：`core_model`（L1&L2）、`advanced_model`（L3）、`full_model`（L4）。
- 领域：`diffusion`、`omni`、`tts`、`cache`、`parallel`。
- 平台：`cpu`、`gpu`、`cuda`、`rocm`、`xpu`、`npu`。
- 硬件：`H100`、`L4`、`MI325`、`A2`、`A3`；多卡：`distributed_{cuda,rocm,npu}`；
  条件跳过：`skipif_{cuda,rocm,npu}`（卡数不足时跳过）。
- 其他：`slow`（快速 CI 可跳）、`benchmark`。
- 带 `*` 的平台/硬件/分布式/skipif markers 由 `@hardware_test` 参数化装饰器（或
  `hardware_marks`）**自动添加**，用法：
  `@hardware_test(res={"cuda": "L4", "rocm": "MI325", "npu": "A2"}, num_cards=2)`。

## 相关

- 各级怎样映射到 Buildkite 管线见 [buildkite-structure](buildkite-structure.md)；
  仓库配置坑见 [ci-gotchas](ci-gotchas.md)。
