# HunyuanImage-3.0-Instruct IT2I Gap 风险报告

**版本**：2026-04-20
**作者**：CI/精度评测工作组
**状态**：待领导决策（方案 A / B / C）

---

## TL;DR

**vLLM-Omni 的 HunyuanImage-3.0-Instruct 目前不支持 IT2I（图文转图片）场景**——DiT pipeline 的代码路径上有 3 层缺失，从桥接传来的 PIL 图片一路被丢弃，永远到不了 DiT 的 condition image encoding。

**影响**：所有依赖 IT2I 能力的下游任务（图片编辑 API、gbench 精度评测、业务图编辑功能）都跑不通。

**修复路径**：照 GLM-Image / BAGEL 先例在 DiT 侧加 image 处理，~195-215 行代码，1.5-3 人天。有开源官方代码可复制，**非创新**。

---

## 一、精确问题定位（代码级证据）

### 1.1 IT2I 的数据流现状

走 `hunyuan_image3_it2i.yaml` 部署，完整数据路径：

```
[用户请求] prompt + PIL 图片
     ↓
[AR Stage 0] HunyuanImage3ForConditionalGeneration 生成 latent tokens
     ↓
[桥接 ar2diffusion] 塞进 OmniDiffusionRequest，pil_image 被成功转发 ✓
     ↓ pil_image 在 req.prompts[i]["pil_image"] 字段里
[DiT Stage 1] pipeline_hunyuan_image3.py::forward()
     ↓
[第 1003 行] prompt = [p.get("prompt") or "" for p in req.prompts]
     ↓ ❌ 只抽 "prompt" 字段，pil_image 被丢弃
[第 1013-1022 行] prepare_model_inputs(prompt=..., cot_text=None, mode="gen_image", ...)
     ↓ ❌ 没传 image 参数
[prepare_model_inputs else 分支 第 515 行]
     ↓ batch_message_list 为 None，走 else
[第 494 行] batch_cond_image_info = None   ❌ 硬编码 + TODO 注释
     ↓
[apply_chat_template(batch_cond_image_info=None)]
     ↓
DiT 拿到的 sequence 里没有任何 cond_image 信息
     ↓
出图等同于纯文生图（图片被完全忽略）
```

### 1.2 5 层代码缺口（都是事实，非推测）

| # | 缺口位置 | 代码行 | 问题 |
|---|---|---|---|
| 1 | `pipeline_hunyuan_image3.py::forward()` 第 1003 行 | `prompt = [p if isinstance(p, str) else (p.get("prompt") or "") for p in req.prompts]` | 只抽 `prompt` 字段，`pil_image` / `multi_modal_data` 被丢弃 |
| 2 | `pipeline_hunyuan_image3.py::prepare_model_inputs()` 签名 第 469-481 行 | 参数表：`prompt, mode, system_prompt, cot_text, num_inference_steps, guidance_scale, image_size, message_list, device, max_new_tokens` | **没有 `image` 参数** |
| 3 | `pipeline_hunyuan_image3.py::prepare_model_inputs()` else 分支 第 493-494 行 | `# TODO: construct with user input images`<br>`batch_cond_image_info = None` | 作者留的明文 TODO，未实现 |
| 4 | `hunyuan_image3_transformer.py::HunyuanImage3ImageProcessor` 第 1353 行 | 只有 `build_image_info(image_size)`（用于生成图 target 尺寸） | 缺 `build_cond_images` / `vae_process_image` / `vit_process_image` / `as_image_tensor` 等把 PIL 转成 JointImageInfo 的方法 |
| 5 | `model_executor/models/hunyuan_image3/hunyuan_image3.py`（AR 模型） | 未实现 `OmniOutput(multimodal_outputs=...)` 输出 | 桥接尝试读 `ar_output.multimodal_output`（`stage_input_processors/hunyuan_image3.py:111`），但 AR 侧没写入，永远为空 |

**5 个缺口并存，补任何一个都不够，必须一起补**。

---

## 二、业界对比：别人都已经做了

| 模型 | image 输入实现方式 | 代码位置 | 状态 |
|---|---|---|---|
| **GLM-Image** | `_prepare_condition_image_kv_cache(condition_images, prior_token_image_ids, ...)` —— DiT 侧自己调 `vae.encode(...)` 编码 condition image | `vllm_omni/diffusion/models/glm_image/pipeline_glm_image.py:602` | ✅ 已实现 |
| **BAGEL** | `prepare_vae_images` / `prepare_vit_images` —— DiT 侧自己编码；通过 `past_key_values` + `kv_transfer_manager` 从 AR 传 | `vllm_omni/diffusion/models/bagel/` | ✅ 已实现 |
| **HunyuanImage-3.0** | 桥接传 `pil_image`，但 DiT 不读；`batch_cond_image_info = None` 硬编码 | — | ❌ **未实现** |

**结论**：这不是设计差异，是实现缺陷。原作者只实现了 T2I 路径，IT2I 的代码留空。

---

## 三、同事 PR #2949 不解决 IT2I 问题

- PR 标题：`[Feature] Add KV Cache Reuse between AR-DiT in Hunyuan-Image3`
- PR 做的事：T2I 场景下 AR 把 **text prompt 的 KV cache**（含 CFG negative prompt KV）传给 DiT 复用，跳过 DiT 的文字 encode
- PR **新增的唯一函数**：`_forward_with_kv_reuse`（`pipeline_hunyuan_image3.py` 第 1041-1238 行）
- 这个新函数**内部所有 cond image 相关字段硬编码 None**（第 1128-1131 行）：
  ```python
  "cond_vae_images": None,
  "cond_vit_images": None,
  "cond_vit_image_mask": None,
  ```
- `_forward_with_kv_reuse` 只在 `req.sampling_params.past_key_values` 非 None 时触发（第 1014 行），**这个条件在 IT2I 路径下不成立**（IT2I yaml 的 DiT stage 走的是普通 `forward()`，桥接 `ar2diffusion` 没塞 `past_key_values`）

**验证**：PR 里 IT2I 相关改动只在 `end2end.py`（example 脚本）和 README，**生产代码对 IT2I 路径 0 改动**。

---

## 四、修复方案 & 工作量

### 方案 A（推荐）：照 GLM-Image / BAGEL 先例在 DiT 侧加 image 处理

**思路**：和 GLM-Image 一致，DiT 自己调 VAE/ViT 编码 PIL。工作重点是把官方 `hunyuan3.0_ins/image_processor.py` 的相关函数移植到 vLLM-Omni。

**改动清单**：

| 文件 | 新增代码量 | 内容 |
|---|---|---|
| `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py::HunyuanImage3ImageProcessor` | ~175-195 行 | 加 5 个方法 + 辅助类（从官方 `hunyuan3.0_ins/image_processor.py` 复制）：<br>• `as_image_tensor` ~60 行<br>• `vae_process_image` ~5 行<br>• `vit_process_image` ~15 行<br>• `get_image_with_size` ~35 行<br>• `build_cond_images` ~30 行<br>• `ImageTensor` / `CondImage` / `JointImage` 辅助类 ~30-50 行 |
| `pipeline_hunyuan_image3.py::prepare_model_inputs` else 分支 | ~15 行 | 加 `batch_image_list = self._validate_and_batchify_image(...)` → `build_cond_images` → 填 `batch_cond_image_info`（照抄官方 `modeling_hunyuan_image_3.py:2668-2676`） |
| `pipeline_hunyuan_image3.py::forward` 第 1003 行 | ~5 行 | 从 `req.prompts[i].get("pil_image")` 或 `multi_modal_data.image` 读 PIL，加到 `prepare_model_inputs(image=...)` 传递 |
| 签名 | ~1 行 | `prepare_model_inputs(..., image=None, ...)` 加参数 |

**总计**：~195-215 行。**全部从官方源码复制**，非创新设计。

**需要验证的 3 层（无法跳过）**：
1. **本地 import smoke**：改完后 `prepare_model_inputs(prompt="x", image=PIL.new("RGB", (512,512)))` 返回非空结构不报错
2. **远端端到端 smoke**：起 server，HTTP `/v1/images/edits` 打一张图 + prompt，confirm 出图不崩
3. **视觉合理性 smoke**：出的图像大致是图，不是噪声花屏（不要求和官方 pipeline 一致）

**风险评估**：

| 风险项 | 等级 | 说明 |
|---|---|---|
| 逻辑风险（抄错/对齐错） | **低** | 官方代码开源可参照，GLM-Image 先例可比对 |
| 运行时 bug（tensor shape / dtype） | **中** | VAE/ViT tensor 的 shape / dtype 要和 chat template 的 token 数对齐 |
| 数值精度 | **低** | VAE 权重同一份，encode 实现从官方移植 |
| TP/并行分片 | **中** | GLM-Image 验证过 DiT TP worker 里跑 VAE，HunyuanImage3 同理但要实测 |
| chat template 拼接 | **中-高** | 作者留 TODO 的地方就是这里。`apply_chat_template` 的 `batch_cond_image_info` 路径代码上存在，但 prompt 分支下的 cond image sections 插入位置可能有隐藏 bug |

**预计时间**：**1.5-3 人天**
- 代码移植：0.5-1 天
- 本地 smoke + 远端调试：1-2 天（bf16 MoE 80B 模型远端调试迭代慢，预计 1-3 轮）

### 方案 B：等同事 PR #2949 合并，在其基础上扩展加 image 通道

**前提**：
- 等 PR #2949 合并（时间不可控）
- AR 侧要先实现 `OmniOutput(multimodal_outputs=...)`（HunyuanImage3 AR 目前没实现）

**改动清单**：

| 文件 | 新增代码量 |
|---|---|
| `hunyuan_image3.py` AR 侧加 mm_output 输出 | ~30 行 |
| `stage_input_processors/hunyuan_image3.py` 桥接加 mm payload | ~20 行 |
| `pipeline_hunyuan_image3.py::_forward_with_kv_reuse` 读 image tensor | ~30 行 |

**总计**：~80 行。

**劣势**：
- 时间不可控（依赖 PR 合并）
- 协调成本高（AR 输出格式要和 DiT 接口对齐，跨开发者）
- 复用价值低于方案 A（只修 KV reuse 路径的 IT2I，不修普通 IT2I）

**预计时间**：PR 合并后 1-2 人天。PR 未合并前等待时间不可控。

### 方案 C：放弃 IT2I

- 不修复 IT2I 能力
- 下游业务（图片编辑 API / gbench / 业务图编辑）自己想办法
- **预计时间**：0 人天
- **代价**：能力缺失

---

## 五、推荐 & 决策请求

| 维度 | 方案 A（推荐） | 方案 B | 方案 C |
|---|---|---|---|
| 时间可控性 | ✓ 1.5-3 人天 | ✗ 依赖他人 PR | ✓ 0 天 |
| 代码量 | ~200 行 | ~80 行 | 0 |
| 开源参考 | ✓ GLM-Image / BAGEL 先例 + 官方源码 | ✓ 部分 | — |
| 风险 | 中（3 层验证可控） | 高（协调 + 前置依赖） | 0 |
| 能力交付 | 完整 IT2I | 仅 KV reuse 路径的 IT2I | 无 |

**推荐方案 A**：不依赖他人、有开源参考、时间可控、能力完整。3 层验证（本地 smoke → 远端 smoke → 视觉合理性）可以充分控制风险。

---

## 六、下一步决策

请领导在以下选项中选择：

- [ ] **方案 A**：立即启动自主实现，预计 1.5-3 人天交付可用 IT2I
- [ ] **方案 B**：等同事 PR #2949 合并后再做，时间不可控
- [ ] **方案 C**：不做 IT2I，本项目 IT2I 能力缺失

无论选择哪个方案，**T2I 的 GenEval 精度 CI 可以并行推进**（不依赖 IT2I 决策，vLLM-Omni 生产代码 0 改动）。

---

## 附录 A：关键文件路径清单

- `vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py`（DiT pipeline）
- `vllm_omni/diffusion/models/hunyuan_image3/hunyuan_image3_transformer.py`（含 `HunyuanImage3ImageProcessor`）
- `vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py`（AR 模型）
- `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py`（AR→DiT 桥接）
- `vllm_omni/model_executor/stage_configs/hunyuan_image3_it2i.yaml`（IT2I 部署配置）
- `hunyuan3.0_ins/image_processor.py`（官方 image 处理代码，移植来源）
- `hunyuan3.0_ins/modeling_hunyuan_image_3.py`（官方 HunyuanImage3ForCausalMM）
- `vllm_omni/diffusion/models/glm_image/pipeline_glm_image.py::_prepare_condition_image_kv_cache`（参考先例）
- `vllm_omni/diffusion/models/bagel/`（参考先例）

## 附录 B：同事 PR #2949 关键信息

- URL：<https://github.com/vllm-project/vllm-omni/pull/2949>
- 标题：`[Feature] Add KV Cache Reuse between AR-DiT in Hunyuan-Image3`
- 状态：OPEN（截至 2026-04-20）
- 作用：T2I 的 AR→DiT 文字 KV 复用，不影响 IT2I 路径
