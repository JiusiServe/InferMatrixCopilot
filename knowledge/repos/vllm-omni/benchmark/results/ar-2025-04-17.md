# AR Benchmark 结论（2025-04-17）

## 对齐配置
- temperature=0.6, top_k=1024, top_p=0.95, max_tokens=128, stop=[127957]
- 随机 512×512 噪声图片，4×H800

## 结果

| 指标 | HF baseline (PP4) | vLLM-Omni (TP4) |
|------|-------------------|-----------------|
| avg total | 27.81s | 5.35s |
| avg output tokens | 128.0 | 87.1 |
| decode tps | 4.67 t/s | ~16.0 t/s |

- decode throughput 3.4x（TP4 并行带宽翻 4 倍）
- vLLM 62% runs 提前 stop：flash vs eager attention bf16 精度差异导致 MoE routing 分歧，非配置问题

## 算存比（Arithmetic Intensity）

HunyuanImage-3.0-Instruct AR stage（38B MoE, 7B active, 0.4B ViT）

| 阶段 | FLOPs | Memory Load | AI (FLOPs/Byte) | Ridge (4×H800) | 瓶颈 |
|------|-------|-------------|-----------------|-----------------|------|
| Prefill+ViT (seq=1237) | 18.4 TFLOPs | 76 GB | 242 | 295 | memory-bound（接近 ridge） |
| Decode (per token) | 14 GFLOPs | 14.26 GB | 1.0 | 295 | memory-bound（严重） |

H800 x4: 3956 TFLOPs bf16 peak, 13400 GB/s HBM bandwidth, ridge point = 295 FLOPs/Byte.

Decode 严重 memory-bound，TP4 通过分摊 weight load 提升带宽是主要加速手段。Prefill 接近 ridge，batch size 增大会变 compute-bound。

## 已知坑
- I2T YAML 原始 `stop_token_ids: [127957, 128026]` 多了 128026，导致 vLLM 只生成 47 tokens 就停。已修正为 `[127957]`
- 对比性能用 per-token throughput（tps），不要用 total time（受 output length 影响）

## 数据文件
- `bench_results/comparison_100runs.md` — 对比报告
- `bench_results/hf_baseline_128tok_100runs.json` — HF 100 runs
- `bench_results/vllm_omni_aligned_128tok_100runs.json` — vLLM 100 runs（对齐配置）
- `scripts/bench/` — bench 脚本
