---
title: "BAGEL 实现规则"
created: 2026-09-02
updated: 2026-09-02
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #5775", "PR #5884", vllm_omni/diffusion/cache/cachedit/backend.py, vllm_omni/diffusion/models/bagel/bagel_transformer.py, vllm_omni/diffusion/models/bagel/pipeline_bagel.py, vllm_omni/diffusion/models/lance/lance_transformer.py, tests/diffusion/cache/test_cache_backends.py]
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

## BAGEL-2：DiT owner 是 nested `language_model.model`

**适用范围**：任何消费 `BagelPipeline._dit_modules` 的 Cache-DiT、compile、SP、LoRA、loader 或
offloader 路径；Lance 继承此 pipeline 时也需复核其实际组件树。

**合同**：Bagel 声明 `_dit_modules = ["language_model.model"]`；consumer 必须把它当多段 attribute
path 解析到真实 DiT，不能把含点字符串传给单层 `getattr`。缺失中间节点应按该 consumer 的既有
策略 skip/warn/fail，不能因解析器差异静默漏掉模型。目标 pin 的 Cache-DiT 已支持 dotted
enable/refresh/summary；generic compile、registry SP 和 LoRA 仍未共享 dotted resolver，不能声称
Bagel 的全部 lifecycle 已支持。
Bagel init 也令 `transformer` 指向同一 object，但 `_dit_modules` 非空时 Cache-DiT 不走 conventional
fallback；consumer 必须以 canonical declaration 为准，不能依赖当前 direct alias。Cache-DiT 会在
refresh/summary 时重新解析该 path，故 enable 后不得替换 `language_model.model` identity；若 future
declaration 同时列出两个 alias，也会重复 enable，因为当前 discovery 不按 identity 去重。

**验收**：真实 Bagel component tree 覆盖 Cache-DiT enable→repeated request refresh→summary，断言
hook/context 始终绑定同一 nested model；目标 cache backend 没有 disable API，future 若增加 worker
shutdown/teardown 必须验证清理同一 target。对 compile、SP、LoRA 与 offload 分别验证同一 object
identity 和 missing-middle 行为。当前 mock 测试只覆盖 Cache-DiT dotted enable/refresh/summary，
不构成真实 cross-consumer 或 teardown 证据。^[PR #5884]
