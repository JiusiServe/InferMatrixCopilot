---
title: "Graph 测试 buffer 规则"
created: 2026-10-06
updated: 2026-10-06
type: rule
tags: [vllm-omni, ci]
sources: ["PR #8330"]
confidence: high
---

# Graph 测试 buffer 规则

## OMNI-CI-GRAPH-1a — fake estimator 未写的输出区域必须初始化

- 触发：修改 CFM graph eager/replay oracle、fake estimator 或 cache-tail fixture。
- 强制：synthetic estimator 只写 chunk 前缀时，其他会参与 parity 比较的 cnn/attention
  output 区域用确定值初始化；eager 与 graph 比较相同有效区域及定义好的 tail。
- 禁止：用 torch.empty 的未写尾部作为 oracle，让偶发 NaN/垃圾值形成 graph 数值回归；
  把 fixture 初始化等同于真实 model cache-tail 已验证。
- 验收：未写 tail 不含非有限值，模拟 estimator 遗漏写入时 oracle 稳定；独立真实
  estimator 测试仍要检查历史 cache 的读写 ownership。^[PR #8330]

更一般的 fixture 生命周期查 [CI fixture 规则](rules-test-fixtures.md)。
