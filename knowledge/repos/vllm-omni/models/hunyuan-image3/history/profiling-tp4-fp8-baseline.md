测试时间：2026-04-27，节点 hk01dgx036（H800 80GB × 8），NUM_STEPS=20，NUM_PROMPTS=2，1024×1024

**tp4_fp8 结果：**
- 端到端延迟均值：2.85s
- `HunyuanImage3Pipeline.model.forward`（全部 transformer layers）：1.147s
- `HunyuanImage3Pipeline.vae.decode`：0.487s
- `model.layers[0].forward`（单层）：0.154s
- `model.layers[0].self_attn.forward`：0.059s
- `model.layers[0].mlp.forward`：0.068s
- 峰值显存：32.8 GB（4 卡共享）
- 吞吐：0.35 req/s

**Why:** tp2_fp8_sp2 和 tp2_fp8_cfgp2 因节点 GPU 全满未跑，待补充。

**How to apply:** 对比 HF baseline 和其他并行配置时用此数据作参照。
