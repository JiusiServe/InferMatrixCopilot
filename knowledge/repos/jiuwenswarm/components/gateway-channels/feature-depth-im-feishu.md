---
title: "飞书 频道：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/gateway/test_feishu_im_adapter.py:L12-L26]
feature: "im-feishu"
entry_points: ["jiuwenswarm/gateway/channel_manager/im_platforms/feishu/feishu_connect.py"]
source_globs: ["jiuwenswarm/gateway/channel_manager/im_platforms/feishu/feishu_connect.py", "jiuwenswarm/gateway/channel_manager/im_platforms/feishu/*"]
---

# 飞书 频道：实现深读

[功能概览](feature-im-feishu.md) · [owner 入口](_index.md)

<!-- kb:depth feature=im-feishu facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=932550eb526a773104bcd9f8c994fe668b5a3395d3c11c8186b8b3f58ea2cda4 -->
**用户显示名解析的单测**
tests/unit_tests/gateway/test_feishu_im_adapter.py 的两个用例验证 FeishuIMPlatformAdapter.resolve_user_display_name：get_user_name_by_open_id 返回 " 张三 " 时断言去空格后为 "张三"；无飞书用户名时回退为 "Open ID 尾号是 5678 的用户"，空 open_id 返回空串。这是源码中的既有断言，不代表当前已运行通过。

来源：[tests/unit_tests/gateway/test_feishu_im_adapter.py:L12–L26](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/gateway/test_feishu_im_adapter.py#L12-L26)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/gateway/test_feishu_im_adapter.py","start":12,"end":26,"sha256":"a7d86509acf8f78be12884273bab9aed23f4bf215f8168d37c17d97728d4068e"}],"trace":[]} -->
<!-- /kb:depth -->
