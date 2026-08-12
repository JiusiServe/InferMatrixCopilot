---
title: "vLLM-Omni CI 规则"
created: 2026-08-04
updated: 2026-08-04
type: rule
tags: [vllm-omni, ci]
sources: ["PR #5436", "PR #5695", "PR #5696", .buildkite/, tests/helpers/mark.py]
confidence: high
---

# vLLM-Omni CI 规则

只有 `VOMNI-CI-数字字母` 是可审计规则 ID。

## Direct 代码快速入口

| PR 描述信号 | 规则 | 第一批 live 源码 |
|---|---|---|
| Buildkite path、label、pytest selector、marker、队列、卡数或目标分支 | `VOMNI-CI-1a` | 命中 `.buildkite/` step → pytest 命令 → changed test 的 `pytestmark` / `hardware_test` |
| 平台专有 golden、阈值、accuracy/performance lane | `VOMNI-CI-1b` | changed test case → golden selector → scorer/threshold → 实际 CI hardware marker |

## VOMNI-CI-1a — 选择器改动必须闭合到实际收集的测试集合

- 触发：新增、拆分、收窄或移动 Buildkite step，或修改 path、label、pytest `-m`、
  hardware marker、队列、卡数及非默认目标分支。
- 强制：冻结 PR 的真实 target base；分别在 base/head 收集测试，并把
  `path/label → pytest selector → test marker → hardware/queue/card count` 逐项对齐；
  每个被移除的平台或测试都必须有明确归类。
- 禁止：从文件名推断收集集合；在 `main` 上验证一个目标为 release/challenge 分支的
  diff；把未解释的掉测、平台移除或 label 变化当作纯 CI 重排。
- 验收：保存 base/head 的 collection diff，head 中每个选中测试都能到达匹配的 runner，
  每个掉测都有 `moved`、`intentionally removed` 或 `still covered elsewhere` 结论，并用
  实际 target branch 跑一次选择器 smoke。 ^[PR #5695] ^[PR #5696]

## VOMNI-CI-1b — 平台专有质量 oracle 必须来自同一硬件 case

- 触发：按 CUDA/ROCm/NPU 或具体硬件选择 golden、评分器、阈值或质量 job。
- 强制：golden provenance、测试输入、模型 revision、执行参数、marker、队列和实际硬件
  属于同一个 case；平台分支必须显式选择 oracle，未命中的平台保持原合同。
- 禁止：用另一硬件的本地输出生成 golden；用无法解释的阈值放宽吸收平台漂移；修改
  一个平台时顺带改变其他平台的 baseline。
- 验收：目标 CI runner 产出的 artifact 可复现提交 golden 的 digest 和评分，目标平台
  命中专属 oracle，至少一个未改平台 control 仍选择原 oracle；阈值证据同时满足
  [DIFF-3a](../components/diffusion/rules.md#diff-3a--质量阈值必须由完全相同的测试-case-产生)。
  ^[PR #5436]
