# 遗言：只差运行 HF baseline 对比就能知道 vllm-omni 精度差在哪了

> 生成时间: 2026-04-29 11:01:32
> 项目路径: D:\vllm-omni\workflow-starter

## 项目背景

vLLM-Omni × HunyuanImage-3.0-Instruct。80B 多模态模型，AR（LLM）+ DiT（扩散）双阶段。

本次工作场景：T2T（text-to-text）offline 推理，只跑 AR 阶段（`mode="gen_text"`）。
远端服务器：`47.79.124.13:31230`（SSH root 直连）。
模型路径：`/mnt/models/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78.../`

## 本次会话目标

用户反馈 vllm-omni T2T 输出比 HF 官方模型缺少细节描述（无乱码、无重复，就是描述不丰富）。
本会话目标：
1. 统一 SDPA / FA 注意力后端
2. 跑 HF 官方 AR baseline，与 vllm-omni 输出对比，定位精度差异根因

## 已完成的工作

### 1. FA vs SDPA 对比测试（结论：两者输出完全相同）
- 测试脚本：远端 `/tmp/test_t2t_backends_v2.py`
- 配置：远端 `/tmp/t2t_tp2.yaml`（TP=2, temperature=0, greedy）
- 结论：FA 和 SDPA 输出逐字相同（2187 chars），**attention backend 不是精度差异的原因**
- 输出存档：`/tmp/t2t_fa_default.txt` 和 `/tmp/t2t_sdpa.txt`（内容一致）

### 2. process_image() Siglip2 兼容性修复（已 commit + push）
- 文件：`D:/vllm-omni/wt-hunyuan-t2t-sdpa-fa/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py`
- 问题：transformers ≥5.x 的 `Siglip2ImageProcessorFast` 返回 list 而非 tensor，`.squeeze(0)` 崩溃
- 修复：在 `process_image()` 约 854-868 行加 `isinstance(x, list)` 判断 + `torch.stack()`
- 已提交：commit `42ee44b6`，branch `feature/hunyuan-t2t-sdpa-fa`，repo `zuiho-kai/vllm-omni`

### 3. HF 模型 snapshot 已打好三个 patch

文件：`/mnt/models/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/modeling_hunyuan_image_3.py`

| Patch | 状态 | 说明 |
|-------|------|------|
| RoPE broadcast fix (Bug1) | ✅ 已打 | `seq_len = q.size(-2)` else 分支 |
| 2D attention_mask fix (Bug2) | ✅ 已打 | `attention_mask.ndim == 2` → None |
| lazy_initialization 单参数 | ✅ 正确 | 4.57.1 版只需 `(key_states)`，5.x 才要两个参数 |
| use_cache in prepare_inputs | ✅ 已打 | 取消注释，为 transformers 5.x 加的，4.57.1 不影响 |
| use_cache in _update_model_kwargs | ✅ 已打 | 同上 |

### 4. claudeception 知识固化
- 更新 `memory/feedback_hf_trust_remote_code.md` 新增 Rule 6（patch snapshot 不是 cache）和 Rule 7（runbook 版本不容置疑）

## 未完成的工作

### ⚠️ 主任务：跑 HF baseline 并与 vllm-omni 对比

**当前状态**：用户正在手动执行以下 4 步（会话结束时可能完成也可能没完成）

**Step 1 — 杀进程 + 确认 GPU 空闲**
```bash
pkill -9 -f python 2>/dev/null; sleep 5; nvidia-smi --query-gpu=index,memory.used --format=csv,noheader
```

**Step 2 — 确认 snapshot runbook patch 已在**（已验证两个都是 ✅）
```bash
SNAP=/mnt/models/hub/models--tencent--HunyuanImage-3.0-Instruct/snapshots/2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/modeling_hunyuan_image_3.py
grep -c 'seq_len = q.size(-2)' $SNAP    # 应输出 1
grep -c 'attention_mask.ndim == 2' $SNAP  # 应输出 1
```

**Step 3 — 清 module cache**
```bash
rm -rf /mnt/models/modules/transformers_modules/_2ec2c78bee7d4b94157341fba86c4c2c7b1858b2/
```

**Step 4 — 用 venv_hf（transformers 4.57.1）跑**
```bash
source /root/venv_hf/bin/activate && python /tmp/hf_baseline_ar.py 2>&1 | tee /tmp/hf_baseline_ar.log
```

### ⚠️ 对比分析（HF baseline 跑完后）
```bash
cat /tmp/t2t_hf_baseline.txt   # HF 官方 AR 输出
cat /tmp/t2t_fa_default.txt    # vllm-omni FA 输出
```
比较两者差异，判断是否有质量差距，找根因。

## 关键决策与发现

### FA = SDPA（已确认）
vllm-omni AR 的 FA 和 SDPA 路径在 temperature=0, greedy 下输出逐字相同。注意力后端不是精度差异来源。

### trust_remote_code 模型的 patch 必须改 snapshot（重要教训）
transformers 每次 `from_pretrained(..., trust_remote_code=True)` 都会从 snapshot 重建
`$HF_HOME/modules/transformers_modules/<hash>/`，覆盖所有对 cache dir 的手动修改。
**必须 patch snapshot + rm -rf cache dir**。

### venv 区分
- `/root/venv_hf` → transformers 4.57.1（HF baseline 专用，runbook 指定版本）
- `/root/venv` → transformers 5.6.2（vllm-omni 专用）

### transformers 版本 API 差异
- 4.57.1: `lazy_initialization(key_states)` — 1个参数
- 5.6.2: `lazy_initialization(key_states, value_states)` — 2个参数
- 4.50.0: `StaticCache` 没有 `layers` 属性，完全无法用

### HF 模型 gen_text 调用方式（正确）
```python
kw = model.prepare_model_inputs(prompt=PROMPT, mode="gen_text")
kw.pop("mode", None)          # 避免 duplicate kwarg
kw["use_cache"] = True        # 防止 transformers 5.x KeyError（4.57.1 不需要但无害）
out = model.generate(**kw, mode="gen_text", decode_text=True)
txt = out[0]  # decode_text=True 返回 List[str]
```

### 本次会话犯的错：在 5.6.2 上打补丁而不是直接用 runbook 指定的 4.57.1
打了 7+ 个补丁（lazy_init 参数/use_cache/KeyError），全是不必要的。教训写入 memory。

## 下一步建议

1. **确认 GPU 空闲**（`nvidia-smi`，两卡都应该 0 MiB）
2. **执行 Step 3 + Step 4**（清 cache，`source venv_hf` 跑 baseline）
3. **看 `/tmp/hf_baseline_ar.log` 输出**，如果报新错，优先读报错行附近的模型代码
4. 输出存到 `/tmp/t2t_hf_baseline.txt` 后，`diff /tmp/t2t_hf_baseline.txt /tmp/t2t_fa_default.txt` 对比

如果 HF baseline 跑通了且输出有明显质量差距，根因大概率在：
- prompt 格式（vllm-omni vs HF 的 input_ids 对比）
- KV cache 精度（fp16 vs bf16）
- generation config（temperature/top_p 等）

## 关键文件清单

| 文件 | 说明 |
|------|------|
| `远端 /tmp/hf_baseline_ar.py` | HF baseline 推理脚本（用 venv_hf 跑） |
| `远端 /tmp/hf_baseline_ar.log` | 最近一次运行日志 |
| `远端 /tmp/t2t_fa_default.txt` | vllm-omni FA 输出（2187 chars，基准） |
| `远端 /tmp/t2t_sdpa.txt` | vllm-omni SDPA 输出（与 FA 相同） |
| `远端 /tmp/t2t_tp2.yaml` | vllm-omni T2T 测试配置（TP=2） |
| `远端 snapshot/modeling_hunyuan_image_3.py` | HF 模型代码，已打 5 个 patch |
| `D:/vllm-omni/wt-hunyuan-t2t-sdpa-fa/vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py` | 本地 worktree，已修 process_image()，已 commit |
| `D:/vllm-omni/workflow-starter/memory/feedback_hf_trust_remote_code.md` | 本次会话新增 Rule 6/7 |
| `D:/vllm-omni/workflow-starter/memory/hf_baseline_runbook.md` | HF baseline 完整运行手册 |
| `C:\Users\user\.claude\plans\hunyuanimage3-ins-t2t-vllm-omni-t2t-sdp-quizzical-acorn.md` | 当前计划文件 |
