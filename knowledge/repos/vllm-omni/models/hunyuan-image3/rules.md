# HunyuanImage3 开发规则

这些规则适用于 HunyuanImage3 的生成、编辑、prompt、AR 采样、AR→DiT 交接、条件图处理和公开入口。只有加粗项目或表格第一列中的 `HY3-数字字母` 是可审计规则 ID；章节标题只是分组，不计入 ID，解释性文字和链接也不计。

## 开发快速入口

- **HY3-0a — 开发阶段按任务选规则。** 开发者只合并下表命中的规则和源码入口，不在编码前手工枚举整页；任务命中多行时必须取规则与源码并集，不能只选看起来最接近的一行。独立 reviewer 仍按当前完整 diff 审计全部稳定 ID。

| 正在修改什么 | 开发阶段先读 | 第一批 live 源码 |
|---|---|---|
| `task`、`bot_task`、system prompt、stop、CoT | `HY3-1*`、`HY3-2a/2e`、`HY3-3*`、`HY3-6a/6e/6f/6i/6j` | `vllm_omni/diffusion/models/hunyuan_image3/prompt_utils.py::{build_prompt_tokens, resolve_stop_token_ids}`；`vllm_omni/entrypoints/openai/serving_chat.py::_build_multistage_generation_inputs`；`vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py::ar2diffusion` |
| 图片数量、多参考图、online/offline | `HY3-2*`、`HY3-3d`、`HY3-5a/5b`、`HY3-6a/6b/6c/6d/6i/6j` | `vllm_omni/entrypoints/openai/api_server.py::edit_images`；`vllm_omni/entrypoints/openai/serving_chat.py::_build_multistage_generation_inputs`；`examples/offline_inference/hunyuan_image3/end2end.py`；`vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py::get_hunyuan_image_3_pre_process_func` |
| `size=auto`、ratio token、batch ratio | `HY3-1a/1e/1h`、`HY3-2a/2e`、`HY3-4*`、`HY3-6a/6b/6g/6j` | `vllm_omni/diffusion/models/hunyuan_image3/prompt_utils.py::resolve_stop_token_ids`；`vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py::{_extract_ratio_index, ar2diffusion}`；`vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py::{get_hunyuan_image_3_pre_process_func, prepare_model_inputs, prepare_encode}` |
| alpha、resize/crop、条件 VAE、seed/RNG | `HY3-2a/2e`、`HY3-5*`、`HY3-6a/6d/6h/6j` | `vllm_omni/diffusion/models/hunyuan_image3/pipeline_hunyuan_image3.py::{_resize_and_crop_center, get_hunyuan_image_3_pre_process_func, prepare_seed, _encode_cond_image, prepare_model_inputs, prepare_encode}`；`vllm_omni/model_executor/models/hunyuan_image3/hunyuan_image3.py::{_parse_and_validate_image_input, _vae_encode}` |
| shared serving 分层和模型 adapter | `HY3-1g`、`HY3-2a/2e/2f`、`HY3-6a/6b/6i/6j` | `vllm_omni/entrypoints/openai/api_server.py::edit_images`；`vllm_omni/entrypoints/openai/serving_chat.py::_build_multistage_generation_inputs`；模型 owner 的 `vllm_omni/diffusion/models/hunyuan_image3/prompt_utils.py` 和 `vllm_omni/model_executor/stage_input_processors/hunyuan_image3.py` |

- **HY3-0b — 代码地图之后停止读文档。** 打开命中行的第一批源码后就沿 live producer-consumer 调用链实现；只有规则明确链接的官方机制、源码证明跨 owner 或一个具体未知量阻止落盘时，才再读一篇 guide 或增加一个 owner，不能预读 incidents/history。

## 完整行为链

- **HY3-1a — 编码前行为表。** 涉及 `task`、`bot_task`、system prompt、stop token 或 AR→DiT 数据时，编码前填写下表，并为每行核对官方主入口。

  | 请求模式 | AR prompt/prefix | 阶段跳转 | 最终停止位置 | 交给 DiT 的文本范围 | DiT system prompt |
  |---|---|---|---|---|---|
  | T2I |  |  |  |  |  |
  | IT2I |  |  |  |  |  |
  | 其他实际支持模式 |  |  |  |  |  |

- **HY3-1b — legacy 只在入口归一化。** 公开 legacy 调用只允许在请求入口做一次显式 normalization，并记录旧字段到新字段的映射。
- **HY3-1c — 内部字段保持正交。** `task` 表示用户要做什么，`bot_task` 表示 AR 怎样生成；进入模型计划后两者不得互相充当默认值。
- **HY3-1d — legacy 有回归证据。** 新旧公开入口各保留一个行为测试。
- **HY3-1e — 单一模型计划。** prompt、stage transition、final stop、CoT 截断和 DiT prompt 必须由同一份模型专属计划导出；字段出现在下游字典里不能证明行为已经对齐。
- **HY3-1f — 官方主入口是语义基线。** 对齐官方 `generate_image()` 等真实用户入口，不用绕过阶段跳转的底层 `generate()` 代替。机制解释见 [HF alignment pitfalls](guides/hf-alignment-pitfalls.md)。
- **HY3-1g — 模型语义留在 owner。** shared serving 不实现 HunyuanImage3 状态机，不导入模型 prompt helper，也不堆模型名称分支；它只传通用请求事实并调用模型 owner 暴露的 adapter/capability，模型专属默认值和跳转计划留在 owner。
- **HY3-1h — 行为表逐行验收。** 每行必须同时给出官方源码、vLLM-Omni consumer 和测试证据；受影响行缺少任一项时状态只能是 `implementation draft`。

## 所有公开入口

- **HY3-2a — live 入口清单。** 修改图片数量、prompt、size、seed 或模式前，从 live 源码枚举所有能进入同一模型流程的入口，包括实际存在的 offline example、image generation/edit endpoint、chat endpoint 和内部直调；不能根据当前编辑文件假定只有一个入口。
- **HY3-2b — 图片数量合同。** T2I 接受 0 张参考图，IT2I 接受 1–3 张；不得为了代码兼容给 T2I 伪造 `num_images=1`。
- **HY3-2c — 入口尽早拒绝。** 每个公开入口都在文件读取、URL 获取、解码、resize 和 GPU/VAE 工作前校验图片数量。
- **HY3-2d — 数量边界有入口证据。** 测试覆盖 0、1、2、3、>3，并断言 >3 的拒绝发生在昂贵操作之前。
- **HY3-2e — online/offline 行为一致。** 两条路径共用模型 owner 的 normalization/plan，或用逐字段 parity test 证明一致；helper 返回值测试不能代替公开入口证据。
- **HY3-2f — 新入口不能形成旁路。** 新增入口或调用方式时同步扩展入口矩阵，并用旧入口回归证明新 happy path 没有绕过旧合同。

## Prompt 和 tokenizer

- **HY3-3a — 官方分段 tokenization。** HunyuanImage3 chat prompt 使用官方分段 tokenization；需要 Token 级对齐时传 `prompt_token_ids`，不得静默退回整串 BPE。
- **HY3-3b — 缺少模型工件就 fail fast。** tokenizer、processor 或模型专属配置缺失时在 owner 边界报出具体缺项，不切到会改变 token 边界的路径。
- **HY3-3c — system prompt 是完整合同。** 类型、正文、尾部换行和 bot prefix 都必须与官方行为一致；不得随手 `strip()`，也不得在 DiT 阶段替换成另一种 prompt 类型。
- **HY3-3d — 使用真实 tokenizer 验收。** 至少一个测试使用真实 tokenizer/processor，并同时断言 token ids、raw prompt、system prompt 和图像占位符数量。格式解释见 [official prompt format](guides/official-prompt-format.md)。

## `size=auto` 和 ratio

- **HY3-4a — ratio 来源唯一。** `size=auto` 使用 AR 实际生成的 `<img_ratio_*>` 和官方允许集合；集合按可能不连续处理，不用连续区间、第一张参考图比例或自造 heuristic 代替。
- **HY3-4b — ratio 生命周期完整。** ratio 限制、选择、AR 输出提取、AR→DiT 翻译和最终宽高必须连成一条可追踪链；只在 pipeline 尾部补宽高不算完成。
- **HY3-4c — batch 内逐请求归属。** 每个请求独立拥有 ratio；实现只支持同尺寸 batch 时，在进入 pipeline 前明确拒绝不同 ratio，不默默使用第一个请求的值。
- **HY3-4d — ratio 边界测试。** 至少覆盖一个非连续 token、两个不同 ratio 的请求和缺少 ratio token 的失败路径。

## 条件图和随机数

- **HY3-5a — 保留原生 bucket。** 每张参考图保留自己的 bucket 语义，异构尺寸不得在真实 VAE/ViT 处理前被无条件 `stack`。
- **HY3-5b — 使用生产图像路径验收。** 至少运行一次生产 processor/VAE 路径，fake tensor shape 不算替代证据。
- **HY3-5c — 图像策略精确对齐。** alpha 到 RGB、resize/crop、归一化和 cond VAE posterior 策略逐项核对官方实现，不能用看起来合理的白底或黑底策略代替。
- **HY3-5d — RNG 阶段归属明确。** 编码前写清 request seed 控制 AR sampling、条件 VAE、DiT noise 的哪些阶段以及是否共享 RNG 流。
- **HY3-5e — 不改变官方 RNG 消费顺序。** 不得通过 clone 或局部新建 generator 无意改变官方随机数消费顺序。
- **HY3-5f — seed 端到端验收。** 相同 seed 同时覆盖 online/offline 和条件图路径；只证明 AR seed 或最终 DiT seed 被赋值不算可复现。

## 验收范围和完成状态

- **HY3-6a — 逐行说明适用性。** 非琐碎修改把下表每行标成 `affected`、`unaffected-control` 或 `N/A-with-evidence`；`affected` 行补本次行为证据，`N/A` 指向当前 diff 或 live 调用链。存在未改生产路径时至少选择一个 control；修改覆盖全部路径时明确说明，不虚构 control。
最低验收矩阵的每一行都是独立规则，按适用性逐行报告，不能只报告已经跑通的 happy path。

| 规则 ID | 维度 | 最低用例 |
|---|---|---|
| **HY3-6b** | 入口 | offline、image endpoint、chat endpoint、内部直调中实际存在的路径 |
| **HY3-6c** | 图片数量 | T2I 0；IT2I 1、2、3、>3 |
| **HY3-6d** | 图片内容 | 异构尺寸、带 alpha 图片 |
| **HY3-6e** | 模式 | 每个受支持的 `task × bot_task` 组合及一个非法组合 |
| **HY3-6f** | Prompt | 真实 tokenizer、system prompt、阶段跳转、CoT 截断 |
| **HY3-6g** | 输出尺寸 | 显式 size、`auto`、batch 不同 ratio、缺 ratio |
| **HY3-6h** | 随机数 | online/offline 同 seed；AR、cond VAE、DiT 各阶段归属 |
| **HY3-6i** | 分层 | shared serving 没有 HunyuanImage3 状态机或模型 helper import |

- **HY3-6j — draft 只绑定受影响证据。** 受影响行所必需的正式行为测试无法运行且没有等价 CPU/CI/真实 artifact 证据时标记 `implementation draft`；不受影响或已有充分替代证据的行不阻止窄修改完成，lint、格式、编译和 mock smoke 不冒充受影响行为证据。
