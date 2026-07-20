---
title: "vLLM-Omni CI 指南"
created: 2026-07-10
updated: 2026-07-20
type: index
tags: [vllm-omni, ci]
sources: []
---

# vLLM-Omni CI 指南

| 遇到什么 | 查看哪里 |
|---|---|
| JSON 配置、pipeline 和 perf CI 特有问题（仓库配置坑） | [CI gotchas](ci-gotchas.md) |
| 测试分级 L1–L5 与 pytest markers | [test tiers](test-tiers.md) |
| Buildkite 管线布局与队列→硬件映射 | [buildkite structure](buildkite-structure.md) |
| 镜像/依赖/管线/超时等环境坑 runbook | [CI environment gotchas](ci-environment-gotchas.md) |
| 可选依赖未安装、硬件不满足与真实 kernel 的分层测试 | [optional dependencies](optional-dependencies.md) |
| 精度失败先归因（golden/评分器/上游 bug/回归） | [accuracy attribution](accuracy-attribution.md) |
