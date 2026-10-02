---
title: "跨进程分布式 Team：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_distributed_runtime.py:L11-L33, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_distributed_runtime.py:L70-L104, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/distributed_runtime.py:L74-L81, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_distributed_runtime.py:L54-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/distributed_runtime.py:L100-L131, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/distributed_runtime.py:L53-L59, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/distributed_runtime.py:L31-L35, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/team/distributed_runtime.py:L53-L71, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/test_distributed_runtime.py:L97-L104]
---

# 跨进程分布式 Team：实现深读

[功能概览](feature-distributed-team.md) · [owner 入口](_index.md)

<!-- kb:depth feature=distributed-team facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=11d4289add061a1ec399cf104c87ae1eed3a562b822dbd5a73541dc2822f1382 -->
**归一化函数契约**
normalize_distributed_transport_fields(config_base, team_cfg) 返回 team_cfg 的深拷贝（L78 deepcopy），不修改调用方传入的 team_cfg；调用方义务是同时提供全局 config_base（用于解析 runtime.role）和 team 配置，并使用返回值而非原地读取入参。

来源：[jiuwenswarm/agents/harness/team/distributed_runtime.py:L74–L81](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/distributed_runtime.py#L74-L81), [tests/unit_tests/agentserver/test_distributed_runtime.py:L54–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_distributed_runtime.py#L54-L59)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/distributed_runtime.py","start":74,"end":81,"sha256":"785ae3fbb85ec54fc053a768650f6bc15019ead1b29049a4d934bc7fa9975c17"},{"path":"tests/unit_tests/agentserver/test_distributed_runtime.py","start":54,"end":59,"sha256":"88f4987ca7e58d579b20260e29b351383e2e8fe83722594398175c5bd2c59127"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=distributed-team facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=5fc60f58ec4e263c816f7e9892d22214fac63236b988bb8410a4770482c2ecaf -->
**端口默认值与角色缺省**
leader 侧 direct_port/pub_port/sub_port 缺省分别为 18555/18556/18557，teammate direct_port 缺省 18600（L101-131）；端口值为 None 或空白字符串时回落到默认值，host 缺省 127.0.0.1（L100）。team.runtime.role 缺省为 "leader"。

来源：[jiuwenswarm/agents/harness/team/distributed_runtime.py:L100–L131](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/distributed_runtime.py#L100-L131), [jiuwenswarm/agents/harness/team/distributed_runtime.py:L53–L59](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/distributed_runtime.py#L53-L59), [jiuwenswarm/agents/harness/team/distributed_runtime.py:L31–L35](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/distributed_runtime.py#L31-L35)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/distributed_runtime.py","start":100,"end":131,"sha256":"ae67c3920f666fe7b539789dd82c2941f0a3c4ca8cbbd578042235051b8e2fd2"},{"path":"jiuwenswarm/agents/harness/team/distributed_runtime.py","start":53,"end":59,"sha256":"3aff4c9a915f0b47c178adc55ce3a385197f86ca3b7a68df1e52a040cb9339ec"},{"path":"jiuwenswarm/agents/harness/team/distributed_runtime.py","start":31,"end":35,"sha256":"eb042b1277a9a62187d9993b9d5f7fdb0c7c9e5de4ad5c64283a1c03e06e64b4"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=distributed-team facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=1582efa8c0f51ea1152041b9cfc3ea10fa2a6093783531dec4a7de511eeeb228 -->
**非法端口触发 ValueError**
parse_port 对无法 int() 的值（如 "abc"）或超出 1..65535 的值抛出 ValueError，消息为 "Invalid {field_name}: {value!r}. Expected an integer in range 1..65535."（L64-70）；None 或空白字符串不报错而是返回默认端口。

来源：[jiuwenswarm/agents/harness/team/distributed_runtime.py:L53–L71](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/team/distributed_runtime.py#L53-L71), [tests/unit_tests/agentserver/test_distributed_runtime.py:L97–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_distributed_runtime.py#L97-L104)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/team/distributed_runtime.py","start":53,"end":71,"sha256":"61783b283e4fed35baee4102bc3d8b096d9dd63a52780c415aed17119ef73d3d"},{"path":"tests/unit_tests/agentserver/test_distributed_runtime.py","start":97,"end":104,"sha256":"4c38f8e59e016407ba3e0f4c005a295f10b993bcaae389281f6f7c9f327b8812"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=distributed-team facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=fb190e9f74249a2f0f53ba65a20459cf31d3423749508ded72be7a0fd8c8f9b8 -->
**单元测试入口**
`tests/unit_tests/agentserver/test_distributed_runtime.py` 覆盖：leader 在 pubsub 已预填时仍移除 `known_peers`（L11-33）；归一化不改写入参且补全地址/`pubsub_bind=True`（L36-67）；teammate 生成唯一指向 leader 的 `known_peers`（L70-90）；`parse_port` 对空白串取默认、对非数字和越界值抛带字段名/范围的 `ValueError`（L93-104）。这些断言描述测试所固化的行为，不代表本次已运行通过。

来源：[tests/unit_tests/agentserver/test_distributed_runtime.py:L11–L33](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_distributed_runtime.py#L11-L33), [tests/unit_tests/agentserver/test_distributed_runtime.py:L70–L104](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/tests/unit_tests/agentserver/test_distributed_runtime.py#L70-L104)

<!-- kb:depth-proof {"evidence":[{"path":"tests/unit_tests/agentserver/test_distributed_runtime.py","start":11,"end":33,"sha256":"1e505911d579be857fb1b7bf4e986789e3f6bd181a43f30c5ff109a2b45b16ca"},{"path":"tests/unit_tests/agentserver/test_distributed_runtime.py","start":70,"end":104,"sha256":"11c7714480cf2a441e632f4d5749ee7a6d3fe6344abc341a21555990d82a0e74"}],"trace":[]} -->
<!-- /kb:depth -->
