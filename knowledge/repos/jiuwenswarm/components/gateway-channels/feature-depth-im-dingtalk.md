---
title: "钉钉 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py:L28-L42, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py:L374-L412]
feature: "im-dingtalk"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/*"]
---

# 钉钉 频道：实现深读

[功能概览](feature-im-dingtalk.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-dingtalk facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=f8b03114e972120b4ee9810e19c6ede4d6466a44cfa18653ba39280ca9dcaf2c -->
**DingTalkConfig 默认值与兜底**
DingTalkConfig 默认 enabled=False、max_download_size=100*1024*1024（100MB）、download_timeout=60、send_file_allowed 与 enable_file_download 为 True；api_base/oapi_base 默认空串，注释说明由 app_gateway 从 config.yaml 加载兜底、不硬编码。start() 中 workspace_dir 为空时回落到 get_agent_workspace_dir()。

来源：[jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py:L28–L42](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py#L28-L42), [jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py:L374–L412](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py#L374-L412)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py","start":28,"end":42,"sha256":"3c78a55632aa445561d5500804bd34b0495c26bfb02eca93f29bab3b61e4e082"},{"path":"jiuwenswarm/gateway/channel_manager/im_platforms/dingtalk/dingtalk_connect.py","start":374,"end":412,"sha256":"96edea83215b060cb62f697e112d9d4edf0631958ff1ee52e42bdc8d2dc1a894"}],"trace":[]} -->
<!-- /kb:depth -->
