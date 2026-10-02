---
title: "图片生成与产物落盘：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L474-L477, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L335-L350, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L39-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L390-L415, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L450-L467, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L479-L505, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L340-L360, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L285-L314, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agents/harness/test_multimodal_config.py:L26-L48, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L323-L335, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L468-L477, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L300-L314, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L237-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L42-L60]
feature: "image-generation"
entry_points: ["jiuwenswarm/agents/harness/common/tools/image_tools.py", "jiuwenswarm/agents/harness/common/tools/multimodal_config.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/image_tools.py", "jiuwenswarm/agents/harness/common/tools/multimodal_config.py"]
---

# 图片生成与产物落盘：实现深读

[功能概览](feature-image-generation.md) · [owner 入口](_index.md)

<!-- kb:depth feature=image-generation facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=44e774f1d20af4bda22dd2e3e28664a158d7b9694c5985b4108026ac97a21827 -->
**生图调用链：generate_image 到配置读取与落盘**
generate_image 接收 prompt（如 "一只猫"），先尝试从 config.yaml 应用环境变量配置，随后在 L477 直接调用 _invoke_model_image_generation；后者在 L339-340 调用 get_config() 并把结果传给 multimodal_config._get_model_config 读取 models.image_gen 模型配置（api_key/api_base/model）。拿到结果后在 L392-395 用 get_agent_workspace_dir() 加时间戳与随机后缀生成输出路径，把 base64 或下载的 URL 图片写入该 .png 文件，返回包含 image_path 的 dict，最终 generate_image 返回带保存路径的多行字符串。

调用路径：`jiuwenswarm/agents/harness/common/tools/image_tools.py`（`generate_image`） → `jiuwenswarm/agents/harness/common/tools/image_tools.py`（`_invoke_model_image_generation`） → `jiuwenswarm/agents/harness/common/tools/multimodal_config.py`（`_get_model_config`）

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L474–L477](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L474-L477), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L335–L350](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L335-L350), [jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L39–L49](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L39-L49), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L390–L415](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L390-L415)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":474,"end":477,"sha256":"f95fa8bcb733eb4c4ec224ea4be49c2753c8249a5c69635d3b5f94f29bab319e"},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":335,"end":350,"sha256":"812c673977bfbcfc72ae117d3d99325dc017c0fb7a4eaefef63e8ec8fab2046e"},{"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","start":39,"end":49,"sha256":"f39550a250e54703858129a50c194f6545197d3529b94308f01fe882432118a9"},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":390,"end":415,"sha256":"995d63eabbc90911b9fa02aaab051698394b07b5a13359b12525ffa167aeb245"}],"trace":[{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","symbol":"generate_image","start":474,"end":477},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","symbol":"_invoke_model_image_generation","start":339,"end":340},{"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","symbol":"_get_model_config","start":42,"end":49}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=image-generation facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=d53c28bf6a0d74aa208462da45f7caf9a7a60b46e903c99ffe994721ce9f58ba -->
**generate_image 的输入输出契约**
generate_image(prompt: str, size="1024x1024", quality="standard", save_dir=None) -> str：成功时返回多行字符串（含 Saved to 路径、Prompt，可选 Revised prompt 与 Original URL）；结果 dict 含 "error" 键时直接原样返回错误字符串而非抛异常。调用方若指定 save_dir，需容忍该目录被 mkdir(parents=True) 创建，文件会 rename 到该目录下。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L450–L467](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L450-L467), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L479–L505](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L479-L505)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":450,"end":467,"sha256":"0946de4d012e02309bd18a58bad42879b3883eeabacc08af2e2b1c89ceee7692"},{"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","start":479,"end":505,"sha256":"184ac5ff046a3d94e2217f9ce6be7b8b70c1ac921d3ece0fcc9be76ff4b61250"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=image-generation facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=cfb31b6466d61f1d3aa7fbbe841049096b690d816d495890ae3402f0e8322570 -->
**image_gen 优先读 models.image_gen 配置，api_base/model/provider 缺省为 dashscope 地址、wanx-v1、DashScope**
api_base 缺省 https://dashscope.aliyuncs.com/api/v1，model 缺省 wanx-v1；provider 为 DashScope 时改写为 OpenAI 并补 endpoint_profile=dashscope；apply_image_gen_model_config_from_yaml 仅把非空值镜像到 IMAGE_GEN_* 环境变量。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L340–L360](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L340-L360), [jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L285–L314](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L285-L314)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":360,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"6cd6041d9608e09b3aa16abcebb0a0057f6ea1ad41db0b5969d1d3de8783ccfd","start":340},{"end":314,"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","sha256":"6289d5c3eecff51c05d43ff17e3c671203638d2dcc16e9783d0db34c89ede20b","start":285}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=image-generation facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=87192a6db3af93715dc68afc8fd4a6f4b34da98a030a825a2150a092eced75c7 -->
**generate_image 依赖 get_config→apply_image_gen_model_config_from_yaml（值非空才写 IMAGE_GEN_*）与 openjiuwen Model 函数内延迟导入**
generate_image 函数内导入 get_config，先执行 apply_image_gen_model_config_from_yaml(get_config())；后者经 _get_model_config(config_base, "image_gen") 取值，仅在字段非空时写入 IMAGE_GEN_API_KEY/API_BASE/MODEL_NAME/PROVIDER 环境变量；_invoke_model_image_generation 在函数体内延迟导入 openjiuwen 的 Model/ModelClientConfig。

来源：[jiuwenswarm/agents/harness/common/tools/image_tools.py:L323–L335](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L323-L335), [jiuwenswarm/agents/harness/common/tools/image_tools.py:L468–L477](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/image_tools.py#L468-L477), [jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L300–L314](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L300-L314), [jiuwenswarm/common/config.py:L237–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L237-L244)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":335,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"c24ff9e002e05b83e307c178ce36e3586c28d0a21178453303fdfa965dd7ead3","start":323},{"end":477,"path":"jiuwenswarm/agents/harness/common/tools/image_tools.py","sha256":"894b5d455e62aee5e00457bb29a554530307668544337448b67245da33da18d5","start":468},{"end":314,"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","sha256":"23ded4ccde03c34e5dbc1348184350b77f4bab6d723348a05f4ea7a914b89e3f","start":300},{"end":244,"path":"jiuwenswarm/common/config.py","sha256":"5ef680b085e74776575ebc948be5d277192e0c744c84d90cf49237b5a032e1f9","start":237}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=image-generation facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=086da81848a1fb46dc73a42b24f572e1f414c2692b9cef357bb07a3d39ebb199 -->
**apply_image_gen_model_config_from_yaml 仅在取出的值非空时覆盖 IMAGE_GEN_*，配置留空不会清掉进程内旧值**
设计推断（非作者历史意图）：

mc 来自 _get_model_config：models 为 dict 或 list 块两种形式均可，inner 取 model_config 或 model_client_config，model_name 还可回退 model 键；strip 后仅非空值写入对应环境变量。收益：字段缺省不覆盖进程内已有值；代价：从配置删字段也无法清除残留旧值（推断）。

来源：[jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L42–L60](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L42-L60), [jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L300–L314](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/multimodal_config.py#L300-L314)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":60,"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","sha256":"89197209e797b11a4abfcebeba0db46f5becf2ab3fe70503e354138cb5b9b6ea","start":42},{"end":314,"path":"jiuwenswarm/agents/harness/common/tools/multimodal_config.py","sha256":"23ded4ccde03c34e5dbc1348184350b77f4bab6d723348a05f4ea7a914b89e3f","start":300}],"trace":[]} -->
<!-- /kb:depth -->
