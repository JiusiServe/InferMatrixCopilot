# 遗言：HF官方baseline的SDPA死活key_size不等于value_size就差这一个trace了

> 生成时间: 2026-04-28 10:59:30
> 项目路径: D:\vllm-omni\workflow-starter（本地）/ root@47.79.124.13:31182（远端云实例）

---

## 项目背景

**vLLM-Omni × HunyuanImage-3.0-Instruct** profiling 对比工程。

- 仓库：`zuiho-kai/vllm-omni`，分支 `pr-3055`
- 远端：L20X × 4（140GB/卡），阿里云容器实例，`root@47.79.124.13:31182`（SSH 直连）
- 共享存储：`/mnt`（1.8PB CPFS），模型在 `/mnt/models/hub`
- 两个 venv：
  - `/root/venv` — vllm 0.19.1 + vllm-omni（torch 2.7.0+cu126, transformers 5.6.2）
  - `/root/venv_hf` — HF 官方环境（torch 2.8.0+cu128, transformers 4.57.1）

---

## 本次会话目标

1. 在全新云实例上跑 3 个 vllm-omni profiling 配置（tp4_fp8 / tp2_fp8_sp2 / tp2_fp8_cfgp2）
2. 拿 torch profiler trace JSON（可在 chrome://tracing 看时序图）
3. 跑 HF 官方 baseline 的 torch profiler trace 做对比

---

## 已完成的工作

### 1. 云实例环境搭建
- 安装 uv、创建 venv、安装 vllm 0.19.1
- `git clone https://github.com/zuiho-kai/vllm-omni.git --branch pr-3055`（先从本地 push 了 pr-3055 到 zuiho-kai fork）
- 下载 HunyuanImage-3.0-Instruct 模型到 `/mnt/models/hub`（158GB）
- Patch `pipeline_hunyuan_image3.py:114`：`Siglip2VisionModel(vision_config).vision_model` → `Siglip2VisionModel(vision_config)`（transformers 5.6.2 兼容）

### 2. vllm-omni 三配置 stage_durations benchmark ✅
结果 JSON 已下载到本地：
- `profiling_l20x_tp4_fp8.json` — 5.87s 延迟，model.forward 3.96s，47GB/卡
- `profiling_l20x_tp2_fp8_sp2.json` — 5.40s 延迟，model.forward 3.54s，66GB/卡
- `profiling_l20x_tp2_fp8_cfgp2.json` — 4.40s 延迟，model.forward 3.07s，66GB/卡
- `profiling_l20x_results.json` — 汇总

### 3. vllm-omni tp4_fp8 torch profiler trace ✅
- 4 rank trace 文件已下载并解压到 `D:\vllm-omni\workflow-starter\torch_traces\tp4_fp8\20260428-023238_stage_0_diffusion_1777343558\`
- `trace_rank{0-3}.json`（每个 ~889MB）+ `profiler_out_{0-3}.txt`
- Top 算子：fused_moe 820ms(16.6%), fmha_cutlass 695ms(14%), nccl_allreduce 653ms(13.2%), cudnn_conv(VAE) 534ms(10.8%)

### 4. HF 官方环境搭建 ✅
- `/root/venv_hf`：torch==2.8.0+cu128, transformers==4.57.1（官方 requirements.txt 精确版本）
- 额外装了 einops, diffusers==0.35.2, torchvision==0.23.0
- `config.json` 补了 `"model_version": "instruct"`（原始 config 缺这个字段）

### 5. Error book 更新 ✅
- `.claude_errors/remote_and_ssh.md`：盲等 210s 不看日志、Siglip2VisionModel 版本不兼容
- `.claude_errors/profiling_and_model_loading.md`：Siglip2 patch、HF baseline 版本夹缝问题

---

## 未完成的工作

### ❌ HF 官方 baseline torch profiler trace

**当前阻塞点**：`model.generate_image()` 在 AR decode 阶段崩溃。

**错误**：
```
File ".../modeling_hunyuan_image_3.py", line 1363, in forward
    attn_output = torch.nn.functional.scaled_dot_product_attention(
RuntimeError: Expected key.size(1) == value.size(1) to be true, but got false.
```

**已尝试的方案**：
1. ❌ `attn_implementation="sdpa"` + transformers 5.6.2 → `StaticLayer.lazy_initialization() missing 1 required positional argument`
2. ❌ `attn_implementation="sdpa"` + transformers 4.50.0 → `HunyuanStaticCache has no attribute 'layers'`
3. ❌ `attn_implementation="sdpa"` + transformers 4.57.1（官方版本）→ `key.size(1) != value.size(1)`
4. ❌ `attn_implementation="eager"` + transformers 4.57.1 → **同样的 SDPA 错误**（eager 没生效）
5. ❌ Patch `attn_mask` dtype（long→bfloat16）→ 解决了 dtype 问题但 key/value size 不匹配仍在
6. ❌ Patch snapshot + modules 两个目录 → transformers 重新复制代码覆盖 patch

**根因分析（最后一步发现）**：
- `attn_implementation="eager"` 传给了 `from_pretrained`，但模型自定义代码有**自己的 attention dispatch**
- `modeling_hunyuan_image_3.py:1375`：`Hunyuan_ATTENTION_CLASSES = {...}` 硬编码了 attention 类
- `line 1388-1389`：`if attn_impl in Hunyuan_ATTENTION_CLASSES: self.self_attn = Hunyuan_ATTENTION_CLASSES[attn_impl](...)`
- 只有 `HunyuanImage3SDPAAttention`（line 1257），没有 eager 实现
- **所以 `attn_implementation="eager"` 被忽略了，始终走 SDPA**

**下一步修复方向**：
```python
# 方案 A：在 Hunyuan_ATTENTION_CLASSES 里加一个 eager 实现
# 查看 line 1375 的 dict，加一个用 torch.matmul 的 eager class

# 方案 B：直接 patch HunyuanImage3SDPAAttention.forward
# 把 scaled_dot_product_attention 替换成手动 matmul + softmax
# 这样不需要改 dispatch 逻辑

# 方案 C：修 HunyuanStaticCache.update() 确保 key/value size 一致
# 根因可能在 cache 的 update 方法里
```

**HF trace 脚本已上传到远端**：`/tmp/bench_hf_trace.py`（用 `torch.profiler` 包裹 `generate_image` 单次调用）

---

## 关键决策与发现

1. **模型存 /mnt（CPFS 共享存储）**：1.8PB，SSD，可跨实例复用
2. **vllm-omni 是纯 Python overlay**：不需要编译 CUDA 扩展，`pip install -e .` 秒装
3. **pr-3055 分支**：HunyuanImage3 支持只在这个分支，需要先 push 到 zuiho-kai fork 才能远端 clone
4. **transformers 版本地狱**：
   - 模型仓库 config.json 写的 `transformers_version: 4.50.0`
   - 官方 requirements.txt 写的 `transformers==4.57.1`
   - 模型的 custom code（trust_remote_code）会被 transformers 从 snapshot 复制到 `~/.cache/huggingface/modules/`，每次加载都重新复制
5. **Hunyuan_ATTENTION_CLASSES 硬编码**：模型自定义了 attention dispatch，忽略 `attn_implementation` 参数
6. **CFG-Parallel 最快**：tp2_fp8_cfgp2 比 tp4_fp8 快 25%（4.40s vs 5.87s）

---

## 下一步建议（新会话直接执行）

### 优先级 1：修 HF baseline trace

```bash
# SSH 进入
ssh -p 31182 root@47.79.124.13

# 查看 attention dispatch
source /root/venv_hf/bin/activate
grep -n "ATTENTION_CLASSES" /mnt/models/modules/transformers_modules/_2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/modeling_hunyuan_image_3.py

# 方案 B（最快）：直接在 HunyuanImage3SDPAAttention.forward 里把 SDPA 换成手动 matmul
# 需要同时 patch snapshot 和 modules 两个目录的文件：
# /mnt/models/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/modeling_hunyuan_image_3.py
# /mnt/models/modules/transformers_modules/_2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/modeling_hunyuan_image_3.py

# Patch 后跑：
export HF_HUB_OFFLINE=1
python /tmp/bench_hf_trace.py
```

### 优先级 2：释放云实例（省钱）

跑完后删实例，模型在 /mnt 可复用。

---

## 关键文件清单

| 文件 | 说明 |
|------|------|
| `profiling_l20x_results.json` | 三配置汇总结果 |
| `profiling_l20x_tp4_fp8.json` | tp4_fp8 完整 benchmark JSON |
| `profiling_l20x_tp2_fp8_sp2.json` | tp2_fp8_sp2 完整 benchmark JSON |
| `profiling_l20x_tp2_fp8_cfgp2.json` | tp2_fp8_cfgp2 完整 benchmark JSON |
| `torch_traces/tp4_fp8/.../trace_rank{0-3}.json` | tp4_fp8 torch profiler trace（chrome://tracing 可视化） |
| `torch_traces/tp4_fp8/.../profiler_out_{0-3}.txt` | tp4_fp8 profiler 摘要 |
| `run_diffusion_profiling.txt` | vllm-omni profiling 脚本（bash） |
| `analyze_torch_trace.py` | 当时使用的临时 trace 分析脚本，现已从框架仓库删除 |
| `bench_hf_trace.py` | HF 官方 torch profiler 脚本（已上传远端 /tmp/） |
| `bench_hf_dit_only.py` | DiT-only benchmark 脚本（未跑通） |
| `patch_attn_mask.py` | attn_mask dtype patch 脚本 |
| `.claude_errors/profiling_and_model_loading.md` | profiling 踩坑记录 |
| `.claude_errors/remote_and_ssh.md` | 远端操作踩坑记录 |
