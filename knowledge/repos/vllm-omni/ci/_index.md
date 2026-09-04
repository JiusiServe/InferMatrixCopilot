---
title: "vLLM-Omni CI"
created: 2026-07-10
updated: 2026-09-04
type: index
tags: [vllm-omni, ci]
sources: [.buildkite/cuda/pipeline.yml, docs/contributing/ci/test_system_overview.md]
---

# vLLM-Omni CI

## 什么时候查这里

- 处理 vLLM-Omni 的 L2/L4、模型测试配置或 CI 特有问题。

## 不放什么

- 跨仓库通用的测试方法。

## Invalid-request error expectation

- 对 Qwen3-Omni 的 incomplete `response_format={"type": "json_schema"}`，DFX
  invalid-request test 应断言 400 公共 API error envelope 中的
  `BadRequestError`、`param="response_format"` 和 `json_schema` 缺失提示；不要把
  vLLM 内部 validator 的 Pydantic `value_error` token 当成该接口合同。该断言曾因
  上游错误映射改为 `BadRequestError` 而导致 weekly CI 失败。^[PR #6290 / issue #6248]

## 目录内容

| 遇到什么 | 查看哪里 |
|---|---|
| 审查硬件 lane、回归 fence、CI 工具供应链或 xdist/shared fixture | [CI rules](rules.md) |
| 查看仓库特有 CI 陷阱 | [CI guides](guides/_index.md) |
| 调查历史 CI 失败 | [CI incidents](incidents/_index.md) |
