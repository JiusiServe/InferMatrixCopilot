## PR #3243 最终交付（2026-04-30 cherry-pick 后）

分支 `feature/hunyuan-t2t-sdpa-fa`，从 origin/main 起 10 个 commit，**只动 4 个文件**：

```
examples/offline_inference/hunyuan_image3/end2end.py            +99 -0
vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py +366 -5
vllm_omni/model_executor/stage_configs/hunyuan_image3_i2t.yaml  +1 -1
vllm_omni/model_executor/stage_configs/hunyuan_image3_t2t.yaml  +1 -1
```

Commit 序列（按时间）：

| # | hash | 类型 | 干啥 |
|---|---|---|---|
| 1 | `d71981e7` | fix | Siglip2 transformers≥5.x 返回 list 的 squeeze 兼容 |
| 2 | `d360569a` | fix | T2T `build_prompt` 改 instruct 格式（早版） |
| 3 | `27083f9c` | fix | 统一所有 chat 任务用 instruct chat 模板，trigger 在 `Assistant:` 之后 |
| 4 | `ea809348` | fix | `A:` → `Assistant:` 匹配 HF tokenizer 实际输出（token 72803） |
| 5 | `7bd429ed` | fix | 新增 `build_prompt_tokens()` 走 prompt_token_ids 路径，绕过 BPE 跨段 merge |
| 6 | `3d415e17` | docs | `<timestep>` slot 用 `<img>` 占位 + 注入 `timestep_emb(0)` 与 HF 等价 |
| 7 | `8a1a4af9` | docs | image preprocessing 已对齐 HF（resize/crop math + VAE normalize 一致） |
| 8 | `41d29432` | fix | VAE pixel cast 从 process_image 挪到 _vae_encode 入口（fp32 byte-identical） |
| 9 | `31c2fa56` | fix | **fp32 MoE router**（subclass + custom_routing_function 绕过 bf16 topk_softmax） |
| 10 | `07d8cf0d` | fix | i2t/t2t yaml 的 stop_token_ids 加 `</think>` (128024) |

**重要**：history 在 2026-04-30 重写过——之前夹带了 5 个 GEBench CI commit + 1 个 merge commit（共 96 files / 1287+1431 lines 污染），用 `git checkout -b feature/hunyuan-image3-ar-alignment origin/main && git cherry-pick <10 commits>` 重做 + force-push。详见 `feedback_pr_branch_pollution.md`（如果未来又出问题）。

## 三个 yaml 的 stop_token_ids 对照表

| yaml | is_comprehension | final_output_type | stop_token_ids | 何时停 |
|---|---|---|---|---|
| `hunyuan_image3_i2t.yaml` | true | text | **`[127957, 128024, 128026]`**（加了 `</think>`） | `</think>` 时停（跟 HF `bot_task="think"` 同款） |
| `hunyuan_image3_t2t.yaml` | true | text | **`[127957, 128024, 128026]`**（加了 `</think>`） | 同上 |
| `hunyuan_image3_it2i.yaml` | **false** | image | `[127957]`（**故意不加** `</think>`） | 走完整 think→recap→answer→boi→size→ratio→4096 image tokens → EOS 才停（要喂 DiT） |

`is_comprehension=false` 时 `_StageTransitionLogitsProcessor` 启用，在 `</think>` 强制 emit `<recaption>`，在 `</recaption>` 强制 emit `<answer><boi><img_size_*>`，然后 `_ConditionalSliceVocabLogitsProcessor` 把 vocab mask 成只允许 ratio token。完成 ratio 后再继续 emit 4096 个 image latent token IDs 给 DiT。

## image embedding 6 层全部已对齐

| # | 层面 | 状态 | 来源 |
|---|---|---|---|
| 1 | resize/crop math（int(round) 顺序、LANCZOS、center crop region）| ✅ byte-identical | docs commit `8a1a4af9` |
| 2 | VAE PIL→tensor（`Normalize([0.5],[0.5])`）| ✅ byte-identical | 同上 |
| 3 | VAE pixel dtype cast 时机 | ✅ 修了 fp32 mean=0.157296 byte-identical | fix commit `41d29432` |
| 4 | `<timestep>` slot routing（HF `<timestep>` vs omni `<img>` 占位）| ✅ embedding 层等价 | docs commit `3d415e17`。**单点改 token id 必崩**（routing 深耦合）|
| 5 | embed_multimodal 拼接顺序 `[timestep, vae, vit]`（hunyuan_image3.py:1850）| ✅ 等价 HF | HF 用 scatter（`instantiate_vae/vit/continuous_tokens`），omni 用 cat→merger 替换 `<img>`，最终 hidden_states 一致 |
| 6 | Siglip2 ViT normalize transformers 5.x vs 4.x ~1 ULP 差异 | ✅ 消除 | omni venv 降到 4.57.1（详见 `hf_omni_alignment_method.md`） |

后向证据：Mode 2（think+recap）前 64 chars (~21 tokens) byte-identical with HF——如果 image embedding 有 bug，第 1 个 token 就会偏。

## 对齐数据（greedy temp=0, 2× L20, TP=2）

测试 prompt：`"新年宠物海报，Q版圆润..."` + `assets/demo_instruct_imgs/input_0_0.png`

### Mode 1: AR-only think（HF `bot_task="think"` vs omni `is_comprehension=true` + stop `</think>`）

| | HF baseline | omni this PR | gap |
|---|---|---|---|
| chars | 466 | 482 | +16 / +3.4% |
| 共同前缀 | — | — | 52 chars (~17-18 token byte-identical) |

### Mode 2: AR think+recap（HF `model.generate_image(bot_task="think_recaption")` AR portion vs omni `is_comprehension=false` + stop `</recaption>`）

| | HF official | omni this PR | gap |
|---|---|---|---|
| total chars | 777 | 811 | +34 / +4.4% |
| think 段 | 448 | 482 | +34 |
| **recap 段** | **329** | **329** | **byte 长度精确一致** |
| 共同前缀 | — | — | 64 chars (~21 token byte-identical) |

**recap 段长度 329=329 是 stage_transition 等价的最强证据**——证明 omni `_StageTransitionLogitsProcessor` 跟 HF `generate_image()` 内部传给 `model.generate()` 的 `stage_transitions` 参数是同款机制。

## 不可修的架构差异（列出来挡未来同类 review 问题）

剩下 +16/+34 chars 的 gap 全部来自 vllm 为性能做的实现选择，**不可修除非把 vllm 换成 HF**：

1. **PagedAttention KV cache**（block-paged 16 token/block）vs HF contiguous tensor → `softmax(QK^T)V` 的 reduction 顺序不同
2. **Triton fused MoE expert MLP**（per-expert 加权和的 reduction 顺序）vs HF python loop 串行加 → BF16 reduction 顺序不同（**注意：跟本 PR 修的 fp32 router 不是同一个东西，router 是"选哪些 expert"，expert MLP 是"expert 算完后怎么加起来"**）
3. **TP=2 sharded matmul + all-reduce** vs HF 单 GPU per-matmul（HF `device_map="auto"` 是 layer-wise pipeline split，每个 matmul 仍在一张 GPU 上完整算）→ all-reduce 顺序差
4. **TP-sharded fp32 gate matmul** 跟 HF 单 GPU full-rank fp32 matmul 在 reduction tree 上不同（虽然两边都是 fp32）
5. **vllm sampler vs transformers sampler** RNG primitive / logits processor 顺序 / top_k 实现差（sampling 模式才有影响，greedy 影响 0）

## HF AR baseline 测试模板（避免下次又翻车）

```python
# === MUST: replicate HF official `generate_image()` AR portion ===
sys_text = get_system_prompt("en_unified", "think_recaption", None)  # 同 bot_task
model_inputs = model.prepare_model_inputs(
    prompt=USER_PROMPT, image=image, system_prompt=sys_text,
    mode="gen_text", bot_task="think",  # ← first_bot_task!
)
model_inputs.pop("max_new_tokens", None)   # ← 必 pop, generation_config 已经塞了
model_inputs.pop("eos_token_id", None)     # ← 必 pop, 同上

tkw = model._tokenizer
stage_transitions = [(tkw.end_of_think_token_id, [tkw.convert_tokens_to_ids(tkw.recaption_token)])]
final_stop_tokens = [tkw.end_of_recaption_token_id]

outputs = model.generate(
    **model_inputs, mode="gen_text", decode_text=True,
    do_sample=False, temperature=0.0,
    max_new_tokens=2048,
    stage_transitions=stage_transitions,    # ← omni 同款 _StageTransitionLogitsProcessor
    final_stop_tokens=final_stop_tokens,    # ← 在 </recaption> 停, 不进 image gen
)
```

**禁止替换成** `model.generate(bot_task="auto", eos_token_id=[...])`——绕过 stage_transitions 拿到的不是官方推荐跑法的 baseline。详见 `feedback_check_official_demo_first.md`。

## 关键源码位置

- HF `generate_image()` 内部 stage_transitions 拼装：`hunyuan3.0_ins/modeling_hunyuan_image_3.py:3237-3320`
- HF `HunyuanTopKGate.__init__` (fp32 wg)：`hunyuan3.0_ins/modeling_hunyuan_image_3.py:1102`
- HF `HunyuanMoE.forward` (autocast disabled around router)：`hunyuan3.0_ins/modeling_hunyuan_image_3.py:1204`
- HF `HunyuanTopKGate.easy_topk` (fp32 softmax+topk+clamp)：`hunyuan3.0_ins/modeling_hunyuan_image_3.py:1132`
- omni `HunyuanImage3SparseMoeBlock`（fp32 router subclass）：`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1156-1278`
- omni `_patch_moe_blocks()`（post-init module replacement + 前置 cleanup）：`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py:1553-1620`
- omni `_StageTransitionLogitsProcessor`（is_comprehension=false 时启用）：同上文件 1530-1546 + 1900-1970
- omni `embed_multimodal()`（拼接 `[timestep, vae, vit]`）：同上文件 1789-1853
- omni `_vae_encode()`（fp32 cast at encoder boundary）：同上文件 1419-1430

## 未对齐的功能（intentional / out-of-scope）

- **sampling 模式输出**：vllm sampler ≠ transformers sampler（已知不可对齐，hf_omni_alignment_method.md 详述）。本 PR sampling 测试只验证"功能性正确"（无 garbage / 无死循环），不期望 byte-identical。
- **完整 IT2I → DiT 出图**：本 PR 只动 AR 段。DiT 段对齐工作未启动（sampling-mode 输出图像对比是另一个 PR 的范围）。
- **T2I (从纯文本生成图)**：路径走 `it2i.yaml` 的 image gen 部分，本 PR 不验证 T2I AR 输出。

## 关键 commit 反向索引

如果 review 问"X 改在哪里"：

- 死循环 garbage 修复 → `27083f9c` (instruct chat template) + `ea809348` (Assistant: prefix)
- BPE 跨段 merge → `7bd429ed` (build_prompt_tokens)
- pixel quant noise → `41d29432`
- top-k expert flip → `31c2fa56` (fp32 MoE router)
- AR-only output 无尽 recap → `07d8cf0d` (stop at `</think>`)

如果 review 问"为什么 it2i.yaml 没改" → 因为 IT2I 完整 pipeline 要 AR 走完 image tokens 喂 DiT，不能在 `</think>` 停（commit `07d8cf0d` 的 message 详细解释）。

如果 review 问"BF16 还差 +16/+34 chars 怎么办" → 看 hf_omni_alignment_method.md「关键认识 2: sampler 不可对齐」+ 本文件「不可修架构差异」5 项。
