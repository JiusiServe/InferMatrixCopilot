---
title: "图片生成与产物落盘：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L474-L477, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L335-L350, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/multimodal_config.py:L39-L49, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L390-L415, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L450-L467, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/image_tools.py:L479-L505]
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
