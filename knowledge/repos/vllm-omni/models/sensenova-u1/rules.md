---
title: "SenseNova-U1 规则"
created: 2026-09-05
updated: 2026-09-05
type: rule
tags: [vllm-omni, models, diffusion]
sources: ["PR #6516", "Issue #6471", recipes/SenseNova/SenseNova-U1.5.md, vllm_omni/diffusion/models/sensenova_u1/pipeline_sensenova_u1.py, vllm_omni/diffusion/models/sensenova_u1/paged_decode.py, vllm_omni/diffusion/models/sensenova_u1/sensenova_u1_transformer.py, tests/diffusion/models/sensenova_u1/]
confidence: high
---

# SenseNova-U1 规则

## Direct 代码快速入口

| 信号 | 规则 | 第一批源码 |
|---|---|---|
| U1.5 distilled 8-step LoRA、kohya keys、one-way fusion | SENSENOVA-1a | `pipeline_sensenova_u1.py::load_lora_weights` → loader → parameter `weight_loader` |
| `VLLM_OMNI_SENSENOVA_PAGED_DECODE`、think/text decode、capture/reuse/sleep | SENSENOVA-1b | `pipeline_sensenova_u1.py::_decode_context` → `paged_decode.py` |
| GQA K/V、three-axis RoPE、single-token mask | SENSENOVA-1c | `sensenova_u1_transformer.py` → pipeline forward |

## SENSENOVA-1a — U1.5 distilled LoRA 是启动期单文件、单向融合

- 触发：`sensenova/SenseNova-U1.5-8B-MoT` 的 distilled 8-step adapter、kohya A/B key mapping、TP load 或融合失败处理变更。
- 强制：U1.5 共享 U1 pipeline；startup 只接受 exactly one file。以 suffix/exact first-match mapping 解析 kohya A/B，fp32 计算 delta 后一次 round；fused/packed target 依声明顺序拼接，parameter `weight_loader` 负责 TP shard。zero match fail。成功后只留 adapter-name sentinel，不留 tensors；重复 load no-op。逐 parameter progressive fuse 失败必须 abort startup、reload 才可恢复，不承诺 rollback 或 adapter switching。
- 禁止：substring multi-match、silent no-op、保留 adapter state、将一向 fused distill 当 dynamic PEFT/unload，或外推 checkpoint/quality/perf 支持。
- 验收：CPU 覆盖 A/B、suffix overlap、fused mapping、fp32 delta、TP loader、zero-match、retained sentinel/second load 与 partial-failure abort；真实 adapter/TP/E2E 另行证据。^[PR #6516] ^[Issue #6471]

## SENSENOVA-1b — paged AR decode 是单序列模型本地 CUDA opt-in

- 触发：`VLLM_OMNI_SENSENOVA_PAGED_DECODE`、AR decode cache/capture、dynamic PEFT 或 level-2 sleep。
- 强制：literal env default `"1"` 才启用；仅 CUDA、eligible head dimension 与完整 varlen signature，其他情况 eager fallback。cache 是 one-sequence internal K/V、identity block table、device write position/static capture；fit bucket 才 reuse，growth 必须 allocate/copy/block-table 后 atomic publish bucket+generation，并 recapture；graphs 进 global pool，sleep2 clear。dynamic PEFT wrappers 禁 cross-request capture/reuse；one-way fused distill 仍 eligible。
- 禁止：把它称为 scheduler/KV manager/prefix reuse/continuous batching；跨 request 复用 dynamic adapter graph；failed grow 后保留部分 buffers；宣称通用 paged-KV、hardware parity 或性能。
- 验收：覆盖 env/eligibility fallback、single sequence identity table、reuse/grow generation/recapture/failed grow、sleep clear、base→LoRA→base veto；scheduler-visible runner 或 multi-sequence forward 时删除本实现并改用 manager。^[PR #6516]

## SENSENOVA-1c — native GQA 与三轴 RoPE 必须在模型 forward 保持

- 触发：SenseNova attention head layout、RoPE construction 或 single-token decode mask 变更。
- 强制：native GQA 不预 expand K/V；每 forward 一次构建/共享 three-axis RoPE embeddings；single-token decode 不注入 all-zero mask。
- 禁止：把此模型 exception 推广给 shared attention，或用单测外推 quality/performance。
- 验收：GQA/reference、RoPE sharing 和 maskless decode 各有 model test；真实 output parity/accelerator coverage 独立取得。^[PR #6516]
