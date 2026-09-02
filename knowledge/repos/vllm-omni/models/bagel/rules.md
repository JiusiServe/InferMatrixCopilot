---
title: "BAGEL 实现规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5775", vllm_omni/diffusion/models/bagel/bagel_transformer.py, vllm_omni/diffusion/models/lance/lance_transformer.py]
confidence: high
---

# BAGEL 实现规则

## BAGEL-1：CFG position ID 沿序列轴合并

**适用范围**：`Bagel.forward` 将顺序 CFG 的 gen/cfg_text/cfg_img 分支合并为一次
LLM forward；也覆盖继承 `Bagel.generate_image` 和该 forward 的 Lance。

**合同**：每分支的普通 RoPE position ID 形状为 `(S,)`，沿 dim 0 合并为
`(sum S,)`；每分支的 multimodal RoPE position ID 形状为 `(3,S)`，必须沿 dim 1
合并为 `(3,sum S)`。三条 t/h/w 是模态轴，不能沿 dim 0 拼成 `(3N,S)`；CFG 的
batch/branch 关系由重复 query sequence、`packed_seqlens` 和 merged cache 单独表达。

**验收**：

- 构造至少两个 CFG 分支，分别断言 1-D 输入得到 `(sum S,)`、2-D 输入得到
  `(3,sum S)`，且每个分支在序列轴上的值和顺序保持不变。
- 将结果送到对应 rotary/mRoPE 下游，断言 position ID 的序列长度与重复后的 query
  token 总数一致，模态轴仍为 3；不能只检查 `torch.cat` 本身不报错。
- 保留 BAGEL 1-D 路径的回归覆盖，并为 Lance `(3,S)` 路径补 GPU E2E。引入该合同的
  PR #5775（`c9f2e5ad`）只有 shape tracing、ruff 和 reviewer approval，作者因无
  CUDA GPU 未执行 Lance 端到端，因此不能把该提交视为 GPU 精度/功能已验证。
