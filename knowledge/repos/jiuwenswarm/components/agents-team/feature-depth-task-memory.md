---
title: "任务经验检索与沉淀：实现深读"
created: 2026-10-02
updated: 2026-10-02
type: architecture
tags: [jiuwenswarm]
sources: [openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L204-L269, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L104-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/config.py:L237-L244, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L37-L39, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/common/utils.py:L1751-L1760, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L150-L194, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L266-L269, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L96-L101, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L121-L146, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L150-L158, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/经验记忆.md:L12-L22", openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:jiuwenswarm/agents/harness/common/tools/task_tools.py:L175-L187, openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:tests/unit_tests/agentserver/memory/test_external_memory_config.py:L117-L126, "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/经验记忆.md:L7-L22", "openJiuwen-ai/jiuwenswarm@f0a69728c96b5961d993449f1a901cbd2f4dac5b:docs/zh/经验记忆.md:L28-L38"]
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

<!-- kb:depth feature=task-memory facet=configuration pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=dc281445d0a60b74c89396a50bde4b90f1ed0234b498e897971b04cf83569139 -->
**task_memory.enabled 默认关闭，模型与凭据经 YAML→专用环境变量→embed 回退链解析，缺项时停用服务**
_is_task_memory_enabled() 只读取 get_config()['task_memory']['enabled']，未设置时返回 False；文档记载 enabled: true 后 Agent 获得三个经验工具。_get_service() 构造服务时，llm_model/embedding_model/api_key/api_base 依次取自 YAML task_memory 小节、TASK_MEMORY_* 环境变量、embed 小节或 EMBED_*/通用环境变量；api_key、llm_model 或 embedding_model 任一无法解析时记录「task tools will be disabled」警告并返回 None。

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L96–L101](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L96-L101), [jiuwenswarm/agents/harness/common/tools/task_tools.py:L121–L146](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L121-L146), [jiuwenswarm/agents/harness/common/tools/task_tools.py:L150–L158](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L150-L158), [docs/zh/经验记忆.md:L12–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E7%BB%8F%E9%AA%8C%E8%AE%B0%E5%BF%86.md#L12-L22)

<!-- kb:depth-proof {"basis":"supported","evidence":[{"end":101,"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","sha256":"6cafbac8a7c6f04a6a8149654e04e1cc2a39cd46f7d91edca214d9252dd9809d","start":96},{"end":146,"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","sha256":"0a5f07f0ad78329a56edc9bb60d48f06c381dd50ba00e6dab5b2283059586daf","start":121},{"end":158,"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","sha256":"0738db826c10f0338041aab03b7e1aa0b881d332c2cdd7faf0a619db695f1ace","start":150},{"end":22,"path":"docs/zh/经验记忆.md","sha256":"d67263b43fbdec69b0877978469241ac107d3b1a2f6f15cfc53c9325e0bcb71c","start":12}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=task-memory facet=tradeoffs pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=2487c7581f51e2875972225f37c85aee906dbe5cdb6e5452c07592993c6bc08a -->
**仅当 api_base 为真时临时覆写进程环境变量 API_BASE，TaskMemoryService 构造返回后才恢复**
设计推断（非作者历史意图）：

该分支在 api_base 为真时覆写 os.environ["API_BASE"]，仅在 TaskMemoryService(**kwargs) 返回后按原值恢复或删除；同进程内此窗口中的其他环境变量读取者可能看到被覆写的值（代码注释自述构造器无 api_base 参数、借环境变量传递；收益/代价权衡为我的推断）。

来源：[jiuwenswarm/agents/harness/common/tools/task_tools.py:L175–L187](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/jiuwenswarm/agents/harness/common/tools/task_tools.py#L175-L187)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":187,"path":"jiuwenswarm/agents/harness/common/tools/task_tools.py","sha256":"06620dfcd91439e496ab071a092ce196961f7b1dec63ff28742f7309577e5b3a","start":175}],"trace":[]} -->
<!-- /kb:depth -->

<!-- kb:depth feature=task-memory facet=validation pin=f0a69728c96b5961d993449f1a901cbd2f4dac5b sha256=08333f31e632c4223b75d90626182a0d16ef173f151e194a84a07201bb5b3a6a -->
**task_memory 启用与 experience_retrieve 调用的文档化验收（本轮未执行）**
文档中的人工验收步骤（本轮未执行）：

文档化人工验收步骤（NOT EXECUTED）：在 config/config.yaml 将 task_memory.enabled 设为 true（文档标注为总开关），文档称 Agent 将获得三个工具；再按文档建议在任务开始时以 query 描述当前任务或问题调用 experience_retrieve，检查返回的 memory_string（可读文本）与 retrieved_memory（结构化列表）。不据此声称检索必命中或服务已运行。

来源：[docs/zh/经验记忆.md:L7–L22](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E7%BB%8F%E9%AA%8C%E8%AE%B0%E5%BF%86.md#L7-L22), [docs/zh/经验记忆.md:L28–L38](https://github.com/openJiuwen-ai/jiuwenswarm/blob/f0a69728c96b5961d993449f1a901cbd2f4dac5b/docs/zh/%E7%BB%8F%E9%AA%8C%E8%AE%B0%E5%BF%86.md#L28-L38)

<!-- kb:depth-proof {"acceptance_mode":"lightweight","basis":"supported","evidence":[{"end":22,"path":"docs/zh/经验记忆.md","sha256":"e92d53e20efff560b7ecc5d7720f0ca83373c70b738f71abc5963f57e6b2c08a","start":7},{"end":38,"path":"docs/zh/经验记忆.md","sha256":"f475a15809bd7dc4c645329949e0fc43cd82fc2d62c3ee4803b80e46d1e6bfd2","start":28}],"trace":[],"validation_kind":"documented_manual"} -->
<!-- /kb:depth -->
