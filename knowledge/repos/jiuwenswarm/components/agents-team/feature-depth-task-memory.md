---
title: "任务经验检索与沉淀：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L204-L269, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L104-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L237-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L37-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1751-L1760, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L150-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L266-L269]
feature: "task-memory"
entry_points: ["jiuwenswarm/agents/harness/common/tools/task_tools.py"]
source_globs: ["jiuwenswarm/agents/harness/common/tools/task_tools.py", "jiuwenswarm/agents/harness/common/memory/*"]
---

# 任务经验检索与沉淀：实现深读

[功能概览](feature-task-memory.md) · [owner 入口](_index.md)

<!-- kb:depth feature=task-memory facet=flow pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=6a3812ff675a2aac275db58a738dfe4ea271fafee5e2578432cbd9045c43ac62 -->
**experience_retrieve 的服务初始化调用链**
工具函数 experience_retrieve(query) 先经 _get_task_data_path() 定位本地 task-data.json，再调用 _get_service() 惰性初始化 TaskMemoryService 单例；_get_service 内部调用 get_config() 读取 config.yaml 的 task_memory 与 embed 段解析模型与密钥，最终 experience_retrieve 用返回的服务执行检索并把本地持久化条目与服务端结果合并为 memory_string 与 retrieved_memory 返回。

调用路径：`jiuwenswarm/agents/harness/common/tools/task_tools.py`（`experience_retrieve`） → `jiuwenswarm/agents/harness/common/tools/task_tools.py`（`_get_service`） → `jiuwenswarm/common/config.py`（`get_config`）

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L204–L269](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L204-L269), [jiuwenswarm/agents/harness/common/tools/task_tools.py:L104–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L104-L194), [jiuwenswarm/common/config.py:L237–L244](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/config.py#L237-L244)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":204,"end":269,"sha256":"ad8d1460401627a7a02e3022ac0f1cd833a48a4dbdeb82248b333c490b4c512c"},{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":104,"end":194,"sha256":"f18b2978a3837a7fc14265e5615b937a2ec7321a8a10364b71510fa60263e350"},{"path":"jiuwenswarm/common/config.py","start":237,"end":244,"sha256":"5ef680b085e74776575ebc948be5d277192e0c744c84d90cf49237b5a032e1f9"}],"trace":[{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","symbol":"experience_retrieve","start":204,"end":269},{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","symbol":"_get_service","start":104,"end":194},{"path":"jiuwenswarm/common/config.py","symbol":"get_config","start":237,"end":244}]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=task-memory facet=api pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=b7335531a86c1306afe490bcc4d10aebdd949375ef1c6fc599ab7174f4cf1de3 -->
**experience_retrieve 的输入输出契约**
experience_retrieve 接收 query 字符串，返回含 memory_string（可读文本）与 retrieved_memory（结构化列表）的字典；调用方需注意三种状态：服务可用时为合并结果，服务禁用时返回 status="persisted_only"（仅本地数据），检索抛异常时返回 status="error" 且列表为空。

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L204–L269](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L204-L269)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":204,"end":269,"sha256":"ad8d1460401627a7a02e3022ac0f1cd833a48a4dbdeb82248b333c490b4c512c"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=task-memory facet=dependencies pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=bb811ccee8a34c0716858e81cb3147f10aab4058d9b7f4acedefdf045d6a4a7e -->
**对 get_agent_workspace_dir 的本地持久化耦合**
_get_task_data_path() 通过 get_agent_workspace_dir()（返回 agent 根目录下的 workspace，即 <用户主目录>/.jiuwenswarm/agent/workspace）拼接 task-data.json，使经验数据在 TaskMemoryService 外部服务不可用时仍可从本地文件读出，这是 persisted_only 降级路径的物理基础。

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L37–L39](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L37-L39), [jiuwenswarm/common/utils.py:L1751–L1760](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/common/utils.py#L1751-L1760)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":37,"end":39,"sha256":"b34a21b86e58037afb81d05306e25b4a0388d94ab23b7c7636a9b2ef2a7227ec"},{"path":"jiuwenswarm/common/utils.py","start":1751,"end":1760,"sha256":"f69da5db397197a47b8a1c8e5c7ff1a77d495283281c14cbf3bb74df6e67748f"}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=task-memory facet=failure_modes pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=09431972a5b77e0e48f6b07a1548ac2fd9cf647ba06aafee452482876076e75d -->
**缺配置与服务异常的降级行为**
_get_service 中若 api_key、llm_model 或 embedding_model 任一缺失，记录 warning 并返回 None（工具退化为仅本地持久化）；TaskMemoryService 构造抛异常时置 _service=None 并在下次调用重试初始化。experience_retrieve 中 svc.retrieve 抛异常不向上传播，而是返回 {"status":"error", "error": str(exc), "memory_string":"", "retrieved_memory":[]}。

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L150–L194](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L150-L194), [jiuwenswarm/agents/harness/common/tools/task_tools.py:L266–L269](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L266-L269)

<!-- kb:depth-proof {"evidence":[{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":150,"end":194,"sha256":"992fcb6fdc7b2aab7d0c6aebcd85488b7ca48ea5f85214426573d5e6db43d097"},{"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","start":266,"end":269,"sha256":"6027115973baf703e79d9c047aacf5f6a49da68dbcca6be6aa3785d1dc26420e"}],"trace":[]} -->
<!-- /kb:depth -->
