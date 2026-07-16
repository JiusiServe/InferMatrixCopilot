## 环境要求

- transformers==4.57.1（官方 requirements.txt 指定版本）
- torch==2.8.0+cu128, torchvision==0.23.0（必须一起 pin，不能单独装 torchvision）
- einops, diffusers==0.35.2
- `config.json` 里必须有 `"model_version": "instruct"`（原始 config 缺这个字段，需手动补）

## 必修 Bug Fix（不修就崩）

模型代码有两个 bug，必须 patch **snapshot + cache 两个文件**：

**文件位置**（以实际 traceback 为准）：
- Snapshot: `$HF_HOME/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/<hash>/modeling_hunyuan_image_3.py`
- Cache: `~/.cache/huggingface/modules/transformers_modules/_<hash>/modeling_hunyuan_image_3.py`

> 注意：`HF_HOME` 不同时 cache 路径也不同。先跑一次看 traceback 确认实际路径再 patch。

### Bug 1: RoPE 广播导致 key/value size 不匹配

**症状**: `RuntimeError: Expected key.size(1) == value.size(1) to be true, but got false`

**根因**: CFG unconditional 路径 `position_ids=None`，cos/sin `[1, max_pos_emb, head_dim]` 广播把 key 从 `[...,1,...]` 扩到全长，value 不过 RoPE 保持 1。

**Fix**: `apply_rotary_pos_emb` 函数（约 line 547），在 `position_ids is not None` 分支后加 else：

```python
    if position_ids is not None:
        cos = cos[position_ids]
        sin = sin[position_ids]
    else:
        seq_len = q.size(-2)
        cos = cos[..., :seq_len, :]
        sin = sin[..., :seq_len, :]
```

### Bug 2: CFG 2D attention_mask 传给 SDPA

**症状**: `The expanded size of the tensor (1) must match the existing size (2) at non-singleton dimension 3`

**根因**: transformers 4.57.1 的 `UnbatchedClassifierFreeGuidanceLogitsProcessor` 传 2D `[1, N]` padding mask，SDPA 期望 4D。

**Fix**: `HunyuanImage3SDPAAttention.forward`（约 line 1362），在 SDPA 调用前加：

```python
        if attention_mask is not None and attention_mask.ndim == 2:
            attention_mask = None
```

### 自动 Patch 脚本

```python
#!/usr/bin/env python3
"""Patch HunyuanImage3 model bugs. Run ONCE after model download."""
import sys

SNAP = "<snapshot_path>/modeling_hunyuan_image_3.py"  # 填实际路径
CACHE = "<cache_path>/modeling_hunyuan_image_3.py"    # 填实际路径

# Bug 1: RoPE broadcast
ROPE_OLD = """    if position_ids is not None:
        cos = cos[position_ids]
        sin = sin[position_ids]

    cos = cos.unsqueeze(unsqueeze_dim)"""
ROPE_NEW = """    if position_ids is not None:
        cos = cos[position_ids]
        sin = sin[position_ids]
    else:
        seq_len = q.size(-2)
        cos = cos[..., :seq_len, :]
        sin = sin[..., :seq_len, :]

    cos = cos.unsqueeze(unsqueeze_dim)"""

# Bug 2: 2D attention_mask
MASK_OLD = """        if attention_mask is not None and not attention_mask.is_floating_point() and attention_mask.dtype != torch.bool:
            attention_mask = attention_mask.to(query_states.dtype)
        attn_output = torch.nn.functional.scaled_dot_product_attention("""
MASK_NEW = """        if attention_mask is not None and attention_mask.ndim == 2:
            attention_mask = None
        if attention_mask is not None and not attention_mask.is_floating_point() and attention_mask.dtype != torch.bool:
            attention_mask = attention_mask.to(query_states.dtype)
        attn_output = torch.nn.functional.scaled_dot_product_attention("""

for path in [SNAP, CACHE]:
    with open(path) as f:
        code = f.read()
    patched = False
    if ROPE_OLD in code:
        code = code.replace(ROPE_OLD, ROPE_NEW); patched = True
    if MASK_OLD in code:
        code = code.replace(MASK_OLD, MASK_NEW); patched = True
    if patched:
        with open(path, 'w') as f: f.write(code)
        print(f"Patched: {path}")
    else:
        print(f"Already patched or pattern mismatch: {path}")
```

## 关键参数陷阱

### diff_infer_steps 不是 generate_image 的 kwarg

```python
# ❌ 错误：不生效，模型用默认 50 步
model.generate_image(prompt=..., diff_infer_steps=10)

# ✅ 正确：改 generation_config
model.generation_config.diff_infer_steps = 10
model.generate_image(prompt=...)
```

### cot_text 跳过 AR 阶段

`generate_image` 接受 `cot_text` 参数（list of str），传入后跳过 AR thinking/recaption 生成，直接进 diffusion。

```python
# 第一次跑拿 cot_text
cot_text, samples = model.generate_image(prompt=..., verbose=0)
# 后续跑直接传 cot_text，跳过 AR（省 5-7 分钟）
_, samples = model.generate_image(prompt=..., cot_text=cot_text)
```

> 注意：即使传了 cot_text，模型仍需做 AR prefill（处理 system prompt + cot_text），只是不再生成 thinking 文本。

### guidance_scale 的 kwarg 泄漏

`generate_image(guidance_scale=5.0)` 会通过 `**kwargs` 泄漏到 gen_text 阶段的 `super().generate()`，触发 transformers 的 `UnbatchedClassifierFreeGuidanceLogitsProcessor`。这是模型代码的 bug，上面两个 fix 已经兜住了。

## torch.profiler 精确控制（关键！）

### 问题

80B 模型即使只跑 13s，profiler 包整个 `generate_image()` → 250GB+ RSS，23GB+ trace。原因是 AR prefill（1234 tokens × 33 layers × MoE）产生百万级 kernel 调用。

### 解法：monkey-patch progress_bar 只包 denoising loop

```python
_prof_holder = [None]  # None = profiler inactive
_orig_progress_bar = model.pipeline.progress_bar

def _patched_progress_bar(*args, **kwargs):
    pb = _orig_progress_bar(*args, **kwargs)
    class WrappedPB:
        def __init__(self, inner): self._inner = inner
        def __enter__(self):
            r = self._inner.__enter__()
            if _prof_holder[0] is not None:
                torch.cuda.synchronize()
                _prof_holder[0].__enter__()
            return r
        def __exit__(self, *a):
            if _prof_holder[0] is not None:
                torch.cuda.synchronize()
                _prof_holder[0].__exit__(*a)
            return self._inner.__exit__(*a)
        def update(self): self._inner.update()
    return WrappedPB(pb)

model.pipeline.progress_bar = _patched_progress_bar

# Warmup（profiler inactive）
model.generate_image(prompt=..., cot_text=cot_text, verbose=0)

# Profiling（profiler active）
prof = profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
               record_shapes=True, profile_memory=False)
_prof_holder[0] = prof
_, samples = model.generate_image(prompt=..., cot_text=cot_text, verbose=1)
prof.export_chrome_trace("trace.json")  # ~1.2GB (79MB gz)
```

### 结果对比

| 方法 | trace 大小 | RSS |
|------|-----------|-----|
| 包整个 generate_image | 23GB+ | 250GB+ |
| 只包 denoising loop | 1.2GB (79MB gz) | 正常 |

## vllm-omni profiler 注意事项

- `delay_iterations:1` + 单请求 = 空 trace（profiler 跳过唯一请求）
- 单请求 profiling 必须 `delay_iterations:0`
- 50 步 trace ~79MB/rank gz，10 步 ~47MB/rank gz

## device_map 说明

脚本用 `device_map="auto"`（accelerate 自动分层），是 **layer parallelism**，不是 tensor parallelism：
- 每层只在 1 张卡上跑，激活值逐层搬运，同一时刻只有 1 张卡在算
- 4x L20X 实测显存分布：GPU0 61GB / GPU1 47GB / GPU2 47GB / GPU3 39GB（不均匀）
- 对比 vllm-omni TP=4：每层切 4 份，4 卡同时算

这是 HF baseline 比 vllm-omni 慢的核心原因之一。对比 trace 时注意：HF trace 是单进程多卡（layer parallel），vllm-omni 是 4 rank（tensor parallel）。

## 完整运行顺序

1. 确认环境（transformers 版本、config.json 有 model_version）
2. **Patch 两个 bug**（snapshot + cache 文件）
3. 加载模型，设 `generation_config.diff_infer_steps`
4. 跑一次拿 cot_text（或从之前的日志提取）
5. Warmup（传 cot_text，3 步，无 profiler）
6. Profiling（monkey-patch progress_bar，传 cot_text，10 步）
7. 导出 trace + gzip
