# vLLM-Omni 性能与 Profiling 错题

| 错题 | 查看哪里 |
|---|---|
| 2026-04-23 — 没做侦察 + judge 模型未预下载 | [2026-04-23-profiling-and-model-loading-01](2026-04-23-profiling-and-model-loading-01.md) |
| 2026-04-23 — 连续跑多配置时 GPU 显存残留 OOM | [2026-04-23-profiling-and-model-loading-02](2026-04-23-profiling-and-model-loading-02.md) |
| 2026-04-27 — HF_HUB_CACHE 覆盖 HF_HOME 导致 server 600s 超时 | [2026-04-27-profiling-and-model-loading-03](2026-04-27-profiling-and-model-loading-03.md) |
| 2026-04-27 — async_chunk=True 默认值导致 HunyuanImage3 启动 ValueError | [2026-04-27-profiling-and-model-loading-04](2026-04-27-profiling-and-model-loading-04.md) |
| 2026-04-27 — Siglip2VisionModel 版本不兼容 (transformers 5.6.2) | [2026-04-27-profiling-and-model-loading-05](2026-04-27-profiling-and-model-loading-05.md) |
| 2026-04-27 — HF 官方 pipeline 无法在 L20X 云实例上跑通 | [2026-04-27-profiling-and-model-loading-06](2026-04-27-profiling-and-model-loading-06.md) |
| 2026-04-28 — trust_remote_code 模型的 patch 被反复覆盖 | [2026-04-28-profiling-and-model-loading-07](2026-04-28-profiling-and-model-loading-07.md) |
| 2026-04-28 — attn_implementation="eager" 对自定义 attention dispatch 无效 | [2026-04-28-profiling-and-model-loading-08](2026-04-28-profiling-and-model-loading-08.md) |
| 2026-04-28 — pip install torchvision 把 torch 升级到不兼容版本 | [2026-04-28-profiling-and-model-loading-09](2026-04-28-profiling-and-model-loading-09.md) |
| 2026-04-28 — 用户要 torch profiler trace，给了 benchmark stats JSON | [2026-04-28-profiling-and-model-loading-10](2026-04-28-profiling-and-model-loading-10.md) |
| 2026-04-28 — HF 模型 RoPE 广播导致 SDPA key/value size 不匹配 | [2026-04-28-profiling-and-model-loading-11](2026-04-28-profiling-and-model-loading-11.md) |
| 2026-04-28 — HF 模型 CFG 2D attention_mask 传给 SDPA 报错 | [2026-04-28-profiling-and-model-loading-12](2026-04-28-profiling-and-model-loading-12.md) |
| 2026-04-28 — torch.profiler 包整个 generate_image() → 23GB+ trace 爆炸 | [2026-04-28-profiling-and-model-loading-13](2026-04-28-profiling-and-model-loading-13.md) |
| 2026-04-28 — diff_infer_steps 参数不是 generate_image 的 kwarg | [2026-04-28-profiling-and-model-loading-14](2026-04-28-profiling-and-model-loading-14.md) |
| 2026-04-28 — vllm-omni profiler delay_iterations:1 + 单请求 → 空 trace | [2026-04-28-profiling-and-model-loading-15](2026-04-28-profiling-and-model-loading-15.md) |
| 2026-04-28 — pkill -f python 杀死 SSH session | [2026-04-28-profiling-and-model-loading-16](2026-04-28-profiling-and-model-loading-16.md) |
| 2026-04-28 — monkey-patch F.scaled_dot_product_attention 没生效 | [2026-04-28-profiling-and-model-loading-17](2026-04-28-profiling-and-model-loading-17.md) |
| 2026-04-28 — patch 了错误的 cache 路径 | [2026-04-28-profiling-and-model-loading-18](2026-04-28-profiling-and-model-loading-18.md) |
| 2026-06-17 — LTX2.3 开图 profiling 把 eager trace 和 graph benchmark 混成一个结论 | [2026-06-17-profiling-and-model-loading-19](2026-06-17-profiling-and-model-loading-19.md) |
| 2026-06-17 — LTX2.3 mask-sync 优化看似减同步但会改精度 | [2026-06-17-profiling-and-model-loading-20](2026-06-17-profiling-and-model-loading-20.md) |
