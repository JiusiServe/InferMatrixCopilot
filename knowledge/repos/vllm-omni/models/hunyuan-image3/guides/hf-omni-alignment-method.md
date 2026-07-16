## 触发条件

- 用户反馈"vllm-omni 离线推理输出和官方 HF 不一样"
- 用户给出"omni 输出 vs official 输出"的对比，omni 缺细节 / 死循环 / 重复
- 怀疑 attention backend、prompt 格式、tokenization、image embedding 之一

## 系统化排查顺序（从外向内）

### 1. attention backend 不是问题（先排除）
- 跑 vllm-omni FA 和 SDPA 对比（temp=0 greedy）
- 实测：HunyuanImage3 T2T 下两者输出**逐字相同**
- → 如果 FA/SDPA 一样，attention backend 排除

### 2. prompt 格式（最常见的 bug 源）
- 跑 HF baseline 拿"对的"输出和 input_ids 作为黄金参考
  - HF: `model.prepare_model_inputs(prompt=..., image=..., mode="gen_text", bot_task="think", system_prompt=en_unified)`
  - `do_sample=False, temperature=0.0` 强制 greedy
- 跑 vllm-omni 同样的 user_prompt + image，对比输出
- 如果 vllm-omni 死循环 / 开头无结构 → **build_prompt 格式错**
- 详见 `official_prompt_format.md`

### 3. input_ids 逐 token 对齐
- HF dump：`kw["input_ids"][0].cpu().tolist()`
- vllm-omni dump：在 build_prompt 后 `tok.encode(prompt_str)` 拿 token_ids
- 解码每个 token：`tok.decode([tid], skip_special_tokens=False)`
- 找第一个分叉位置：常见原因
  - **BPE 跨边界 merge**（如 `。\n\n → 3490` vs HF 的 `1811+271`）
  - **角色前缀拼写**（HF `Assistant:` token 72803 vs 错用 `A:` token 32）
  - **system prompt strip 问题**（末尾 `\n` 被 strip 后丢一个 token）
  - **image token 展开结构**（`<timestep>` vs `<img>` 占位）

### 4. 终极对齐：prompt_token_ids 路径
当文本 BPE 边界 merge 怎么调都对不上时，**绕过 vllm-omni 的整串 BPE**：

```python
# Build segment-by-segment to mimic HF apply_chat_template
ids = [bos_id]
ids += tok.encode(sys_text, add_special_tokens=False)
ids += tok.encode("\n\nUser: ", add_special_tokens=False)
ids += [img_token_id]    # placeholder, 不展开
ids += tok.encode(user_prompt, add_special_tokens=False)
ids += tok.encode("\n\nAssistant: ", add_special_tokens=False)
ids += [trigger_token_id]

# 用 prompt_token_ids 而非 prompt 字符串
results = omni.generate({
    "prompt_token_ids": ids,
    "multi_modal_data": {"image": image},
})
```

vllm-omni 原生支持（`OmniTokensPrompt` / `vllm_omni/inputs/data.py: token_inputs_omni()`）。

### 5. 还对不上 → 怀疑 image embedding 或 BF16 噪声
- vllm-omni 的 image token 展开（`hunyuan_image3.py:_get_prompt_updates`）和 HF 不完全同（如 `<timestep>` 占位差异，详见 `official_prompt_format.md`）
- BF16 数值噪声：greedy 在 logits 平局时也会让 vllm-omni 和 HF 走不同路径，是无法消除的下界
- 如果只想"行为一致" 而非 byte-identical：到此可以收工

### 关键认识：「文本 token 一样 ≠ 输出一样」

因果注意力的污染机制：

```
input：[text 0..1226] [image_segment 1227..6207] [user_text 6208..N] [\n\nAssistant: <think>]
                       ^^^^^^^^^^^^^^^^^^^^^^^^^
                       这段两边只要差 1 个 token（如 <timestep> vs <img>）
                       或差 1 个 BF16 ULP 的 image embedding 值，
                       后续所有位置算 attention 时都会拿到不同的 K/V
                       到 <think> 这个生成起点时，模型状态已经分叉

→ 第 1 个生成 token 就分叉，后面用 greedy 走完全不同路径
```

所以"文本 portion 前 1227 token byte-identical"**不足以保证输出一致**，仍要排查 image segment 的 token 结构和 embedding 数值。

### 关键认识 2：sampling 模式下 vllm 和 HF transformers 的 sampler 不可对齐

哪怕 input_ids、temperature、top_p、top_k、max_tokens、seed 全设成一样，**sampling 输出也不会逐字相同**。原因：

| 项 | HF transformers | vLLM-omni |
|---|---|---|
| 采样函数所在位置 | `transformers/generation/utils.py: _sample()` | `vllm/v1/sample/sampler.py` |
| RNG 来源 | `torch.manual_seed(42)`（**全局** RNG） | `torch.Generator().manual_seed(req.seed)`（**per-request**）|
| `torch.multinomial` 用哪个 RNG | 全局——**会被 model.forward 里偷偷消耗 RNG 的 op 干扰** | 独立 generator——不被 forward 影响 |
| logits processors 顺序 | 默认 `min_length → temperature → top_p → top_k → ...` | 常 `temperature → top_k → top_p`（fused kernel）|
| top_k 实现 | logits 设 `-inf` 后 softmax | 可能 sort + truncate + renormalize |
| BF16 reduction | PyTorch 默认顺序 | Triton fused kernel 顺序 → 1e-5 量级数值差 |

任意一项差异都让"seed=42 抽到的下一个 token"不同。第一个 token 不同 → KV cache 分叉 → 后续 token 全部分叉 → 100 token 后输出完全不相关。

**实测**（HunyuanImage3 IT2I sampling temp=0.6 seed=42，本会话 2026-04-29）：
- HF：1255 字（停在 `</think>`）
- omni（同 seed 同 yaml）：2751 字（写完 think + recaption-style + image_2 幻觉）
- A/B 测 prompt-string vs prompt_token_ids 路径：2936 vs 2751，**两个路径量级一样**——证明长度差异**不是 BPE fix 引入的**，是 sampler 实现本质差异

→ **要 byte-identical 输出 = 不可能**（除非 vllm 调 transformers `_sample`，违背 vllm 存在意义）。
→ 如果 demand 是 byte-identical：直接劝退，改对齐**功能性指标**（关键元素覆盖、结构标签命中率）。
→ 单 seed 对比信号弱，要论证质量必须**多 seed 统计**或**改 greedy 缩窄变量**。

### 隐藏陷阱：max_tokens 不影响自然 stop

omni 在 max_tokens=2048 vs 4096 下输出**完全相同**（2751 字、byte-identical），因为模型在 ~1500 token 时已经自然 hit `<|endoftext|>` 停了。max_tokens 只是上限，不强制截断。所以"对齐 max_tokens"对中长输出的 sampling 对比**没有效果**。

## 测试覆盖陷阱（避免走老路）

历史 PR（#2713/#3107）的"已对齐"声明在多个组合下不成立。**不要相信 PR 描述里"已通过"的字样**，先确认它跑了哪条路径，再对照本方法论补漏。详见 `feedback_pr_test_path_audit.md`。

## 验证模板

写**两个独立测试脚本**（不要混在一起，避免 kv-cache 复用）：

- `test_*_hf.py`（用 `<OTHER_USER_ROOT>/bin/activate`，transformers==4.57.1）
  - 调 `model.prepare_model_inputs` + `model.generate(do_sample=False, temperature=0.0, decode_text=True)`
  - dump `kw["input_ids"]`
- `test_*_omni.py`（用 `<OTHER_USER_ROOT>/bin/activate`，transformers==5.6.2）
  - 调 `omni.generate({"prompt_token_ids": ids, "multi_modal_data": {...}})`（避免 BPE 整串重新 encode）
  - 需要 `if __name__ == "__main__":` 包住 main（避免 multiprocessing bootstrap error）

`yaml` 配置：用 `hunyuan_image3_i2t.yaml`（AR-only，requires_multimodal_data=true，`is_comprehension=true`，`final_output_type=text`），temp=0，max_tokens=2048，stop=`[127957, 128026]`。

## 实证

- 修复前 IT2I greedy：vllm-omni 输出死循环 garbage（`最终图像完整保留了image_1...`×7）
- 修复 prompt 格式后：vllm-omni 输出结构对、关键元素全覆盖
- 用 prompt_token_ids 路径后：**前 1227 token 与 HF byte-identical**（图像位置之前完全一致）
- 不能修的部分：
  - 图像内 `<timestep>` 展开差异（深耦合，不能单点改 token id）
  - BF16 数值噪声 + transformers 5.6.2（vllm-omni venv 锁死） vs 4.57.1（HF venv） 的 Siglip2 normalize 路径差异
  - sampling 时 vllm sampler ≠ transformers sampler（不同 RNG primitive、不同 logits processor 顺序、不同 BF16 fused kernel）

## HunyuanImage3 transformers 版本约束

官方 README 没硬性写 transformers 版本，但 [requirements.txt](https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/blob/main/requirements.txt) pin 了 `transformers[accelerate,tiktoken]==4.57.1`。

**vllm 实际允许的 transformers 范围**：`>= 4.56.0, != 5.0.*, != 5.1.*, != 5.2.*, != 5.3.*, != 5.4.*, != 5.5.0`——也就是 **4.57.1 完全在允许范围内**。`<OTHER_USER_ROOT>` 默认装的是 5.6.2 只是因为没 pin 让 pip 挑了最新版，不是硬性约束。

→ **omni venv 也可以装 transformers==4.57.1**（和 venv_hf 同版本），消除 Siglip2 list-vs-tensor 兼容差异。

**但实测（2026-04-29）**：把 omni venv 从 5.6.2 降到 4.57.1，跑同一个 IT2I greedy 测试，输出**byte-identical**（2167 字完全相同）。说明：
- vllm-omni 的 `process_image()` 在 transformers 5.6.2 vs 4.57.1 下产生的预处理 tensor 数值**没有可观测差异**（或者差异在 BF16 量化后被消化了）
- omni 和 HF 之间剩下的 800+ 字输出长度差，**不来自 transformers 版本**
- 真正的差异源是更深的两套实现差：vllm-omni model forward vs HF modeling forward（独立代码）、PagedAttention KV cache 数值、image token routing 细节

→ 装 4.57.1 可以做（消除 list-vs-tensor 兼容代码 + 跟官方版本对齐），但不要指望它修好输出对齐——本会话实测证明它一字不差。

（更早版本的本文件先错把"omni 锁 5.x"写成硬约束，又错把"transformers 版本是数值差异源"写成假设——两次都错，已修正——勿信）

## 用过的资源

- HF 官方 demo image: `https://github.com/Tencent-Hunyuan/HunyuanImage-3.0/raw/main/assets/demo_instruct_imgs/input_0_0.png`
- HF generation_config 默认：`use_system_prompt="en_unified"`，`bot_task="think_recaption"`，`temperature=0.6` (默认采样)
- 验证用例 prompt：`"新年宠物海报，Q版圆润的可爱标题..."` (中文)，`"Describe the Eiffel Tower in detail..."` (英文 T2T)
